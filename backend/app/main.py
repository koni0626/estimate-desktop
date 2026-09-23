import copy
import os
import secrets
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import ROOT, get_db
from .models import (
    Company,
    Department,
    Section,
    User,
    Member,
    LoginSession,
    Customer,
    Quote,
    Revision,
    ApprovalRequest,
    ApprovalStep,
    Audit,
    Seal,
    Order,
    now,
)
from .schemas import (
    Login,
    InitialSetup,
    DesktopSetup,
    CustomerInput,
    QuoteInput,
    Action,
    SettingsInput,
    MemberInput,
    OrganizationInput,
)
from .security import (
    current_member,
    require_admin,
    hash_password,
    verify_password,
    token_hash,
)
from .pdf import generate_pdf

app = FastAPI(title="見積管理システム API", version="1.0.0")
Db = Depends(get_db)
Auth = Depends(current_member)
DUMMY_HASH = hash_password("unused-random-password")


@app.middleware("http")
async def protect_request(request: Request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        allowed = {
            "http://127.0.0.1:5185",
            "http://localhost:5185",
            "http://127.0.0.1:8005",
            "http://localhost:8005",
        }
        desktop_origin = os.getenv("ESTIMATE2_DESKTOP_ORIGIN")
        if desktop_origin:
            allowed.add(desktop_origin)
        if (origin and origin not in allowed) or request.headers.get(
            "sec-fetch-site"
        ) == "cross-site":
            return JSONResponse(
                {"detail": "許可されていないリクエストです。"}, status_code=403
            )
    response = await call_next(request)
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse(
        {
            "detail": "名前の重複、または関連データの不整合があります。入力内容を確認してください。"
        },
        status_code=409,
    )


def scoped(db, model, identifier, member):
    obj = db.scalar(
        select(model).where(
            model.id == identifier, model.company_id == member.company_id
        )
    )
    if obj is None:
        raise HTTPException(404, "データが見つかりません。")
    return obj


def member_name(db, member_id):
    return (
        db.scalar(
            select(User.display_name)
            .join(Member, Member.user_id == User.id)
            .where(Member.id == member_id)
        )
        or "ユーザー"
    )


def audit(db, member, action, quote_id=None, detail=""):
    db.add(
        Audit(
            company_id=member.company_id,
            actor_id=member.id,
            quote_id=quote_id,
            action=action,
            detail=detail,
        )
    )


def normal_scope(member, quote):
    if member.role == "admin":
        return True
    if member.role == "department_manager" and member.department_id:
        return quote.department_id == member.department_id
    if member.section_id:
        return quote.section_id == member.section_id
    return quote.owner_id == member.id


def assigned(db, member, revision_id):
    return (
        db.scalar(
            select(ApprovalStep.id)
            .join(ApprovalRequest, ApprovalRequest.id == ApprovalStep.request_id)
            .where(
                ApprovalStep.company_id == member.company_id,
                ApprovalStep.approver_id == member.id,
                ApprovalRequest.revision_id == revision_id,
                ApprovalRequest.status.in_(["pending", "approved"]),
            )
        )
        is not None
    )


def can_edit(member, quote):
    return normal_scope(member, quote) and (
        member.id == quote.owner_id or member.role != "member"
    )


def get_revision(db, member, rid, write=False):
    revision = scoped(db, Revision, rid, member)
    quote = scoped(db, Quote, revision.quote_id, member)
    if write:
        # Serialize mutations of a quote, including new revisions and issuance.
        db.execute(
            select(Quote.id).where(Quote.id == quote.id)
        ).first()
        db.refresh(revision)
        db.refresh(quote)
    if not normal_scope(member, quote) and not assigned(db, member, rid):
        raise HTTPException(404, "データが見つかりません。")
    return quote, revision


def latest(db, quote_id):
    return db.scalar(
        select(Revision)
        .where(Revision.quote_id == quote_id)
        .order_by(Revision.version.desc())
        .limit(1)
    )


def require_edit(db, member, quote, revision):
    if not can_edit(member, quote):
        raise HTTPException(403, "この見積を変更する権限がありません。")
    if latest(db, quote.id).id != revision.id:
        raise HTTPException(409, "最新版から操作してください。")


def check_version(revision, lock_version):
    if lock_version != revision.lock_version:
        raise HTTPException(409, "他の操作で更新されています。再読み込みしてください。")


def touch(revision):
    revision.lock_version += 1
    revision.updated_at = now()


def payload_for(db, member, body, previous_seal=None):
    customer = scoped(db, Customer, body.customer_id, member)
    company = db.get(Company, member.company_id)
    data = body.model_dump(mode="json", exclude={"lock_version"})
    if body.seal_id:
        seal = scoped(db, Seal, body.seal_id, member)
        if not seal.active and seal.id != previous_seal:
            raise HTTPException(
                409, "印鑑画像が変更されています。現在の画像を選択してください。"
            )
    items, bases = [], {}
    for row in body.items:
        amount = (row.quantity * row.unit_price).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        item = row.model_dump(mode="json")
        item["amount"] = str(amount)
        items.append(item)
        key = str(row.tax_rate)
        bases[key] = bases.get(key, Decimal(0)) + amount
    subtotal = sum(bases.values(), Decimal(0))
    taxes = {
        key: (value * Decimal(key) / 100).quantize(Decimal("1"), rounding=ROUND_DOWN)
        for key, value in bases.items()
    }
    tax = sum(taxes.values(), Decimal(0))
    if subtotal + tax > Decimal("9999999999999"):
        raise HTTPException(422, "見積金額が上限を超えています。")
    data.update(
        items=items,
        subtotal=str(subtotal),
        tax=str(tax),
        total=str(subtotal + tax),
        taxes={k: str(v) for k, v in taxes.items()},
        customer={
            "name": customer.name,
            "address": customer.address,
            "contact": customer.contact,
            "email": customer.email,
        },
        issuer={
            "name": company.name,
            "address": company.address,
            "phone": company.phone,
        },
        owner_name=member_name(db, member.id),
        organization=" / ".join(
            x.name
            for x in [
                db.get(Department, member.department_id)
                if member.department_id
                else None,
                db.get(Section, member.section_id) if member.section_id else None,
            ]
            if x
        ),
        rounding="明細金額は四捨五入、税率別合算後の税額は切り捨て",
    )
    return data


def new_revision(db, quote, payload, version=1):
    revision = Revision(
        company_id=quote.company_id,
        quote_id=quote.id,
        version=version,
        payload=payload,
        subtotal=Decimal(payload["subtotal"]),
        tax=Decimal(payload["tax"]),
        total=Decimal(payload["total"]),
    )
    db.add(revision)
    db.flush()
    return revision


def steps_for(db, request_id):
    return db.scalars(
        select(ApprovalStep)
        .where(ApprovalStep.request_id == request_id)
        .order_by(ApprovalStep.position)
    ).all()


def active_request(db, revision_id):
    return db.scalar(
        select(ApprovalRequest)
        .where(ApprovalRequest.revision_id == revision_id)
        .order_by(ApprovalRequest.id.desc())
        .limit(1)
    )


def summary(db, quote, rev, business=True):
    order = db.scalar(
        select(Order).where(
            Order.company_id == quote.company_id, Order.quote_id == quote.id
        )
    )
    return {
        "id": quote.id,
        "project_id": quote.project_id,
        "revision_id": rev.id,
        "number": quote.number,
        "version": rev.version,
        "status": rev.status,
        "title": rev.payload["title"],
        "customer_name": rev.payload["customer"]["name"],
        "total": str(rev.total),
        "valid_until": rev.payload["valid_until"],
        "updated_at": rev.updated_at.isoformat(),
        "owner_name": member_name(db, quote.owner_id),
        "department_id": quote.department_id,
        "section_id": quote.section_id,
        "organization": rev.payload.get("organization", ""),
        "sales_status": (
            "won" if order and order.status != "cancelled" else quote.sales_status
        )
        if business
        else None,
        "sales_version": quote.sales_version if business else None,
        "sent_on": quote.sent_on if business else None,
        "order_id": order.id if order and business else None,
    }


def detail(db, member, quote, rev):
    requests = db.scalars(
        select(ApprovalRequest)
        .where(ApprovalRequest.revision_id == rev.id)
        .order_by(ApprovalRequest.id.desc())
    ).all()
    approval = []
    for req in requests:
        approval.append(
            {
                "id": req.id,
                "status": req.status,
                "requester_id": req.requester_id,
                "created_at": req.created_at.isoformat(),
                "steps": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "position": s.position,
                        "approver_id": s.approver_id,
                        "approver_name": member_name(db, s.approver_id),
                        "status": s.status,
                        "comment": s.comment,
                        "decided_at": s.decided_at.isoformat()
                        if s.decided_at
                        else None,
                    }
                    for s in steps_for(db, req.id)
                ],
            }
        )
    histories = db.scalars(
        select(Audit)
        .where(Audit.company_id == member.company_id, Audit.quote_id == quote.id)
        .order_by(Audit.id.desc())
        .limit(40)
    ).all()
    revisions = db.scalars(
        select(Revision)
        .where(Revision.quote_id == quote.id)
        .order_by(Revision.version.desc())
    ).all()
    visible_revisions = [
        r
        for r in revisions
        if normal_scope(member, quote) or assigned(db, member, r.id)
    ]
    req = approval[0] if approval else None
    pending = (
        next((s for s in req["steps"] if s["status"] == "pending"), None)
        if req and req["status"] == "pending"
        else None
    )
    editable = can_edit(member, quote) and latest(db, quote.id).id == rev.id
    return {
        **summary(db, quote, rev, normal_scope(member, quote)),
        "payload": rev.payload,
        "lock_version": rev.lock_version,
        "editable": editable,
        "business_editable": can_edit(member, quote),
        "can_approve": bool(
            pending and pending["approver_id"] == member.id and rev.status == "pending"
        ),
        "can_withdraw": bool(
            req and req["status"] == "pending" and req["requester_id"] == member.id
        ),
        "approvals": approval,
        "revisions": [
            {"id": r.id, "version": r.version, "status": r.status}
            for r in visible_revisions
        ],
        "history": [
            {
                "id": a.id,
                "action": a.action,
                "detail": a.detail,
                "actor": member_name(db, a.actor_id),
                "created_at": a.created_at.isoformat(),
            }
            for a in histories
        ]
        if normal_scope(member, quote)
        else [],
    }


