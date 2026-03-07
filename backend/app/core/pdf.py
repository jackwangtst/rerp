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
SEAL_PATH = os.path.join(os.path.dirname(__file__), "seal.png")

COUNTRY_ZH: dict[str, str] = {
    'Abu Dhabi': '阿布扎比', 'Afghanistan': '阿富汗', 'Albania': '阿尔巴尼亚',
    'Algeria': '阿尔及利亚', 'Am. Oceania': '美属大洋洲', 'American Virgin Islands': '美属维尔京群岛',
    'Andorra': '安道尔', 'Angola': '安哥拉', 'Antigua & Barbuda': '安提瓜和巴布达',
    'Argentina': '阿根廷', 'Armenia': '亚美尼亚', 'Aruba': '阿鲁巴',
    'Australia': '澳大利亚', 'Austria': '奥地利', 'Azerbaijan': '阿塞拜疆',
    'Azores': '亚速尔群岛', 'Bahamas': '巴哈马', 'Bahrain': '巴林',
    'Bangladesh': '孟加拉国', 'Barbados': '巴巴多斯', 'Belarus': '白俄罗斯',
    'Belgium': '比利时', 'Belize': '伯利兹', 'Benin': '贝宁',
    'Bermuda': '百慕大', 'Bhutan': '不丹', 'Bolivia': '玻利维亚',
    'Bosnia and Herzegovina': '波黑', 'Botswana': '博茨瓦纳', 'Brazil': '巴西',
    'British Virgin Islands': '英属维尔京群岛', 'Brunei Darussalam': '文莱',
    'Bulgaria': '保加利亚', 'Burkina Faso': '布基纳法索', 'Burundi': '布隆迪',
    'Cabo Verde': '佛得角', 'Cambodia': '柬埔寨', 'Cameroon': '喀麦隆',
    'Cayman Islands': '开曼群岛', 'Central African Republic': '中非', 'Chad': '乍得',
    'Chile': '智利', "China, People's Republic of": '中国', 'Colombia': '哥伦比亚',
    'Comoros': '科摩罗', 'Congo, Democratic Republic of': '刚果（金）',
    'Congo, Republic of': '刚果（布）', 'Cook Islands': '库克群岛',
    'Costa Rica': '哥斯达黎加', 'Croatia': '克罗地亚', 'Cuba': '古巴',
    'Cyprus': '塞浦路斯', 'Czech Republic': '捷克', "Côte d'Ivoire": '科特迪瓦',
    'Denmark': '丹麦', 'Djibouti': '吉布提', 'Dominica': '多米尼克',
    'Dominican Republic': '多明尼加', 'Dubai': '迪拜', 'East Timor': '东帝汶',
    'Ecuador': '厄瓜多尔', 'Egypt': '埃及', 'El Salvador': '萨尔瓦多',
    'Equatorial Guinea': '赤道几内亚', 'Eritrea': '厄立特里亚', 'Estonia': '爱沙尼亚',
    'Ethiopia': '埃塞俄比亚', 'Eurasian Customs Union': '欧亚关税同盟',
    'European Union': '欧盟', 'Falkland Islands': '福克兰群岛', 'Fiji': '斐济',
    'Finland': '芬兰', 'France': '法国', 'French Polynesia': '法属波利尼西亚',
    'Gabon': '加蓬', 'Gambia': '冈比亚', 'Georgia': '格鲁吉亚',
    'Germany': '德国', 'Germany (Import)': '德国（进口）', 'Ghana': '加纳',
    'Gibraltar': '直布罗陀', 'Greece': '希腊', 'Greenland': '格陵兰',
    'Grenada': '格林纳达', 'Guatemala': '危地马拉', 'Guinea': '几内亚',
    'Guinea-Bissau': '几内亚比绍', 'Guyana': '圭亚那', 'Haiti': '海地',
    'Honduras': '洪都拉斯', 'Hong Kong': '香港', 'Hungary': '匈牙利',
    'Iceland': '冰岛', 'India': '印度', 'Indonesia': '印度尼西亚',
    'Iran': '伊朗', 'Iraq': '伊拉克', 'Ireland': '爱尔兰',
    'Israel': '以色列', 'Italy': '意大利', 'Jamaica': '牙买加',
    'Japan': '日本', 'Jordan': '约旦', 'Kazakhstan': '哈萨克斯坦',
    'Kenya': '肯尼亚', 'Kiribati': '基里巴斯', 'Korea, Democratic Republic of': '朝鲜',
    'Korea, Republic of': '韩国', 'Kosovo': '科索沃', 'Kuwait': '科威特',
    'Kyrgyzstan': '吉尔吉斯斯坦', 'Laos': '老挝', 'Latvia': '拉脱维亚',
    'Lebanon': '黎巴嫩', 'Lesotho': '莱索托', 'Liberia': '利比里亚',
    'Libya': '利比亚', 'Lithuania': '立陶宛', 'Luxembourg': '卢森堡',
    'Macau': '澳门', 'Macedonia': '北马其顿', 'Madagascar': '马达加斯加',
    'Malawi': '马拉维', 'Malaysia': '马来西亚', 'Maldives': '马尔代夫',
    'Mali': '马里', 'Malta': '马耳他', 'Martinique': '马提尼克',
    'Mauritania': '毛里塔尼亚', 'Mauritius': '毛里求斯', 'Mexico': '墨西哥',
    'Micronesia': '密克罗尼西亚', 'Moldova': '摩尔多瓦', 'Monaco': '摩纳哥',
    'Mongolia': '蒙古', 'Montenegro': '黑山', 'Morocco': '摩洛哥',
    'Mozambique': '莫桑比克', 'Myanmar': '缅甸', 'Namibia': '纳米比亚',
    'Nepal': '尼泊尔', 'Netherlands': '荷兰', 'New Caledonia': '新喀里多尼亚',
    'New Zealand': '新西兰', 'Nicaragua': '尼加拉瓜', 'Niger': '尼日尔',
    'Nigeria': '尼日利亚', 'Norway': '挪威', 'Oman': '阿曼',
    'Pakistan': '巴基斯坦', 'Panama': '巴拿马', 'Papua New Guinea': '巴布亚新几内亚',
    'Paraguay': '巴拉圭', 'Peru': '秘鲁', 'Philippines': '菲律宾',
    'Poland': '波兰', 'Portugal': '葡萄牙', 'Puerto Rico': '波多黎各',
    'Qatar': '卡塔尔', 'Romania': '罗马尼亚', 'Russian Federation': '俄罗斯',
    'Rwanda': '卢旺达', 'Samoa': '萨摩亚', 'San Marino': '圣马力诺',
    'Saudi Arabia': '沙特阿拉伯', 'Senegal': '塞内加尔', 'Serbia': '塞尔维亚',
    'Seychelles': '塞舌尔', 'Sierra Leone': '塞拉利昂', 'Singapore': '新加坡',
    'Slovakia': '斯洛伐克', 'Slovenia': '斯洛文尼亚', 'Solomon Islands': '所罗门群岛',
    'Somalia': '索马里', 'South Africa, Republic of': '南非', 'Spain': '西班牙',
    'Sri Lanka': '斯里兰卡', 'Sudan': '苏丹', 'Suriname': '苏里南',
    'Swaziland': '斯威士兰', 'Sweden': '瑞典', 'Switzerland': '瑞士',
    'Syria': '叙利亚', 'Taiwan': '台湾', 'Tajikistan': '塔吉克斯坦',
    'Tanzania': '坦桑尼亚', 'Thailand': '泰国', 'Togo': '多哥',
    'Tonga': '汤加', 'Trinidad and Tobago': '特立尼达和多巴哥', 'Tunisia': '突尼斯',
    'Turkey': '土耳其', 'Turkmenistan': '土库曼斯坦', 'Tuvalu': '图瓦卢',
    'Uganda': '乌干达', 'Ukraine': '乌克兰', 'United Arab Emirates': '阿联酋',
    'United Kingdom': '英国', 'United States of America': '美国',
    'United States of America (CKD)': '美国（CKD）', 'Uruguay': '乌拉圭',
    'Uzbekistan': '乌兹别克斯坦', 'Vanuatu': '瓦努阿图', 'Venezuela': '委内瑞拉',
    'Vietnam': '越南', 'Yemen': '也门', 'Zambia': '赞比亚', 'Zimbabwe': '津巴布韦',
}


