"""Small-business sales flow. All mutations serialize on the source quote."""

import base64
import binascii
import copy
from datetime import date
from io import BytesIO

from fastapi import APIRouter, HTTPException, Response
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import main as core
from .models import Company, Invoice, Member, Order, Quote, Revision, Seal
from .schemas import (
    Action,
    InvoiceInput,
    OrderInput,
    OrderUpdate,
    PaymentInput,
    SalesInput,
    SealInput,
)

router = APIRouter(prefix="/api")
Db, Auth = core.Db, core.Auth


def business_quote(db, member, qid, write=False):
    q = core.scoped(db, Quote, qid, member)
    if not core.normal_scope(member, q):
        raise HTTPException(404, "データが見つかりません。")
    if write:
        if not core.can_edit(member, q):
            raise HTTPException(403, "担当者または対象範囲の管理者のみ変更できます。")
        db.execute(select(Quote.id).where(Quote.id == q.id)).first()
        db.refresh(q)
    return q


def get_order(db, member, oid, write=False):
    order = core.scoped(db, Order, oid, member)
    quote = business_quote(db, member, order.quote_id, write)
    if write:
        db.refresh(order)
    return order, quote


def get_invoice(db, member, iid, write=False):
    inv = core.scoped(db, Invoice, iid, member)
    order, quote = get_order(db, member, inv.order_id, write)
    if write:
        db.refresh(inv)
    return inv, order, quote


def invoice_data(inv, editable):
    return {
        "id": inv.id,
        "order_id": inv.order_id,
        "number": inv.number,
        "status": inv.status,
        "payload": inv.payload,
        "total": str(inv.total),
        "issue_on": inv.issue_on,
        "transaction_on": inv.transaction_on,
        "due_on": inv.due_on,
        "paid_on": inv.paid_on,
        "payment_note": inv.payment_note,
        "overdue": inv.status == "issued" and inv.due_on < date.today(),
        "lock_version": inv.lock_version,
        "editable": editable,
    }


def order_data(db, member, order, quote):
    rev = db.get(Revision, order.revision_id)
    invs = db.scalars(
        select(Invoice)
        .where(Invoice.company_id == member.company_id, Invoice.order_id == order.id)
        .order_by(Invoice.id.desc())
    ).all()
    return {
        "id": order.id,
        "quote_id": quote.id,
        "revision_id": rev.id,
        "quote_number": quote.number,
        "version": rev.version,
        "title": rev.payload["title"],
        "customer_name": rev.payload["customer"]["name"],
        "total": str(rev.total),
        "ordered_on": order.ordered_on,
        "delivery_on": order.delivery_on,
        "status": order.status,
        "note": order.note,
        "lock_version": order.lock_version,
        "editable": core.can_edit(member, quote),
        "invoices": [invoice_data(i, core.can_edit(member, quote)) for i in invs],
    }


@router.post("/seals", status_code=201)
def upload_seal(body: SealInput, db: Session = Db, member: Member = Auth):
    core.require_admin(member)
    try:
        raw = base64.b64decode(body.image_base64, validate=True)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError()
        with Image.open(BytesIO(raw)) as im:
            if (
                im.format not in ("PNG", "JPEG")
                or max(im.size) > 2000
                or min(im.size) < 10
                or getattr(im, "n_frames", 1) != 1
            ):
                raise ValueError()
            im.load()
            output = BytesIO()
            im.convert("RGBA").save(output, format="PNG")
    except (
        ValueError,
        binascii.Error,
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
    ):
        raise HTTPException(
            422, "PNG/JPEG、2MB以下、各辺10〜2000pxの静止画像を選択してください。"
        )
    db.execute(
        select(Company.id).where(Company.id == member.company_id)
    ).first()
    for old in db.scalars(
        select(Seal).where(Seal.company_id == member.company_id, Seal.active.is_(True))
    ):
        old.active = False
    seal = Seal(company_id=member.company_id, image=output.getvalue())
    db.add(seal)
    db.flush()
    core.audit(db, member, "印鑑画像を登録", detail=f"画像版 {seal.id}")
    return {"id": seal.id}


@router.get("/seals/{sid}")
def read_seal(sid: int, db: Session = Db, member: Member = Auth):
    seal = core.scoped(db, Seal, sid, member)
    return Response(seal.image, media_type="image/png")


@router.delete("/seals/current")
def disable_seal(db: Session = Db, member: Member = Auth):
    core.require_admin(member)
    company = db.scalar(
        select(Company).where(Company.id == member.company_id)
    )
    for seal in db.scalars(
        select(Seal).where(Seal.company_id == member.company_id, Seal.active.is_(True))
    ):
        seal.active = False
    company.seal_default = False
    company.route_version += 1
    core.audit(db, member, "印鑑画像の利用を停止")
    return {"ok": True}