@app.get("/api/health")
def health(db: Session = Db):
    db.execute(select(1))
    return {"status": "ok", "database": "sqlite"}


def setup_required(db: Session) -> bool:
    return (
        db.scalar(select(Company.id).limit(1)) is None
        and db.scalar(select(User.id).limit(1)) is None
        and db.scalar(select(Member.id).limit(1)) is None
    )


def issue_session(db: Session, member: Member, response: Response):
    token = secrets.token_urlsafe(40)
    db.add(
        LoginSession(
            id=token_hash(token),
            membership_id=member.id,
            expires_at=now() + timedelta(hours=12),
        )
    )
    response.set_cookie(
        "estimate2_session",
        token,
        max_age=43200,
        httponly=True,
        samesite="lax",
        secure=os.getenv("COOKIE_SECURE") == "true",
        path="/",
    )


@app.get("/api/setup/status")
def initial_setup_status(db: Session = Db):
    demo_available = (
        db.scalar(select(User.id).where(User.username == "solo")) is not None
        and db.scalar(select(User.id).where(User.username == "staff")) is not None
    )
    result = {"required": setup_required(db), "demo_available": demo_available}
    if os.getenv("ESTIMATE2_DESKTOP_TOKEN"):
        result["desktop_mode"] = True
    return result


