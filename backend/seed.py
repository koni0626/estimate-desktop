from datetime import date, timedelta
from sqlalchemy import select
from backend.app.db import SessionLocal
from backend.app.models import (
    Company,
    Customer,
    Department,
    Section,
    User,
    Member,
    Quote,
    ApprovalRequest,
    ApprovalStep,
    Audit,
    now,
)
from backend.app.security import hash_password
from backend.app.schemas import QuoteInput
from backend.app.main import payload_for, new_revision
from backend.app.pdf import generate_pdf


def seed():
    with SessionLocal.begin() as db:
        if db.scalar(select(Company.id).limit(1)):
            print("Demo data already exists; kept unchanged.")
            return
        solo = Company(
            name="ひだまりデザイン事務所",
            address="東京都目黒区中目黒 1-8-12",
            phone="03-1234-5678",
        )
        team = Company(
            name="合同会社ノースワークス",
            address="東京都渋谷区神宮前 3-12-8",
            phone="03-9876-5432",
            approval_mode="sequential",
        )
        db.add_all([solo, team])
        db.flush()
        dep = Department(company_id=team.id, name="事業開発部")
        db.add(dep)
        db.flush()
        sec = Section(company_id=team.id, department_id=dep.id, name="クリエイティブ課")
        db.add(sec)
        db.flush()
        othersec = Section(company_id=team.id, department_id=dep.id, name="営業課")
        db.add(othersec)
        db.flush()

        def user(company, username, name, role, section=None):
            u = User(
                username=username,
                display_name=name,
                password_hash=hash_password("demo1234"),
            )
            db.add(u)
            db.flush()
            m = Member(
                company_id=company.id,
                user_id=u.id,
                role=role,
                section_id=section.id if section else None,
                department_id=section.department_id if section else None,
            )
            db.add(m)
            db.flush()
            return m

        owner = user(solo, "solo", "山田 ひなた", "admin")
        admin = user(team, "admin", "中村 健太", "admin", sec)
        staff = user(team, "staff", "佐藤 葵", "member", sec)
        manager = user(team, "manager", "高橋 直人", "section_manager", sec)
        director = user(team, "director", "鈴木 美咲", "department_manager", sec)
        outsider = user(team, "sales", "田中 悠", "member", othersec)
        team.route = [
            {"name": "課長確認", "approver_id": manager.id, "backup_id": admin.id},
            {"name": "部長承認", "approver_id": director.id, "backup_id": admin.id},
        ]

        def customer(company, name, contact, address):
            c = Customer(
                company_id=company.id,
                name=name,
                contact=contact,
                address=address,
                email="",
            )
            db.add(c)
            db.flush()
            return c

        clients = [
            customer(
                solo, "株式会社 森と暮らし", "山田 様", "東京都世田谷区等々力 2-6-10"
            ),
            customer(solo, "喫茶 こもれび", "吉田 様", "東京都目黒区青葉台 1-5-3"),
            customer(solo, "合同会社 LINO", "松本 様", "神奈川県鎌倉市小町 2-12-5"),
            customer(solo, "アトリエ 青", "石井 様", "東京都杉並区高円寺南 3-7-2"),
        ]
        teamclient = customer(
            team, "株式会社 山の音", "伊藤 様", "長野県松本市深志 1-2-3"
        )

        def quote(member, client, title, amount, days=0, issued=False, pending=False):
            body = QuoteInput(
                title=title,
                customer_id=client.id,
                valid_until=date.today() + timedelta(days=30),
                delivery="ご発注から約4週間",
                notes="ご不明な点がございましたら、お気軽にお問い合わせください。",
                items=[
                    {
                        "name": title,
                        "quantity": "1",
                        "unit": "式",
                        "unit_price": str(amount),
                        "tax_rate": 10,
                    }
                ],
            )
            q = Quote(
                company_id=member.company_id,
                creator_id=member.id,
                owner_id=member.id,
                department_id=member.department_id,
                section_id=member.section_id,
            )
            db.add(q)
            db.flush()
            r = new_revision(db, q, payload_for(db, member, body))
            r.updated_at = now() - timedelta(days=days)
            c = db.get(Company, member.company_id)
            if issued:
                q.number = f"Q-{date.today().year}-{c.next_number:06d}"
                c.next_number += 1
                r.status = "issued"
                r.issued_at = now() - timedelta(days=days)
                r.pdf = generate_pdf(
                    r.payload, q.number, 1, r.issued_at.date().isoformat()
                )
            if pending:
                r.status = "pending"
                req = ApprovalRequest(
                    company_id=c.id,
                    revision_id=r.id,
                    requester_id=member.id,
                    route_version=c.route_version,
                    snapshot=r.payload,
                )
                db.add(req)
                db.flush()
                for i, s in enumerate(c.route):
                    db.add(
                        ApprovalStep(
                            company_id=c.id,
                            request_id=req.id,
                            position=i + 1,
                            name=s["name"],
                            approver_id=s["approver_id"],
                            status="pending" if i == 0 else "waiting",
                        )
                    )
            db.add(
                Audit(
                    company_id=c.id,
                    quote_id=q.id,
                    actor_id=member.id,
                    action="デモ見積を作成",
                    detail="動作確認用のサンプルデータ",
                )
            )

        quote(owner, clients[0], "ブランドサイト リニューアル", 320000, 8, True)
        quote(owner, clients[1], "ショップカード・メニュー制作", 65000, 6, True)
        quote(owner, clients[2], "秋のキャンペーンビジュアル制作", 180000, 5, True)
        quote(owner, clients[3], "展示会リーフレット デザイン", 85000, 4, True)
        quote(owner, clients[0], "採用ページ デザイン・実装", 240000, 2)
        quote(owner, clients[1], "季節限定メニュー 撮影・制作", 48000, 1)
        quote(owner, clients[2], "オンラインストア バナー制作", 72000, 0)
        quote(staff, teamclient, "コーポレートサイト制作", 580000, 1, pending=True)
        quote(staff, teamclient, "ブランドガイドライン制作", 220000)
        quote(outsider, teamclient, "営業資料制作", 90000)
        print(
            "Demo ready: solo / staff / manager / director / admin / sales (password: demo1234)"
        )


if __name__ == "__main__":
    seed()