def _country_label(en: str) -> str:
    zh = COUNTRY_ZH.get(en)
    return f"{en}\n{zh}" if zh else en


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
    has_weeks   = any(i.get("weeks") for i in items)
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
    if has_weeks:
        headers.append("Lead time\n周期(周)");      col_w.append(W * 0.07)
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
            row.append(Paragraph(_country_label(item.get("country") or "-"), s_td_c))
        row.append(Paragraph(item.get("name", ""), s_td_l))
        if has_lr:
            row.append(Paragraph(item.get("lr_or_not") or "-", s_td_c))
        if has_weeks:
            row.append(Paragraph(str(item.get("weeks") or "-"), s_td_c))
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

    left_cell_content = [
        Paragraph(f"{COMPANY_ZH}", S("sc1", fontSize=9, alignment=TA_LEFT, leading=15, textColor=colors.HexColor("#1a3a6b"))),
        Paragraph(f"{COMPANY_ADDR}", S("sc2", fontSize=9, alignment=TA_LEFT, leading=15, textColor=colors.HexColor("#1a3a6b"))),
        Paragraph(f"<b>负责人签字&nbsp;&nbsp;&nbsp;&nbsp;公章</b>", S("sc3", fontSize=9, alignment=TA_LEFT, leading=15, textColor=colors.HexColor("#1a3a6b"))),
    ]
    seal_path = os.path.normpath(SEAL_PATH)
    if os.path.exists(seal_path):
        seal_img = Image(seal_path, width=28*mm, height=28*mm)
        seal_img.hAlign = "LEFT"
        left_cell_content.append(seal_img)

    right_lines = [
        "<b>客户信息</b>",
        customer_name or "",
    ]
    if deliver_to_address:
        right_lines.append(deliver_to_address)
    right_lines.append("<b>授权人签字&nbsp;&nbsp;&nbsp;&nbsp;公司公章</b>")

    sign_data = [
        [left_cell_content,
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