@router.put("/quotes/{qid}/sales")
def sales(qid: int, body: SalesInput, db: Session = Db, member: Member = Auth):
    q = business_quote(db, member, qid, True)
    if q.sales_version != body.lock_version:
        raise HTTPException(409, "更新されています。再読み込みしてください。")
    if db.scalar(
        select(Order.id).where(Order.quote_id == q.id, Order.status != "cancelled")
    ):
        raise HTTPException(409, "受注後の状態は受注管理から変更してください。")
    if body.sales_status != "open" and not db.scalar(
        select(Revision.id).where(
            Revision.quote_id == q.id, Revision.status == "issued"
        )
    ):
        raise HTTPException(409, "正式発行した見積から結果を記録してください。")
    if body.sales_status == "sent" and (
        not body.sent_on or body.sent_on > date.today()
    ):
        raise HTTPException(422, "提出日には今日以前の日付を入力してください。")
    q.sales_status, q.sent_on = body.sales_status, body.sent_on
    q.sales_version += 1
    core.audit(db, member, "見積の営業状況を更新", q.id, body.sales_status)
    return {"ok": True}


@router.get("/orders")
def list_orders(db: Session = Db, member: Member = Auth):
    result = []
    for o in db.scalars(
        select(Order)
        .where(Order.company_id == member.company_id)
        .order_by(Order.id.desc())
    ):
        q = db.get(Quote, o.quote_id)
        if core.normal_scope(member, q):
            result.append(order_data(db, member, o, q))
    return result


@router.post("/orders", status_code=201)
def create_order(body: OrderInput, db: Session = Db, member: Member = Auth):
    rev = core.scoped(db, Revision, body.revision_id, member)
    q = business_quote(db, member, rev.quote_id, True)
    db.refresh(rev)
    old = db.scalar(select(Order).where(Order.quote_id == q.id))
    if old:
        if old.revision_id != rev.id:
            raise HTTPException(
                409,
                "この見積は既に別の版で受注しています。受注管理を確認してください。",
            )
        return order_data(db, member, old, q)
    if rev.status != "issued":
        raise HTTPException(409, "正式発行した見積の版を選択してください。")
    if body.ordered_on > date.today() or (
        body.delivery_on and body.delivery_on < body.ordered_on
    ):
        raise HTTPException(
            422, "受注日は今日以前、納期は受注日以降を指定してください。"
        )
    order = Order(company_id=member.company_id, quote_id=q.id, **body.model_dump())
    db.add(order)
    db.flush()
    core.audit(
        db,
        member,
        "受注を登録",
        q.id,
        f"{q.number} 第{rev.version}版 / 受注 {order.id}",
    )
    return order_data(db, member, order, q)


@router.get("/orders/{oid}")
def read_order(oid: int, db: Session = Db, member: Member = Auth):
    order, q = get_order(db, member, oid)
    return order_data(db, member, order, q)


@router.put("/orders/{oid}")
def update_order(oid: int, body: OrderUpdate, db: Session = Db, member: Member = Auth):
    order, q = get_order(db, member, oid, True)
    core.check_version(order, body.lock_version)
    if body.ordered_on > date.today() or (
        body.delivery_on and body.delivery_on < body.ordered_on
    ):
        raise HTTPException(422, "受注日と納期を確認してください。")
    if body.status == "cancelled" and db.scalar(
        select(Invoice.id).where(Invoice.order_id == oid, Invoice.status != "void")
    ):
        raise HTTPException(
            409,
            "先に請求書を取り消してください。入金済みの場合は入金記録の訂正が必要です。",
        )
    if body.status == "cancelled" and not body.note:
        raise HTTPException(422, "メモに取消理由を入力してください。")
    for k, v in body.model_dump(exclude={"lock_version"}).items():
        setattr(order, k, v)
    core.touch(order)
    core.audit(
        db, member, "受注を更新", q.id, f"受注 {oid} / {order.status} / {order.note}"
    )
    return order_data(db, member, order, q)


def apply_invoice(inv, body):
    if body.due_on < body.issue_on:
        raise HTTPException(422, "支払期限は請求日以降を指定してください。")
    inv.issue_on, inv.transaction_on, inv.due_on = (
        body.issue_on,
        body.transaction_on,
        body.due_on,
    )
    p = copy.deepcopy(inv.payload)
    p.update(body.model_dump(mode="json", exclude={"lock_version"}))
    inv.payload = p


@router.post("/orders/{oid}/invoices", status_code=201)
def create_invoice(
    oid: int, body: InvoiceInput, db: Session = Db, member: Member = Auth
):
    order, q = get_order(db, member, oid, True)
    if order.status == "cancelled":
        raise HTTPException(409, "取消済みの受注から請求できません。")
    old = db.scalar(
        select(Invoice).where(Invoice.order_id == oid, Invoice.status != "void")
    )
    if old:
        return invoice_data(old, True)
    rev = db.get(Revision, order.revision_id)
    payload = copy.deepcopy(rev.payload)
    payload["source_quote"] = f"{q.number} 第{rev.version}版"
    inv = Invoice(
        company_id=member.company_id, order_id=oid, payload=payload, total=rev.total
    )
    apply_invoice(inv, body)
    db.add(inv)
    db.flush()
    core.audit(db, member, "請求書の下書きを作成", q.id, f"請求 {inv.id}")
    return invoice_data(inv, True)


