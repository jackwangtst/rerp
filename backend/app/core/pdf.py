"""
报价单 PDF 生成模块 - 对齐任域通认证报价单模板
"""
from __future__ import annotations
import io
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os

_FONT_REGISTERED = False

def _ensure_font():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    candidates = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ]
    project_font = os.path.join(os.path.dirname(__file__), "simhei.ttf")
    if os.path.exists(project_font):
        candidates.insert(0, project_font)
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("SimHei", path))
                _FONT_REGISTERED = True
                return
            except Exception:
                continue
    _FONT_REGISTERED = True


def _fn():
    _ensure_font()
    return "SimHei" if "SimHei" in pdfmetrics.getRegisteredFontNames() else "Helvetica"


# 公司固定信息
COMPANY_ZH = "任域通认证服务（深圳）有限公司"
COMPANY_EN = "AnyRegion Certification Service (Shenzhen) Co., Ltd."
COMPANY_ADDR = "深圳市龙华区民治街道新牛社区金地梅陇镇 6栋5B"
COMPANY_TEL = "021-XXXXXXXX"
BANK_NAME = "中国银行深圳锦绣支行"
BANK_ACCOUNT = "760174824677"
BANK_HOLDER = "任域通认证服务（深圳）有限公司"


LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "logo.png")


def generate_quotation_pdf(
    *,
    quote_no: str,
    created_at: date,
    valid_until: date,
    customer_name: str,
    contact_name: str | None,
    contact_phone: str | None,
    deliver_to_address: str | None,
    product_name: str | None,
    product_model: str | None,
    sales_person: str,
    items: list[dict],
    total_amount: Decimal,
    discount_amount: Decimal | None,
    payment_terms: str | None,
    remark: str | None,
) -> bytes:
    _ensure_font()
    fn = _fn()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    W = A4[0] - 36 * mm

    def S(name, **kw):
        return ParagraphStyle(name, fontName=fn, **kw)

    # 样式
    s_title    = S("title",   fontSize=18, alignment=TA_CENTER, leading=28, spaceAfter=2, textColor=colors.HexColor("#1a3a6b"))
    s_co_en    = S("co_en",   fontSize=8,  alignment=TA_CENTER, leading=12, textColor=colors.grey)
    s_co_zh    = S("co_zh",   fontSize=10, alignment=TA_CENTER, leading=16, textColor=colors.HexColor("#1a3a6b"))
    s_label    = S("label",   fontSize=9,  leading=14)
    s_bold     = S("bold",    fontSize=9,  leading=14)
    s_th       = S("th",      fontSize=9,  alignment=TA_CENTER, textColor=colors.white, leading=13)
    s_td_c     = S("tdc",     fontSize=8.5, alignment=TA_CENTER, leading=12)
    s_td_r     = S("tdr",     fontSize=8.5, alignment=TA_RIGHT,  leading=12)
    s_td_l     = S("tdl",     fontSize=8.5, alignment=TA_LEFT,   leading=12)
    s_note     = S("note",    fontSize=8,  leading=13, textColor=colors.HexColor("#444444"))
    s_footer   = S("footer",  fontSize=7.5, leading=12, textColor=colors.grey)

    story = []

    # ── 页眉：Logo + 公司名称 ──────────────────────────────────
    logo_path = os.path.normpath(LOGO_PATH)
    if os.path.exists(logo_path):
        logo = Image(logo_path, height=14*mm, width=40*mm)
        logo.hAlign = "LEFT"
        header_data = [[
            logo,
            [Paragraph(COMPANY_EN, s_co_en), Spacer(1, 1*mm), Paragraph(COMPANY_ZH, s_co_zh)],
        ]]
        header_table = Table(header_data, colWidths=[16*mm, W - 16*mm])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 4),
        ]))
        story.append(header_table)
    else:
        story.append(Paragraph(COMPANY_EN, s_co_en))
        story.append(Paragraph(COMPANY_ZH, s_co_zh))
    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3a6b")))
    story.append(Spacer(1, 1*mm))

    # 标题
    story.append(Paragraph("任域通认证报价", s_title))
    story.append(Spacer(1, 1*mm))

    # 报价单号行
    no_data = [[
        Paragraph(f"No. {quote_no}", S("qno", fontSize=9, leading=14)),
        Paragraph(f"DATE: {created_at}  &nbsp;&nbsp; VALID UNTIL: {valid_until}", S("date", fontSize=9, alignment=TA_RIGHT, leading=14)),
    ]]
    no_table = Table(no_data, colWidths=[W*0.5, W*0.5])
    no_table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    story.append(no_table)
    story.append(Spacer(1, 3*mm))

    # ── DELIVER TO ────────────────────────────────────────────
    deliver_lines = [
        "<b>DELIVER TO:</b>",
        f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{customer_name}",
    ]
    if deliver_to_address:
        deliver_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{deliver_to_address}")
    if contact_name:
        deliver_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;联系人: {contact_name}{'  Tel: ' + contact_phone if contact_phone else ''}")
    deliver_box = [[Paragraph("<br/>".join(deliver_lines), S("deliver", fontSize=9, leading=15))]]
    dt = Table(deliver_box, colWidths=[W])
    dt.setStyle(TableStyle([
        ("BOX", (0,0),(0,0), 0.5, colors.HexColor("#aaaaaa")),
        ("TOPPADDING",(0,0),(0,0),5),("BOTTOMPADDING",(0,0),(0,0),5),
        ("LEFTPADDING",(0,0),(0,0),8),("RIGHTPADDING",(0,0),(0,0),8),
    ]))
    story.append(dt)
    story.append(Spacer(1, 4*mm))

    # ── 产品信息 ──────────────────────────────────────────────
    if product_name or product_model:
        prod_parts = []
        if product_name:
            prod_parts.append(f"<b>产品名称：</b>{product_name}")
        if product_model:
            prod_parts.append(f"<b>产品型号：</b>{product_model}")
        prod_box = [[Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;".join(prod_parts), S("prod", fontSize=9, leading=15))]]
        pt = Table(prod_box, colWidths=[W])
        pt.setStyle(TableStyle([
            ("BOX",           (0,0),(0,0), 0.5, colors.HexColor("#aaaaaa")),
            ("BACKGROUND",    (0,0),(0,0), colors.HexColor("#f5f7fa")),
            ("TOPPADDING",    (0,0),(0,0), 5),
            ("BOTTOMPADDING", (0,0),(0,0), 5),
            ("LEFTPADDING",   (0,0),(0,0), 8),
            ("RIGHTPADDING",  (0,0),(0,0), 8),
        ]))
        story.append(pt)
        story.append(Spacer(1, 4*mm))

    # ── 明细表 ────────────────────────────────────────────────
    # 固定8列：No / Country / Certification / LR or not / Lead time / Local testing / Serie models / Price
    # 各列按数据是否存在动态显示（Country/LR/Lead time/Local testing/Serie models）
    has_country = any(i.get("country") for i in items)
    has_lr      = any(i.get("lr_or_not") is not None for i in items)
    has_months  = any(i.get("months") for i in items)
    has_local   = any(i.get("local_testing") is not None for i in items)
    has_models  = any(i.get("models") for i in items)
    has_remark  = any(i.get("item_remark") for i in items)

    headers = ["No"]
    col_w   = [W * 0.04]
    if has_country:
        headers.append("Country\n国家");           col_w.append(W * 0.09)
    headers.append("Certification\n认证项目");     col_w.append(W * 0.22)
    if has_lr:
        headers.append("LR or not\n当地代表");     col_w.append(W * 0.08)
    if has_months:
        headers.append("Lead time\n周期");         col_w.append(W * 0.07)
    if has_local:
        headers.append("Local testing\n本地测试");   col_w.append(W * 0.08)
    if has_models:
        headers.append("Serie models/cert\nor one model/cert"); col_w.append(W * 0.14)
    col_w.append(W * 0.12)
    headers.append("Price(RMB)")
    if has_remark:
        headers.append("Remark\n备注");            col_w.append(W * 0.16)

    table_data = [[Paragraph(h, s_th) for h in headers]]

    for idx, item in enumerate(items, 1):
        row = [Paragraph(str(idx), s_td_c)]
        if has_country:
            row.append(Paragraph(item.get("country") or "-", s_td_c))
        row.append(Paragraph(item.get("name", ""), s_td_l))
        if has_lr:
            row.append(Paragraph(item.get("lr_or_not") or "-", s_td_c))
        if has_months:
            row.append(Paragraph(str(item.get("months") or "-"), s_td_c))
        if has_local:
            row.append(Paragraph(item.get("local_testing") or "-", s_td_c))
        if has_models:
            row.append(Paragraph(item.get("models") or "-", s_td_l))
        row.append(Paragraph(f"{float(item.get('amount', 0)):,.0f}", s_td_r))
        if has_remark:
            row.append(Paragraph(item.get("item_remark") or "", s_td_l))
        table_data.append(row)

    # 合计行：合并到 Price 列前，Price 列显示金额，备注列（若有）留空
    price_col_idx = headers.index("Price(RMB)")
    span_to = price_col_idx - 1
    total_row = (
        [Paragraph("合计 Total", s_td_c)] +
        [""] * span_to +
        [Paragraph(f"RMB {float(total_amount):,.0f}", s_td_r)] +
        ([""] if has_remark else [])
    )
    table_data.append(total_row)

    # 优惠后行
    if discount_amount and float(discount_amount) > 0:
        final = float(total_amount) - float(discount_amount)
        disc_row = (
            [Paragraph(f"已优惠 -{float(discount_amount):,.0f}", s_td_c)] +
            [""] * span_to +
            [Paragraph(f"RMB {final:,.0f}", S("fin", fontSize=9, alignment=TA_RIGHT, textColor=colors.HexColor("#c0392b"), leading=12))] +
            ([""] if has_remark else [])
        )
        table_data.append(disc_row)

    detail_table = Table(table_data, colWidths=col_w, repeatRows=1)
    last = len(table_data) - 1
    pre_last = last - 1 if (discount_amount and float(discount_amount or 0) > 0) else last

    ts = TableStyle([
        # 表头
        ("BACKGROUND",   (0,0), (-1,0),   colors.HexColor("#1a3a6b")),
        ("TOPPADDING",   (0,0), (-1,0),   5),
        ("BOTTOMPADDING",(0,0), (-1,0),   5),
        ("ALIGN",        (0,0), (-1,0),   "CENTER"),
        # 数据行
        ("FONTNAME",     (0,1), (-1,-1),  fn),
        ("FONTSIZE",     (0,1), (-1,-1),  8.5),
        ("TOPPADDING",   (0,1), (-1,-1),  4),
        ("BOTTOMPADDING",(0,1), (-1,-1),  4),
        ("ROWBACKGROUNDS",(0,1),(-1, pre_last-1), [colors.white, colors.HexColor("#f0f4fa")]),
        # 合计行
        ("BACKGROUND",   (0, pre_last), (-1, pre_last), colors.HexColor("#dde5f5")),
        ("SPAN",         (0, pre_last), (span_to, pre_last)),
        ("ALIGN",        (0, pre_last), (span_to, pre_last), "CENTER"),
        # 网格
        ("GRID",         (0,0), (-1,-1),  0.5, colors.HexColor("#c0c8d8")),
        ("VALIGN",       (0,0), (-1,-1),  "MIDDLE"),
    ])
    if discount_amount and float(discount_amount or 0) > 0:
        ts.add("BACKGROUND", (0, last), (-1, last), colors.HexColor("#fef0ee"))
        ts.add("SPAN",       (0, last), (span_to, last))
        ts.add("ALIGN",      (0, last), (span_to, last), "CENTER")

    detail_table.setStyle(ts)
    story.append(detail_table)
    story.append(Spacer(1, 4*mm))

    # ── 含税说明 ──────────────────────────────────────────────
    tax_note = "（含税1%）" if not (discount_amount and float(discount_amount) > 0) else \
               f"（含税1%，已优惠 RMB {float(discount_amount):,.0f}）"
    story.append(Paragraph(f"<b>合计金额：RMB {float(total_amount):,.0f} {tax_note}</b>",
                           S("tax", fontSize=9, leading=14)))
    story.append(Spacer(1, 3*mm))

    # ── 注意事项 ──────────────────────────────────────────────
    story.append(Paragraph("<b>Remark 注意事项：</b>", S("remark_title", fontSize=9, leading=16)))
    remark_items = []
    if remark:
        remark_items.append(remark)
    default_remarks = [
        "1. 认证报价一个月内有效，含税 1%。以上报价包含当地代表费用，除了需要实际进口商的要客户提供，不包含发证官方随机要求的抽样测试费。",
        "2. 认证周期从收到客户样品和完整资料后开始计算。",
        "3. 一旦客户确定开案后，由于客户原因要求变更或取消，可能会产生的费用由客户承担，费用以实际发生的为准。",
        "4. 项目完成之后一个月内客户需付款 100%。",
        "5. 收款账号信息：",
    ]
    if payment_terms:
        remark_items.append(f"付款条款：{payment_terms}")
    remark_items.extend(default_remarks)

    for item in remark_items:
        story.append(Paragraph(item, s_note))
    story.append(Spacer(1, 3*mm))

    # ── 付款信息 ──────────────────────────────────────────────
    pay_data = [
        [Paragraph("开户行：", s_label), Paragraph(BANK_NAME, s_label),
         Paragraph("账&nbsp;&nbsp;号：", s_label), Paragraph(BANK_ACCOUNT, s_label)],
        [Paragraph("户&nbsp;&nbsp;名：", s_label), Paragraph(BANK_HOLDER, s_label), "", ""],
    ]
    pay_table = Table(pay_data, colWidths=[W*0.12, W*0.38, W*0.12, W*0.38])
    pay_table.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1), fn),
        ("FONTSIZE",(0,0),(-1,-1), 8.5),
        ("TOPPADDING",(0,0),(-1,-1),2),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("SPAN",(1,1),(3,1)),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(pay_table)
    story.append(Spacer(1, 6*mm))

    # ── 落款 ──────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 3*mm))

    left_lines = [
        f"<b>负责人签字&nbsp;&nbsp;&nbsp;&nbsp;公章</b>",
        f"{COMPANY_ZH}",
        f"业务员：{sales_person}",
    ]
    right_lines = [
        "<b>授权人签字&nbsp;&nbsp;&nbsp;&nbsp;公司公章</b>",
        customer_name or "",
    ]
    if deliver_to_address:
        right_lines.append(deliver_to_address)

    sign_data = [
        [Paragraph("<br/>".join(left_lines),  S("sc", fontSize=9, alignment=TA_LEFT,  leading=15, textColor=colors.HexColor("#1a3a6b"))),
         Paragraph("<br/>".join(right_lines), S("cc", fontSize=9, alignment=TA_RIGHT, leading=15))],
    ]
    sign_table = Table(sign_data, colWidths=[W*0.5, W*0.5])
    sign_table.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(sign_table)
    story.append(Spacer(1, 12*mm))
    story.append(Paragraph("签字：___________________", s_footer))

    doc.build(story)
    return buf.getvalue()
