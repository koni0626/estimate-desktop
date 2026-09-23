from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from urllib.parse import urlsplit


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Input):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class InitialSetup(Input):
    company_name: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=200)


class DesktopSetup(Input):
    company_name: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=100)


class CustomerInput(Input):
    name: str = Field(min_length=1, max_length=150)
    contact: str = Field(default="", max_length=120)
    address: str = Field(default="", max_length=300)
    email: str = Field(default="", max_length=200)


class ItemInput(Input):
    name: str = Field(min_length=1, max_length=400)
    quantity: Decimal = Field(gt=0, le=1000000, decimal_places=3)
    unit: str = Field(default="式", max_length=15)
    unit_price: Decimal = Field(ge=0, le=1000000000, decimal_places=2)
    tax_rate: Literal[0, 8, 10] = 10


class RequirementRef(Input):
    request_id: int = Field(gt=0)
    version: int = Field(gt=0)


class QuoteInput(Input):
    project_id: int | None = None
    request_refs: list[RequirementRef] = Field(default_factory=list, max_length=100)
    seal_id: int | None = None
    title: str = Field(min_length=1, max_length=150)
    customer_id: int
    valid_until: date
    delivery: str = Field(default="", max_length=300)
    payment: str = Field(default="納品月の翌月末払い", max_length=300)
    notes: str = Field(default="", max_length=3000)
    internal_note: str = Field(default="", max_length=3000)
    items: list[ItemInput] = Field(min_length=1, max_length=100)
    lock_version: int | None = None


class Action(Input):
    lock_version: int
    comment: str = Field(default="", max_length=1000)


class RouteStep(Input):
    name: str = Field(min_length=1, max_length=100)
    approver_id: int
    backup_id: int | None = None


class SettingsInput(Input):
    seal_default: bool = False
    registration_number: str = Field(default="", pattern=r"^(T[0-9]{13})?$")
    bank_details: str = Field(default="", max_length=500)
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(default="", max_length=300)
    phone: str = Field(default="", max_length=60)
    approval_mode: Literal["none", "sequential"]
    route: list[RouteStep] = Field(default_factory=list, max_length=10)
    route_version: int


class MemberInput(Input):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    role: Literal["member", "section_manager", "department_manager", "admin"] = "member"
    section_id: int | None = None


class OrganizationInput(Input):
    name: str = Field(min_length=1, max_length=100)
    department_id: int | None = None


class SealInput(Input):
    image_base64: str = Field(max_length=2800000)


class SalesInput(Input):
    sales_status: Literal["open", "sent", "lost"]
    sent_on: date | None = None
    lock_version: int


class OrderInput(Input):
    revision_id: int
    ordered_on: date
    delivery_on: date | None = None
    note: str = Field(default="", max_length=1000)


class OrderUpdate(Input):
    ordered_on: date
    delivery_on: date | None = None
    note: str = Field(default="", max_length=1000)
    status: Literal["received", "completed", "cancelled"]
    lock_version: int


class InvoiceInput(Input):
    issue_on: date
    transaction_on: date
    due_on: date
    bank_details: str = Field(default="", max_length=500)
    registration_number: str = Field(default="", pattern=r"^(T[0-9]{13})?$")
    notes: str = Field(default="", max_length=3000)
    lock_version: int | None = None


class PaymentInput(Input):
    lock_version: int
    paid_on: date
    note: str = Field(default="", max_length=1000)


class ProjectInput(Input):
    title: str = Field(min_length=1, max_length=150)
    customer_id: int
    customer_contact: str = Field(default="", max_length=120)
    customer_corporate_number: str = Field(default="", pattern=r"^([0-9]{13})?$")
    purpose: str = Field(default="", max_length=5000)
    status: Literal[
        "consulting",
        "estimating",
        "in_progress",
        "review",
        "completed",
        "on_hold",
        "cancelled",
    ] = "consulting"
    due_on: date | None = None
    external_url: str = Field(default="", max_length=1000)
    lock_version: int | None = None

    @field_validator("external_url")
    @classmethod
    def safe_url(cls, value):
        if value:
            parsed = urlsplit(value)
            if (
                parsed.scheme not in ("https", "http")
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                raise ValueError("外部リンクは http / https のURLを指定してください。")
        return value


class RequirementInput(Input):
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=5000)
    acceptance: str = Field(default="", max_length=3000)
    questions: str = Field(default="", max_length=3000)
    priority: Literal["high", "normal", "low"] = "normal"
    scope: Literal["undecided", "included", "excluded", "on_hold", "additional"] = (
        "undecided"
    )
    status: Literal[
        "consulting", "estimated", "agreed", "in_progress", "review", "done"
    ] = "consulting"
    change_note: str = Field(default="", max_length=1000)
    lock_version: int | None = None