def desktop_launch_authorized(request: Request) -> None:
    secret = os.getenv("ESTIMATE2_DESKTOP_TOKEN")
    cookie = request.cookies.get("estimate2_desktop_launch", "")
    if not secret or not secrets.compare_digest(cookie, token_hash(secret)):
        raise HTTPException(403, "デスクトップアプリから起動してください。")


@app.get("/api/desktop/launch", include_in_schema=False)
def desktop_launch(token: str):
    secret = os.getenv("ESTIMATE2_DESKTOP_TOKEN")
    if not secret or not secrets.compare_digest(token, secret):
        raise HTTPException(404, "ページが見つかりません。")
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        "estimate2_desktop_launch",
        token_hash(secret),
        httponly=True,
        samesite="strict",
        path="/",
    )
    return response


@app.post("/api/desktop/setup", status_code=201)
def desktop_setup(
    body: DesktopSetup, request: Request, response: Response, db: Session = Db
):
    desktop_launch_authorized(request)
    if not setup_required(db):
        raise HTTPException(409, "初回セットアップは完了しています。")
    company = Company(name=body.company_name)
    db.add(company)
    db.flush()
    user = User(
        username="desktop_owner",
        display_name=body.display_name,
        password_hash=hash_password(secrets.token_urlsafe(48)),
    )
    db.add(user)
    db.flush()
    member = Member(company_id=company.id, user_id=user.id, role="admin")
    db.add(member)
    db.flush()
    audit(db, member, "初回セットアップ", detail=company.name)
    issue_session(db, member, response)
    return {"ok": True}


