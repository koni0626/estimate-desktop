from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Index,
    text,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    JSON,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, UTCDateTime


def now():
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(300), default="")
    phone: Mapped[str] = mapped_column(String(60), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_mode: Mapped[str] = mapped_column(String(20), default="none")
    route: Mapped[list] = mapped_column(JSON, default=list)
    route_version: Mapped[int] = mapped_column(default=1)
    next_number: Mapped[int] = mapped_column(default=1)
    next_invoice: Mapped[int] = mapped_column(default=1, server_default="1")
    seal_default: Mapped[bool] = mapped_column(default=False, server_default="false")
    registration_number: Mapped[str] = mapped_column(
        String(14), default="", server_default=""
    )
    bank_details: Mapped[str] = mapped_column(
        String(500), default="", server_default=""
    )


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("company_id", "id"),
        UniqueConstraint("company_id", "name"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(100))


class Section(Base):
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("company_id", "id"),
        UniqueConstraint("company_id", "department_id", "id"),
        ForeignKeyConstraint(
            ["company_id", "department_id"],
            ["departments.company_id", "departments.id"],
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    department_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(300))


class Member(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("company_id", "id"),
        UniqueConstraint("company_id", "user_id"),
        ForeignKeyConstraint(
            ["company_id", "department_id"],
            ["departments.company_id", "departments.id"],
        ),
        ForeignKeyConstraint(
            ["company_id", "department_id", "section_id"],
            ["sections.company_id", "sections.department_id", "sections.id"],
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(30), default="member")
    department_id: Mapped[int | None] = mapped_column(Integer)
    section_id: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class LoginSession(Base):
    __tablename__ = "login_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id"))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("company_id", "id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(150))
    contact: Mapped[str] = mapped_column(String(120), default="")
    address: Mapped[str] = mapped_column(String(300), default="")
    email: Mapped[str] = mapped_column(String(200), default="")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("company_id", "id"),
        ForeignKeyConstraint(
            ["company_id", "customer_id"], ["customers.company_id", "customers.id"]
        ),
        ForeignKeyConstraint(
            ["company_id", "owner_id"], ["memberships.company_id", "memberships.id"]
        ),
        ForeignKeyConstraint(
            ["company_id", "department_id"],
            ["departments.company_id", "departments.id"],
        ),
        ForeignKeyConstraint(
            ["company_id", "department_id", "section_id"],
            ["sections.company_id", "sections.department_id", "sections.id"],
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    customer_id: Mapped[int] = mapped_column(Integer)
    owner_id: Mapped[int] = mapped_column(Integer)
    department_id: Mapped[int | None] = mapped_column(Integer)
    section_id: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(150))
    purpose: Mapped[str] = mapped_column(Text, default="")
    customer_contact: Mapped[str] = mapped_column(String(120), default="")
    customer_corporate_number: Mapped[str] = mapped_column(String(13), default="")
    status: Mapped[str] = mapped_column(String(25), default="consulting")
    due_on: Mapped[date | None] = mapped_column(Date)
    external_url: Mapped[str] = mapped_column(String(1000), default="")
    lock_version: Mapped[int] = mapped_column(default=1)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class ProjectAttachment(Base):
    __tablename__ = "project_attachments"
    __table_args__ = (
        UniqueConstraint("company_id", "project_id", "upload_id"),
        ForeignKeyConstraint(
            ["company_id", "project_id"], ["projects.company_id", "projects.id"]
        ),
        ForeignKeyConstraint(
            ["company_id", "uploaded_by_id"],
            ["memberships.company_id", "memberships.id"],
        ),
        CheckConstraint("size_bytes > 0", name="positive_size"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    upload_id: Mapped[str] = mapped_column(String(36))
    filename: Mapped[str] = mapped_column(String(200))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    content: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    uploaded_by_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class Requirement(Base):
    __tablename__ = "requirements"
    __table_args__ = (
        UniqueConstraint("company_id", "id"),
        ForeignKeyConstraint(
            ["company_id", "project_id"], ["projects.company_id", "projects.id"]
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    acceptance: Mapped[str] = mapped_column(Text, default="")
    questions: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    scope: Mapped[str] = mapped_column(String(20), default="undecided")
    status: Mapped[str] = mapped_column(String(20), default="consulting")
    agreement: Mapped[dict | None] = mapped_column(JSON)
    lock_version: Mapped[int] = mapped_column(default=1)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class RequirementHistory(Base):
    __tablename__ = "requirement_history"
    __table_args__ = (
        UniqueConstraint("company_id", "requirement_id", "version"),
        ForeignKeyConstraint(
            ["company_id", "requirement_id"],
            ["requirements.company_id", "requirements.id"],
        ),
        ForeignKeyConstraint(
            ["company_id", "actor_id"], ["memberships.company_id", "memberships.id"]
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    requirement_id: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)
    note: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "project_id"], ["projects.company_id", "projects.id"]
        ),
        UniqueConstraint("company_id", "id"),
        UniqueConstraint("company_id", "number"),
        ForeignKeyConstraint(
            ["company_id", "creator_id"], ["memberships.company_id", "memberships.id"]
        ),
        ForeignKeyConstraint(
            ["company_id", "owner_id"], ["memberships.company_id", "memberships.id"]
        ),
        ForeignKeyConstraint(
            ["company_id", "department_id"],
            ["departments.company_id", "departments.id"],
        ),
        ForeignKeyConstraint(
            ["company_id", "department_id", "section_id"],
            ["sections.company_id", "sections.department_id", "sections.id"],
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(Integer, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    number: Mapped[str | None] = mapped_column(String(40))
    creator_id: Mapped[int] = mapped_column(Integer)
    owner_id: Mapped[int] = mapped_column(Integer)
    department_id: Mapped[int | None] = mapped_column(Integer)
    section_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
    sales_status: Mapped[str] = mapped_column(
        String(20), default="open", server_default="open"
    )
    sales_version: Mapped[int] = mapped_column(default=1, server_default="1")
    sent_on: Mapped[date | None] = mapped_column(Date)


class Revision(Base):
    __tablename__ = "revisions"
    __table_args__ = (
        UniqueConstraint("company_id", "id"),
        UniqueConstraint("company_id", "quote_id", "version"),
        UniqueConstraint("company_id", "quote_id", "id"),
        ForeignKeyConstraint(
            ["company_id", "quote_id"], ["quotes.company_id", "quotes.id"]
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    quote_id: Mapped[int] = mapped_column(Integer, index=True)
    version: Mapped[int] = mapped_column(default=1)
    lock_version: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(25), default="draft")
    payload: Mapped[dict] = mapped_column(JSON)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(16, 0))
    tax: Mapped[Decimal] = mapped_column(Numeric(16, 0))
    total: Mapped[Decimal] = mapped_column(Numeric(16, 0))
    pdf: Mapped[bytes | None] = mapped_column(LargeBinary, deferred=True)
    issued_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    __table_args__ = (
        UniqueConstraint("company_id", "id"),
        ForeignKeyConstraint(
            ["company_id", "revision_id"], ["revisions.company_id", "revisions.id"]
        ),
        ForeignKeyConstraint(
            ["company_id", "requester_id"], ["memberships.company_id", "memberships.id"]
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    revision_id: Mapped[int] = mapped_column(Integer, index=True)
    requester_id: Mapped[int] = mapped_column(Integer)
    route_version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(25), default="pending")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class ApprovalStep(Base):
    __tablename__ = "approval_steps"
    __table_args__ = (
        UniqueConstraint("company_id", "request_id", "position"),
        ForeignKeyConstraint(
            ["company_id", "request_id"],
            ["approval_requests.company_id", "approval_requests.id"],
        ),
        ForeignKeyConstraint(
            ["company_id", "approver_id"], ["memberships.company_id", "memberships.id"]
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    request_id: Mapped[int] = mapped_column(Integer, index=True)
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))
    approver_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(25), default="waiting")
    comment: Mapped[str] = mapped_column(Text, default="")
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Audit(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "quote_id"], ["quotes.company_id", "quotes.id"]
        ),
        ForeignKeyConstraint(
            ["company_id", "actor_id"], ["memberships.company_id", "memberships.id"]
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    quote_id: Mapped[int | None] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(80))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class Seal(Base):
    __tablename__ = "seals"
    __table_args__ = (UniqueConstraint("company_id", "id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    image: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("company_id", "id"),
        UniqueConstraint("company_id", "quote_id"),
        ForeignKeyConstraint(
            ["company_id", "quote_id"], ["quotes.company_id", "quotes.id"]
        ),
        ForeignKeyConstraint(
            ["company_id", "quote_id", "revision_id"],
            ["revisions.company_id", "revisions.quote_id", "revisions.id"],
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    quote_id: Mapped[int] = mapped_column(Integer)
    revision_id: Mapped[int] = mapped_column(Integer)
    ordered_on: Mapped[date] = mapped_column(Date)
    delivery_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="received")
    note: Mapped[str] = mapped_column(Text, default="")
    lock_version: Mapped[int] = mapped_column(default=1)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("company_id", "id"),
        UniqueConstraint("company_id", "number"),
        ForeignKeyConstraint(
            ["company_id", "order_id"], ["orders.company_id", "orders.id"]
        ),
        Index(
            "uq_invoices_active_order",
            "company_id",
            "order_id",
            unique=True,
            sqlite_where=text("status <> 'void'"),
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    order_id: Mapped[int] = mapped_column(Integer)
    number: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    payload: Mapped[dict] = mapped_column(JSON)
    total: Mapped[Decimal] = mapped_column(Numeric(16, 0))
    issue_on: Mapped[date] = mapped_column(Date)
    transaction_on: Mapped[date] = mapped_column(Date)
    due_on: Mapped[date] = mapped_column(Date)
    paid_on: Mapped[date | None] = mapped_column(Date)
    payment_note: Mapped[str] = mapped_column(Text, default="")
    pdf: Mapped[bytes | None] = mapped_column(LargeBinary, deferred=True)
    lock_version: Mapped[int] = mapped_column(default=1)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
