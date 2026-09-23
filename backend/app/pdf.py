from io import BytesIO
from decimal import Decimal
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    Image,
)
from .db import ROOT


def generate_pdf(
    payload,
    number,
    version,
    issued_date=None,
    *,
    document_kind="quote",
    seal_image=None,
):
    invoice = document_kind == "invoice"
    label = "請求書" if invoice else "見積書"
    if "NotoJP" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            TTFont("NotoJP", str(ROOT / "backend/assets/NotoSansJP.ttf"))
        )
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=44,
        leftMargin=44,
        topMargin=46,
        bottomMargin=48,
        title=f"{label} {number or '下書き'}",
        author=payload["issuer"]["name"],
    )
    ink, green = colors.HexColor("#203c37"), colors.HexColor("#177363")
    style = ParagraphStyle(
        "body", fontName="NotoJP", fontSize=9, leading=16, textColor=ink, wordWrap="CJK"
    )
    small = ParagraphStyle("small", parent=style, fontSize=8, leading=13)

    def p(text, s=style):
        return Paragraph(escape(str(text)).replace("\n", "<br/>"), s)

    def money(v):
        value = Decimal(str(v))
        return f"{int(value):,}" if value == value.to_integral() else f"{value:,.2f}"

    title = ParagraphStyle("title", parent=style, fontSize=25, leading=35)
    meta = ParagraphStyle("meta", parent=small, alignment=TA_RIGHT)
    story = [
        Table(
            [
                [
                    p("御請求書" if invoice else "御見積書", title),
                    p(
                        (
                            f"{number or '下書き / PREVIEW'}\n請求日：{payload['issue_on']}\n支払期限：{payload['due_on']}"
                            if invoice
                            else f"{number or '下書き / PREVIEW'}  第{version}版\n発行日：{issued_date or '未発行'}\n有効期限：{payload['valid_until']}"
                        ),
                        meta,
                    ),
                ]
            ],
            colWidths=[235, 272],
        ),
        Spacer(1, 28),
    ]
    customer = payload["customer"]
    issuer = payload["issuer"]
    issuer_parts = [
        p(
            "\n".join(
                x
                for x in [
                    issuer["name"],
                    issuer.get("address", ""),
                    issuer.get("phone", ""),
                    payload.get("organization", ""),
                    f"担当：{payload.get('owner_name', '')}",
                ]
                if x
            )
        )
    ]
    if invoice and payload.get("registration_number"):
        issuer_parts.append(p(f"登録番号：{payload['registration_number']}", small))
    if seal_image:
        stamp = Image(BytesIO(seal_image))
        scale = min(44 / stamp.imageWidth, 44 / stamp.imageHeight)
        stamp.drawWidth, stamp.drawHeight = (
            stamp.imageWidth * scale,
            stamp.imageHeight * scale,
        )
        stamp.hAlign = "RIGHT"
        issuer_parts = [
            Table(
                [[issuer_parts, stamp]],
                colWidths=[151, 54],
                style=[
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ],
            )
        ]
    story += [
        Table(
            [
                [
                    p(
                        f"{customer['name']} 御中\n{customer.get('address', '')}\n{customer.get('contact', '')}"
                    ),
                    issuer_parts,
                ]
            ],
            colWidths=[290, 217],
            style=[("VALIGN", (0, 0), (-1, -1), "TOP")],
        ),
        Spacer(1, 24),
        p(f"件名：{payload['title']}"),
        p(
            "下記のとおり、ご請求申し上げます。"
            if invoice
            else "下記のとおり、お見積もり申し上げます。"
        ),
        Spacer(1, 16),
    ]
    totalstyle = ParagraphStyle(
        "total",
        parent=style,
        fontSize=20,
        leading=28,
        textColor=green,
        alignment=TA_RIGHT,
    )
    total = Table(
        [
            [
                p("ご請求金額（税込）" if invoice else "お見積金額（税込）"),
                p(f"¥ {money(payload['total'])}", totalstyle),
            ]
        ],
        colWidths=[220, 287],
    )
    total.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#edf5f1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 15),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
            ]
        )
    )
    story += [total, Spacer(1, 24)]
    rows = [
        [p(x, small) for x in ["品名・内容", "数量", "単位", "単価", "税率", "金額"]]
    ]
    for item in payload["items"]:
        rows.append(
            [
                p(
                    item["name"] + (" ※" if invoice and item["tax_rate"] == 8 else ""),
                    small,
                ),
                p(item["quantity"], small),
                p(item["unit"], small),
                p(money(item["unit_price"]), small),
                p(f"{item['tax_rate']}%", small),
                p(money(item["amount"]), small),
            ]
        )
    table = Table(
        rows, colWidths=[217, 45, 35, 75, 40, 95], repeatRows=1, hAlign="LEFT"
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7ede9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e3e8e4")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#fafbf9")],
                ),
            ]
        )
    )
    story += [table, Spacer(1, 18)]
    if invoice:
        if any(it["tax_rate"] == 8 for it in payload["items"]):
            story.append(p("※ 軽減税率対象", small))
        story += [p(f"取引年月日：{payload['transaction_on']}", small), Spacer(1, 8)]
    sums = [[p("小計"), p(f"¥ {money(payload['subtotal'])}", meta)]]
    for rate, amount in payload["taxes"].items():
        if invoice:
            base = sum(
                Decimal(it["amount"])
                for it in payload["items"]
                if str(it["tax_rate"]) == rate
            )
            sums.append([p(f"{rate}%対象（税抜）"), p(f"¥ {money(base)}", meta)])
        sums.append([p(f"消費税（{rate}%）"), p(f"¥ {money(amount)}", meta)])
    sums.append([p("合計（税込）"), p(f"¥ {money(payload['total'])}", meta)])
    story += [KeepTogether(Table(sums, colWidths=[370, 137])), Spacer(1, 22)]
    for label, key in [
        *(
            [("対象見積", "source_quote"), ("お振込先", "bank_details")]
            if invoice
            else [("納期・納入条件", "delivery"), ("お支払条件", "payment")]
        ),
        ("備考", "notes"),
    ]:
        if payload.get(key):
            story += [p(label), p(payload[key], small), Spacer(1, 10)]

    def footer(canvas, document):
        canvas.setFont("NotoJP", 8)
        canvas.setFillColor(colors.HexColor("#81908a"))
        canvas.drawString(44, 27, f"{number or '下書き'} / 第{version}版")
        canvas.drawRightString(A4[0] - 44, 27, f"{document.page}")

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