@app.post("/api/desktop/resume", include_in_schema=False)
def desktop_resume(request: Request, response: Response, db: Session = Db):
    desktop_launch_authorized(request)
    members = db.scalars(
        select(Member)
        .join(Company)
        .where(Member.active.is_(True), Company.active.is_(True))
        .limit(2)
    ).all()
    if len(members) != 1:
        raise HTTPException(409, "複数ユーザーのデータはログインが必要です。")
    issue_session(db, members[0], response)
    return {"ok": True}


@app.post("/api/setup", status_code=201)
def initial_setup(body: InitialSetup, response: Response, db: Session = Db):
    # get_db starts BEGIN IMMEDIATE before this check, so only one request can win.
    if not setup_required(db):
        raise HTTPException(409, "初回セットアップは完了しています。ログインしてください。")
    company = Company(name=body.company_name)
    db.add(company)
    db.flush()
    user = User(
        username=body.username,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()
    member = Member(company_id=company.id, user_id=user.id, role="admin")
    db.add(member)
    db.flush()
    audit(db, member, "初回セットアップ", detail=company.name)
    issue_session(db, member, response)
    return {"ok": True}


@app.post("/api/auth/login")
def login(body: Login, response: Response, db: Session = Db):
    user = db.scalar(select(User).where(User.username == body.username))
    valid = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "ユーザー名またはパスワードが違います。")
    member = db.scalar(
        select(Member)
        .join(Company)
        .where(
            Member.user_id == user.id, Member.active.is_(True), Company.active.is_(True)
        )
    )
    if not member:
        raise HTTPException(401, "利用できる事業者がありません。")
    issue_session(db, member, response)
    return {"ok": True}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, db: Session = Db):
    session = db.get(
        LoginSession, token_hash(request.cookies.get("estimate2_session", ""))
    )
    if session:
        db.delete(session)
    response.delete_cookie("estimate2_session", path="/")
    return {"ok": True}


def company_data(c):
    return {
        "id": c.id,
        "name": c.name,
        "address": c.address,
        "phone": c.phone,
        "approval_mode": c.approval_mode,
        "route": c.route,
        "route_version": c.route_version,
        "seal_default": c.seal_default,
        "registration_number": c.registration_number,
        "bank_details": c.bank_details,
    }


@app.get("/api/bootstrap")
def bootstrap(db: Session = Db, member: Member = Auth):
    users = db.execute(
        select(Member, User)
        .join(User)
        .where(Member.company_id == member.company_id)
        .order_by(Member.id)
    ).all()
    company = db.get(Company, member.company_id)
    return {
        "me": {
            "id": member.id,
            "name": member_name(db, member.id),
            "role": member.role,
            "section_id": member.section_id,
            "department_id": member.department_id,
        },
        "company": company_data(company),
        "seal_id": db.scalar(
            select(Seal.id).where(
                Seal.company_id == member.company_id, Seal.active.is_(True)
            )
        ),
        "members": [
            {
                "id": m.id,
                "username": u.username,
                "name": u.display_name,
                "role": m.role,
                "section_id": m.section_id,
                "department_id": m.department_id,
                "active": m.active,
            }
            for m, u in users
        ],
        "departments": [
            {"id": x.id, "name": x.name}
            for x in db.scalars(
                select(Department).where(Department.company_id == member.company_id)
            )
        ],
        "sections": [
            {"id": x.id, "name": x.name, "department_id": x.department_id}
            for x in db.scalars(
                select(Section).where(Section.company_id == member.company_id)
            )
        ],
    }