@router.get("/invoices")
def list_invoices(db: Session = Db, member: Member = Auth):
    result = []
    for inv in db.scalars(
        select(Invoice)
        .where(Invoice.company_id == member.company_id)
        .order_by(Invoice.id.desc())
    ):
        order = db.get(Order, inv.order_id)
        quote = db.get(Quote, order.quote_id)
        if core.normal_scope(member, quote):
            result.append(invoice_data(inv, core.can_edit(member, quote)))
    return result


@router.get("/invoices/{iid}")
def read_invoice(iid: int, db: Session = Db, member: Member = Auth):
    inv, order, q = get_invoice(db, member, iid)
    return invoice_data(inv, core.can_edit(member, q))


@router.put("/invoices/{iid}")
def update_invoice(
    iid: int, body: InvoiceInput, db: Session = Db, member: Member = Auth
):
    inv, order, q = get_invoice(db, member, iid, True)
    core.check_version(inv, body.lock_version)
    if inv.status != "draft":
        raise HTTPException(409, "下書きの請求書のみ編集できます。")
    apply_invoice(inv, body)
    core.touch(inv)
    core.audit(db, member, "請求書を更新", q.id, f"請求 {iid}")
    return invoice_data(inv, True)


@router.post("/invoices/{iid}/payment")
def payment(iid: int, body: PaymentInput, db: Session = Db, member: Member = Auth):
    inv, order, q = get_invoice(db, member, iid, True)
    core.check_version(inv, body.lock_version)
    if inv.status != "issued":
        raise HTTPException(409, "発行済み・未入金の請求書のみ入金確認できます。")
    if body.paid_on > date.today():
        raise HTTPException(422, "入金日は今日以前を指定してください。")
    inv.status, inv.paid_on, inv.payment_note = "paid", body.paid_on, body.note
    core.touch(inv)
    core.audit(
        db,
        member,
        "全額入金を確認",
        q.id,
        f"{inv.number} / {inv.total}円 / {body.paid_on} / {body.note}",
    )
    return invoice_data(inv, True)


@router.post("/invoices/{iid}/{action}")
def invoice_action(
    iid: int, action: str, body: Action, db: Session = Db, member: Member = Auth
):
    inv, order, q = get_invoice(db, member, iid, True)
    if action == "issue" and inv.status in ("issued", "paid"):
        return invoice_data(inv, True)
    core.check_version(inv, body.lock_version)
    if action == "issue":
        if inv.status != "draft" or order.status == "cancelled":
            raise HTTPException(409, "この請求書は発行できません。")
        company = db.scalar(
            select(Company).where(Company.id == member.company_id)
        )
        inv.number = f"I-{inv.issue_on.year}-{company.next_invoice:06d}"
        company.next_invoice += 1
        inv.pdf = core.generate_pdf(
            inv.payload,
            inv.number,
            1,
            inv.issue_on.isoformat(),
            document_kind="invoice",
            seal_image=core.seal_bytes(db, member.company_id, inv.payload),
        )
        inv.status = "issued"
        label = "請求書を発行"
    elif action == "void":
        if inv.status not in ("draft", "issued") or not body.comment:
            raise HTTPException(409, "未入金の請求書に取消理由を入力してください。")
        inv.status = "void"
        label = "請求書を取消"
    elif action == "unpay":
        if inv.status != "paid" or not body.comment:
            raise HTTPException(409, "入金済みの請求書に訂正理由を入力してください。")
        inv.status, inv.paid_on, inv.payment_note = "issued", None, ""
        label = "入金記録を訂正"
    else:
        raise HTTPException(404, "操作が見つかりません。")
    core.touch(inv)
    core.audit(db, member, label, q.id, f"{inv.number or iid} / {body.comment}")
    return invoice_data(inv, True)


@router.get("/invoices/{iid}/pdf")
def invoice_pdf(
    iid: int, download: bool = False, db: Session = Db, member: Member = Auth
):
    inv, order, q = get_invoice(db, member, iid)
    if inv.number and not inv.pdf:
        raise HTTPException(
            409, "保存済みPDFが見つかりません。管理者に確認してください。"
        )
    content = inv.pdf or core.generate_pdf(
        inv.payload,
        None,
        1,
        inv.issue_on.isoformat(),
        document_kind="invoice",
        seal_image=core.seal_bytes(db, member.company_id, inv.payload),
    )
    return Response(
        content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{"attachment" if download else "inline"}; filename="{inv.number or "invoice-draft"}.pdf"'
        },
    )