@app.get("/api/customers")
def customers(db: Session = Db, member: Member = Auth):
    return [
        {
            "id": c.id,
            "name": c.name,
            "contact": c.contact,
            "email": c.email,
            "address": c.address,
        }
        for c in db.scalars(
            select(Customer)
            .where(Customer.company_id == member.company_id)
            .order_by(Customer.name)
        )
    ]


@app.post("/api/customers", status_code=201)
def create_customer(body: CustomerInput, db: Session = Db, member: Member = Auth):
    c = Customer(company_id=member.company_id, **body.model_dump())
    db.add(c)
    db.flush()
    audit(db, member, "顧客を登録", detail=c.name)
    return {"id": c.id, **body.model_dump()}


@app.put("/api/customers/{cid}")
def update_customer(
    cid: int, body: CustomerInput, db: Session = Db, member: Member = Auth
):
    c = scoped(db, Customer, cid, member)
    for key, value in body.model_dump().items():
        setattr(c, key, value)
    audit(db, member, "顧客を更新", detail=c.name)
    return {"id": c.id, **body.model_dump()}


@app.get("/api/quotes")
def quotes(q: str = "", status: str = "", db: Session = Db, member: Member = Auth):
    result = []
    for quote in db.scalars(
        select(Quote)
        .where(Quote.company_id == member.company_id)
        .order_by(Quote.id.desc())
    ):
        if not normal_scope(member, quote):
            continue
        rev = latest(db, quote.id)
        entry = summary(db, quote, rev)
        if status and rev.status != status:
            continue
        if (
            q
            and q.lower()
            not in " ".join(
                [
                    entry["title"],
                    entry["customer_name"],
                    entry["number"] or "",
                    entry["owner_name"],
                ]
            ).lower()
        ):
            continue
        result.append(entry)
    return result


@app.post("/api/quotes", status_code=201)
def create_quote(body: QuoteInput, db: Session = Db, member: Member = Auth):
    payload = payload_for(db, member, body)
    project, snapshots = projects.quote_scope(db, member, body)
    payload["request_snapshots"] = snapshots
    quote = Quote(
        project_id=project.id if project else None,
        company_id=member.company_id,
        creator_id=member.id,
        owner_id=project.owner_id if project else member.id,
        department_id=project.department_id if project else member.department_id,
        section_id=project.section_id if project else member.section_id,
    )
    db.add(quote)
    db.flush()
    if project:
        payload["owner_name"] = member_name(db, project.owner_id)
        owner = db.get(Member, project.owner_id)
        payload["organization"] = " / ".join(
            x.name
            for x in [
                db.get(Department, owner.department_id)
                if owner.department_id
                else None,
                db.get(Section, owner.section_id) if owner.section_id else None,
            ]
            if x
        )
    rev = new_revision(db, quote, payload)
    audit(db, member, "見積書を作成", quote.id)
    db.flush()
    return detail(db, member, quote, rev)


@app.get("/api/revisions/{rid}")
def read_revision(rid: int, db: Session = Db, member: Member = Auth):
    quote, rev = get_revision(db, member, rid)
    return detail(db, member, quote, rev)


@app.put("/api/revisions/{rid}")
def update_revision(
    rid: int, body: QuoteInput, db: Session = Db, member: Member = Auth
):
    quote, rev = get_revision(db, member, rid, True)
    require_edit(db, member, quote, rev)
    check_version(rev, body.lock_version)
    if rev.status not in ("draft", "returned"):
        raise HTTPException(409, "編集できるのは下書き・差戻しの見積です。")
    payload = payload_for(db, member, body, rev.payload.get("seal_id"))
    if body.project_id != quote.project_id:
        raise HTTPException(
            409,
            "見積の案件は作成後に変更できません。案件から新しく見積を作成してください。",
        )
    _, snapshots = projects.quote_scope(db, member, body)
    payload["request_snapshots"] = snapshots
    # Manager edits do not change the responsible person's name or original organization.
    payload["owner_name"] = member_name(db, quote.owner_id)
    payload["organization"] = rev.payload.get("organization", "")
    rev.payload = payload
    rev.subtotal = Decimal(payload["subtotal"])
    rev.tax = Decimal(payload["tax"])
    rev.total = Decimal(payload["total"])
    touch(rev)
    audit(db, member, "見積書を更新", quote.id)
    db.flush()
    return detail(db, member, quote, rev)


@app.get("/api/approvals")
def approvals(db: Session = Db, member: Member = Auth):
    result = []
    for step in db.scalars(
        select(ApprovalStep).where(
            ApprovalStep.company_id == member.company_id,
            ApprovalStep.approver_id == member.id,
            ApprovalStep.status == "pending",
        )
    ):
        req = db.get(ApprovalRequest, step.request_id)
        if req.status != "pending":
            continue
        rev = db.get(Revision, req.revision_id)
        quote = db.get(Quote, rev.quote_id)
        result.append(
            {
                **summary(db, quote, rev, normal_scope(member, quote)),
                "step_name": step.name,
                "position": step.position,
                "step_count": len(steps_for(db, req.id)),
                "requester_name": member_name(db, req.requester_id),
            }
        )
    return result


@app.post("/api/revisions/{rid}/{action}")
def act(rid: int, action: str, body: Action, db: Session = Db, member: Member = Auth):
    quote, rev = get_revision(db, member, rid, True)
    if action == "issue" and rev.status == "issued":
        require_edit(db, member, quote, rev)
        return detail(db, member, quote, rev)
    check_version(rev, body.lock_version)
    req = active_request(db, rev.id)
    if action in ("approve", "return"):
        if rev.status != "pending" or not req or req.status != "pending":
            raise HTTPException(409, "承認待ちの申請ではありません。")
        steps = steps_for(db, req.id)
        step = next((s for s in steps if s.status == "pending"), None)
        if not step or step.approver_id != member.id:
            raise HTTPException(403, "現在の段階の承認者のみ操作できます。")
        if member.id in (quote.creator_id, req.requester_id):
            raise HTTPException(403, "自己承認はできません。")
        if action == "return" and not body.comment:
            raise HTTPException(422, "差戻し理由を入力してください。")
        step.comment = body.comment
        step.decided_at = now()
        if action == "return":
            step.status = "returned"
            req.status = "returned"
            rev.status = "returned"
            for s in steps:
                if s.status == "waiting":
                    s.status = "cancelled"
            audit(db, member, "差戻し", quote.id, f"{step.name}：{body.comment}")
        else:
            step.status = "approved"
            following = next((s for s in steps if s.status == "waiting"), None)
            if following:
                following.status = "pending"
            else:
                req.status = "approved"
                rev.status = "approved"
            audit(db, member, "承認", quote.id, f"{step.name} {body.comment}".strip())
    elif action == "withdraw":
        if not req or req.status != "pending" or req.requester_id != member.id:
            raise HTTPException(403, "申請者のみ取下げできます。")
        req.status = "withdrawn"
        rev.status = "draft"
        for s in steps_for(db, req.id):
            if s.status in ("pending", "waiting"):
                s.status = "cancelled"
        audit(db, member, "申請を取下げ", quote.id)
    else:
        require_edit(db, member, quote, rev)
        company = db.scalar(
            select(Company).where(Company.id == member.company_id)
        )
        if action == "submit":
            if company.approval_mode != "sequential":
                raise HTTPException(409, "この事業者は承認なしで発行できます。")
            if rev.status not in ("draft", "returned"):
                raise HTTPException(409, "この状態では申請できません。")
            if not company.route:
                raise HTTPException(422, "承認経路を設定してください。")
            chosen = []
            for config in company.route:
                candidates = [config["approver_id"], config.get("backup_id")]
                valid = None
                for candidate in candidates:
                    if not candidate or candidate in [
                        quote.creator_id,
                        member.id,
                        *chosen,
                    ]:
                        continue
                    m = db.scalar(
                        select(Member).where(
                            Member.id == candidate,
                            Member.company_id == member.company_id,
                            Member.active.is_(True),
                        )
                    )
                    if m:
                        valid = m.id
                        break
                if not valid:
                    raise HTTPException(
                        422,
                        f"「{config['name']}」に自己承認・重複以外の承認者がいません。会社設定を確認してください。",
                    )
                chosen.append(valid)
            req = ApprovalRequest(
                company_id=member.company_id,
                revision_id=rev.id,
                requester_id=member.id,
                route_version=company.route_version,
                snapshot=copy.deepcopy(rev.payload),
            )
            db.add(req)
            db.flush()
            for i, (config, uid) in enumerate(zip(company.route, chosen)):
                db.add(
                    ApprovalStep(
                        company_id=member.company_id,
                        request_id=req.id,
                        position=i + 1,
                        name=config["name"],
                        approver_id=uid,
                        status="pending" if i == 0 else "waiting",
                    )
                )
            rev.status = "pending"
            audit(db, member, "承認を申請", quote.id, f"{len(chosen)}段階の承認")
        elif action == "reopen":
            if rev.status != "approved":
                raise HTTPException(409, "承認済みの見積のみ編集に戻せます。")
            rev.status = "draft"
            if req:
                req.status = "invalidated"
            audit(
                db,
                member,
                "承認を解除して編集",
                quote.id,
                "再発行には会社設定に応じた再承認が必要",
            )
        elif action == "issue":
            allowed = rev.status == "approved" or (
                company.approval_mode == "none" and rev.status in ("draft", "returned")
            )
            if not allowed:
                raise HTTPException(409, "すべての承認が完了してから発行してください。")
            if rev.status == "approved" and (
                not req
                or req.status != "approved"
                or any(s.status != "approved" for s in steps_for(db, req.id))
            ):
                raise HTTPException(409, "承認状態を確認してください。")
            if not quote.number:
                quote.number = f"Q-{date.today().year}-{company.next_number:06d}"
                company.next_number += 1
            rev.pdf = generate_pdf(
                rev.payload,
                quote.number,
                rev.version,
                date.today().isoformat(),
                seal_image=seal_bytes(db, member.company_id, rev.payload),
            )
            rev.status = "issued"
            rev.issued_at = now()
            audit(
                db,
                member,
                "見積書を発行",
                quote.id,
                f"{quote.number} 第{rev.version}版",
            )
        elif action in ("revise", "duplicate"):
            if action == "revise" and rev.status != "issued":
                raise HTTPException(409, "発行済みの見積のみ改版できます。")
            payload = copy.deepcopy(rev.payload)
            payload["seal_id"] = (
                db.scalar(
                    select(Seal.id).where(
                        Seal.company_id == member.company_id, Seal.active.is_(True)
                    )
                )
                if payload.get("seal_id")
                else None
            )
            if action == "duplicate":
                payload["project_id"] = None
                payload["request_refs"] = []
                payload["request_snapshots"] = []
                quote = Quote(
                    company_id=member.company_id,
                    creator_id=member.id,
                    owner_id=member.id,
                    department_id=member.department_id,
                    section_id=member.section_id,
                )
                db.add(quote)
                db.flush()
                payload["title"] += "（コピー）"
                payload["owner_name"] = member_name(db, member.id)
                payload["organization"] = " / ".join(
                    x.name
                    for x in [
                        db.get(Department, member.department_id)
                        if member.department_id
                        else None,
                        db.get(Section, member.section_id)
                        if member.section_id
                        else None,
                    ]
                    if x
                )
            new = new_revision(
                db, quote, payload, rev.version + 1 if action == "revise" else 1
            )
            audit(
                db,
                member,
                "改版を作成" if action == "revise" else "見積書を複製",
                quote.id,
            )
            db.flush()
            return detail(db, member, quote, new)
        else:
            raise HTTPException(404, "操作が見つかりません。")
    touch(rev)
    db.flush()
    return detail(db, member, quote, rev)


@app.get("/api/revisions/{rid}/pdf")
def pdf(rid: int, download: bool = False, db: Session = Db, member: Member = Auth):
    quote, rev = get_revision(db, member, rid)
    content = (
        rev.pdf
        if rev.status == "issued"
        else generate_pdf(
            rev.payload,
            None,
            rev.version,
            seal_image=seal_bytes(db, member.company_id, rev.payload),
        )
    )
    if not content:
        raise HTTPException(409, "PDFがまだ生成されていません。")
    filename = f"{quote.number or 'draft'}-v{rev.version}.pdf"
    disposition = "attachment" if download else "inline"
    return Response(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


@app.put("/api/settings")
def settings(body: SettingsInput, db: Session = Db, member: Member = Auth):
    require_admin(member)
    company = db.scalar(
        select(Company).where(Company.id == member.company_id)
    )
    if body.route_version != company.route_version:
        raise HTTPException(409, "設定が更新されています。再読み込みしてください。")
    if body.approval_mode == "sequential" and not body.route:
        raise HTTPException(422, "1段階以上の承認経路を追加してください。")
    for step in body.route:
        for uid in [step.approver_id, step.backup_id]:
            if uid:
                m = scoped(db, Member, uid, member)
                if not m.active:
                    raise HTTPException(422, "有効な承認者を指定してください。")
    for key, value in body.model_dump(exclude={"route_version"}).items():
        setattr(company, key, value)
    company.route_version += 1
    audit(
        db,
        member,
        "会社設定を更新",
        detail=f"承認方式：{body.approval_mode} / 経路設定 v{company.route_version}",
    )
    db.flush()
    return company_data(company)


@app.post("/api/members", status_code=201)
def create_member(body: MemberInput, db: Session = Db, member: Member = Auth):
    require_admin(member)
    section = scoped(db, Section, body.section_id, member) if body.section_id else None
    if body.role in ("section_manager", "department_manager") and not section:
        raise HTTPException(422, "部・課の管理者には所属課を設定してください。")
    user = User(
        username=body.username,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()
    new = Member(
        company_id=member.company_id,
        user_id=user.id,
        role=body.role,
        department_id=section.department_id if section else None,
        section_id=section.id if section else None,
    )
    db.add(new)
    db.flush()
    audit(db, member, "ユーザーを登録", detail=body.display_name)
    return {"id": new.id}


@app.post("/api/organizations", status_code=201)
def create_org(body: OrganizationInput, db: Session = Db, member: Member = Auth):
    require_admin(member)
    if body.department_id:
        scoped(db, Department, body.department_id, member)
        org = Section(
            company_id=member.company_id,
            department_id=body.department_id,
            name=body.name,
        )
    else:
        org = Department(company_id=member.company_id, name=body.name)
    db.add(org)
    db.flush()
    audit(db, member, "組織を登録", detail=body.name)
    return {"id": org.id}


@app.get("/api/audit")
def audit_logs(db: Session = Db, member: Member = Auth):
    require_admin(member)
    return [
        {
            "id": a.id,
            "action": a.action,
            "detail": a.detail,
            "actor": member_name(db, a.actor_id),
            "created_at": a.created_at.isoformat(),
        }
        for a in db.scalars(
            select(Audit)
            .where(Audit.company_id == member.company_id)
            .order_by(Audit.id.desc())
            .limit(100)
        )
    ]


def seal_bytes(db, company_id, payload):
    if not payload.get("seal_id"):
        return None
    return db.scalar(
        select(Seal.image).where(
            Seal.company_id == company_id, Seal.id == payload["seal_id"]
        )
    )


from .commerce import router as commerce_router

app.include_router(commerce_router)
from . import projects

app.include_router(projects.router)
from .attachments import router as attachments_router

app.include_router(attachments_router)
from .manual import router as manual_router

app.include_router(manual_router)

if (ROOT / "frontend/dist").exists():
    app.mount(
        "/", StaticFiles(directory=ROOT / "frontend/dist", html=True), name="frontend"
    )
