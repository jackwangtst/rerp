"""
生成系统使用手册 PDF
运行: python3 docs/gen_manual.py
输出: docs/使用手册.pdf
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

# ── 字体 ──────────────────────────────────────────────────────────
def _ensure_font():
    candidates = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    project_font = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "core", "simhei.ttf")
    if os.path.exists(project_font):
        candidates.insert(0, project_font)
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("SimHei", path))
                return "SimHei"
            except Exception:
                continue
    return "Helvetica"

fn = _ensure_font()

# ── 颜色 ──────────────────────────────────────────────────────────
C_BLUE   = colors.HexColor("#1a3a6b")
C_LIGHT  = colors.HexColor("#e8eef8")
C_GREY   = colors.HexColor("#888888")
C_WHITE  = colors.white
C_BG     = colors.HexColor("#f5f7fa")

# ── 样式 ──────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, fontName=fn, **kw)

s_cover_title  = S("ct",  fontSize=28, alignment=TA_CENTER, leading=40, textColor=C_WHITE, spaceAfter=6)
s_cover_sub    = S("cs",  fontSize=13, alignment=TA_CENTER, leading=20, textColor=colors.HexColor("#c8d8f0"))
s_cover_co     = S("cc2", fontSize=11, alignment=TA_CENTER, leading=18, textColor=C_WHITE)
s_h1           = S("h1",  fontSize=16, leading=24, textColor=C_BLUE, spaceBefore=8, spaceAfter=4)
s_h2           = S("h2",  fontSize=12, leading=18, textColor=C_BLUE, spaceBefore=6, spaceAfter=3)
s_h3           = S("h3",  fontSize=10, leading=16, textColor=colors.HexColor("#333333"), spaceBefore=4, spaceAfter=2)
s_body         = S("bd",  fontSize=9,  leading=16, textColor=colors.HexColor("#333333"), spaceAfter=2)
s_note         = S("nt",  fontSize=8.5,leading=14, textColor=C_GREY,  spaceAfter=2)
s_th           = S("th",  fontSize=9,  alignment=TA_CENTER, textColor=C_WHITE, leading=13)
s_td           = S("td",  fontSize=8.5,leading=13)
s_td_c         = S("tdc", fontSize=8.5,alignment=TA_CENTER, leading=13)
s_flow         = S("fl",  fontSize=9,  alignment=TA_CENTER, leading=16, textColor=C_BLUE)
s_toc          = S("toc", fontSize=10, leading=18, textColor=C_BLUE)

W = A4[0] - 36 * mm

# ── 辅助函数 ──────────────────────────────────────────────────────
def table(data, col_widths, header=True):
    t = Table(data, colWidths=col_widths)
    styles = [
        ("FONTNAME",     (0,0), (-1,-1), fn),
        ("FONTSIZE",     (0,0), (-1,-1), 8.5),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#c0c8d8")),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
    ]
    if header:
        styles += [
            ("BACKGROUND",   (0,0), (-1,0), C_BLUE),
            ("TEXTCOLOR",    (0,0), (-1,0), C_WHITE),
            ("ALIGN",        (0,0), (-1,0), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_BG]),
        ]
    t.setStyle(TableStyle(styles))
    return t

def section_title(story, num, title):
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_BLUE))
    story.append(Spacer(1, 1*mm))
    story.append(Paragraph(f"{num}. {title}", s_h1))
    story.append(Spacer(1, 2*mm))

def sub_title(story, title):
    story.append(Paragraph(f"▌ {title}", s_h2))

def body(story, text):
    story.append(Paragraph(text, s_body))

def note(story, text):
    story.append(Paragraph(f"　{text}", s_note))

def spacer(story, h=3):
    story.append(Spacer(1, h*mm))

# ── 封面 ──────────────────────────────────────────────────────────
def build_cover(story):
    cover_bg = Table(
        [[
            Paragraph("任域通认证 ERP", s_cover_title),
            Paragraph("系统使用手册", s_cover_title),
            Paragraph(" ", s_cover_sub),
            Paragraph("AnyRegion Certification Service ERP", s_cover_sub),
            Paragraph(" ", s_cover_sub),
            Paragraph("任域通认证服务（深圳）有限公司", s_cover_co),
            Paragraph("2026 年 3 月", s_cover_co),
        ]],
        colWidths=[W]
    )
    cover_bg.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), C_BLUE),
        ("TOPPADDING",    (0,0), (-1,-1), 30*mm),
        ("BOTTOMPADDING", (0,0), (-1,-1), 30*mm),
        ("LEFTPADDING",   (0,0), (-1,-1), 10*mm),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10*mm),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(cover_bg)
    story.append(PageBreak())

# ── 目录 ──────────────────────────────────────────────────────────
def build_toc(story):
    story.append(Paragraph("目　录", S("toc_h", fontSize=18, alignment=TA_CENTER, leading=30, textColor=C_BLUE)))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BLUE))
    spacer(story, 4)
    items = [
        ("1.", "系统概述"),
        ("2.", "登录与权限"),
        ("3.", "工作台"),
        ("4.", "市场需求"),
        ("　4.1", "线索管理"),
        ("　4.2", "商机管理"),
        ("5.", "客户管理"),
        ("6.", "合同 / 付款"),
        ("　6.1", "报价管理"),
        ("　6.2", "收款管理"),
        ("7.", "财务管理 — 支出"),
        ("8.", "任务管理"),
        ("　8.1", "认证项目"),
        ("　8.2", "审核任务"),
        ("9.", "系统管理"),
        ("　9.1", "用户管理"),
        ("　9.2", "价格库"),
        ("10.", "业务流程总览"),
    ]
    for no, title in items:
        t = Table([[Paragraph(no, s_toc), Paragraph(title, s_toc)]], colWidths=[W*0.12, W*0.88])
        t.setStyle(TableStyle([
            ("TOPPADDING",    (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("FONTNAME",      (0,0), (-1,-1), fn),
        ]))
        story.append(t)
    story.append(PageBreak())

# ── 正文 ──────────────────────────────────────────────────────────
def build_body(story):

    # ── 1. 系统概述 ───────────────────────────────────────────────
    section_title(story, 1, "系统概述")
    body(story, "本系统是专为认证服务业务设计的 ERP 管理平台，覆盖从<b>销售线索获取</b>到<b>认证项目完成</b>的完整业务流程：")
    spacer(story, 2)
    t = table([
        [Paragraph("模块", s_th), Paragraph("功能范围", s_th)],
        [Paragraph("市场需求", s_td), Paragraph("线索录入、跟进记录、商机管理、销售漏斗", s_td)],
        [Paragraph("客户管理", s_td), Paragraph("客户档案、联系人、跟进历史", s_td)],
        [Paragraph("合同/付款", s_td), Paragraph("报价单生成、PDF 导出、收款状态追踪", s_td)],
        [Paragraph("财务管理", s_td), Paragraph("支出记录、利润统计", s_td)],
        [Paragraph("任务管理", s_td), Paragraph("认证项目进度、审核任务分配", s_td)],
        [Paragraph("系统管理", s_td), Paragraph("用户账号管理、认证价格库维护", s_td)],
    ], [W*0.25, W*0.75])
    story.append(t)

    # ── 2. 登录与权限 ─────────────────────────────────────────────
    section_title(story, 2, "登录与权限")
    body(story, "访问系统网址，输入用户名和密码登录。系统分两种角色：")
    spacer(story, 2)
    t = table([
        [Paragraph("角色", s_th), Paragraph("权限范围", s_th)],
        [Paragraph("管理员 (ROLE_ADMIN)", s_td), Paragraph("全部功能，含工作台、用户管理、系统设置", s_td)],
        [Paragraph("普通用户 (ROLE_USER)", s_td), Paragraph("业务功能（线索/商机/客户/报价/财务/任务），不含工作台和系统管理", s_td)],
    ], [W*0.35, W*0.65])
    story.append(t)

    # ── 3. 工作台 ─────────────────────────────────────────────────
    section_title(story, 3, "工作台")
    body(story, "仅管理员可见。展示以下 KPI 统计卡片：")
    spacer(story, 2)
    t = table([
        [Paragraph("指标", s_th), Paragraph("说明", s_th)],
        [Paragraph("本月新增线索", s_td),   Paragraph("当月创建的线索数量", s_td)],
        [Paragraph("在服务客户数", s_td),   Paragraph("状态为服务中的客户总数", s_td)],
        [Paragraph("本月新签合同", s_td),   Paragraph("当月状态变为已接受的报价单数量", s_td)],
        [Paragraph("待执行任务",  s_td),   Paragraph("状态为待开始或进行中的任务数", s_td)],
        [Paragraph("未收款金额",  s_td),   Paragraph("所有未完成收款的待收余额总和", s_td)],
    ], [W*0.30, W*0.70])
    story.append(t)

    # ── 4. 市场需求 ───────────────────────────────────────────────
    section_title(story, 4, "市场需求")

    sub_title(story, "4.1  线索管理")
    body(story, "记录和管理潜在客户信息，跟踪销售进展。")
    spacer(story, 2)
    t = table([
        [Paragraph("字段", s_th), Paragraph("说明", s_th)],
        [Paragraph("公司名称 / 联系人 / 电话 / 邮箱", s_td), Paragraph("基本联系信息", s_td)],
        [Paragraph("来源", s_td), Paragraph("网络 / 转介绍 / 展会 / 其他", s_td)],
        [Paragraph("状态", s_td), Paragraph("新建 → 跟进中 → 已转化 → 已失效", s_td)],
        [Paragraph("意向认证 / 下次跟进日期", s_td), Paragraph("跟进依据", s_td)],
    ], [W*0.40, W*0.60])
    story.append(t)
    spacer(story, 2)
    body(story, "<b>操作步骤：</b>")
    note(story, "1. 点击「新增线索」填写基本信息")
    note(story, "2. 在线索详情中点击「添加跟进」记录每次沟通内容")
    note(story, "3. 线索成熟后可关联客户或直接创建商机")
    spacer(story, 3)

    sub_title(story, "4.2  商机管理")
    body(story, "管理已进入销售阶段的潜在合作机会。")
    spacer(story, 2)
    t = table([
        [Paragraph("字段", s_th), Paragraph("说明", s_th)],
        [Paragraph("商机名称 / 认证类型", s_td), Paragraph("商机基本信息", s_td)],
        [Paragraph("销售阶段", s_td), Paragraph("初步接触 → 需求确认 → 报价 → 谈判 → 赢单 / 输单", s_td)],
        [Paragraph("预估金额 / 赢单率", s_td), Paragraph("销售预测依据", s_td)],
        [Paragraph("预计关闭日期", s_td), Paragraph("计划签单日期", s_td)],
    ], [W*0.35, W*0.65])
    story.append(t)
    spacer(story, 2)
    body(story, "<b>操作步骤：</b>")
    note(story, "1. 点击「新增商机」，可关联已有线索或客户")
    note(story, "2. 随销售进展更新「销售阶段」")
    note(story, "3. 赢单后在报价管理中创建正式报价单")

    # ── 5. 客户管理 ───────────────────────────────────────────────
    section_title(story, 5, "客户管理")
    body(story, "维护正式客户的完整档案信息。")
    spacer(story, 2)
    t = table([
        [Paragraph("字段", s_th), Paragraph("说明", s_th)],
        [Paragraph("公司名称 / 简称", s_td), Paragraph("客户标识", s_td)],
        [Paragraph("客户等级", s_td), Paragraph("A / B / C", s_td)],
        [Paragraph("状态", s_td), Paragraph("潜在 / 服务中 / 已到期 / 已流失", s_td)],
        [Paragraph("联系人", s_td), Paragraph("支持多个联系人，可设主联系人", s_td)],
        [Paragraph("统一社信代码 / 法人代表", s_td), Paragraph("企业工商信息", s_td)],
    ], [W*0.35, W*0.65])
    story.append(t)
    spacer(story, 2)
    body(story, "<b>操作步骤：</b>")
    note(story, "1. 点击「新增客户」填写公司信息")
    note(story, "2. 在客户详情中管理「联系人」列表")
    note(story, "3. 可添加跟进记录维护客情关系")

    # ── 6. 合同/付款 ──────────────────────────────────────────────
    section_title(story, 6, "合同 / 付款")

    sub_title(story, "6.1  报价管理")
    body(story, "创建认证报价单，支持 PDF 导出。报价单状态变为「已接受」即视为合同生效，系统自动创建收款记录。")
    spacer(story, 2)
    body(story, "<b>状态流转：</b>")
    flow = Table([[
        Paragraph("草稿", s_flow), Paragraph("→", s_flow),
        Paragraph("待审批", s_flow), Paragraph("→", s_flow),
        Paragraph("已发送", s_flow), Paragraph("→", s_flow),
        Paragraph("已接受", s_flow),
    ]], colWidths=[W/7]*7)
    flow.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,0),   colors.HexColor("#e8eef8")),
        ("BACKGROUND",    (6,0), (6,0),   colors.HexColor("#d4edda")),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("FONTNAME",      (0,0), (-1,-1), fn),
    ]))
    story.append(flow)
    spacer(story, 3)
    body(story, "<b>报价明细行字段：</b>")
    spacer(story, 1)
    t = table([
        [Paragraph("字段", s_th), Paragraph("说明", s_th)],
        [Paragraph("国家", s_td), Paragraph("认证目标国家，中英文双语显示", s_td)],
        [Paragraph("认证项目", s_td), Paragraph("认证标准名称", s_td)],
        [Paragraph("当地代表 (LR)", s_td), Paragraph("是否需要当地代表", s_td)],
        [Paragraph("周期 (Lead time)", s_td), Paragraph("认证预计周期（周）", s_td)],
        [Paragraph("本地测试", s_td), Paragraph("是否需要本地测试", s_td)],
        [Paragraph("型号 / 证书", s_td), Paragraph("系列申请或单型号", s_td)],
        [Paragraph("单价 / 金额", s_td), Paragraph("参考价格库自动填充，自动计算合计", s_td)],
    ], [W*0.30, W*0.70])
    story.append(t)
    spacer(story, 2)
    body(story, "<b>操作步骤：</b>")
    note(story, "1. 点击「新增报价」，选择关联客户或商机")
    note(story, "2. 填写产品名称、型号")
    note(story, "3. 点击「添加明细」录入认证项目，可从价格库搜索自动填充参考价")
    note(story, "4. 填写付款条款、备注后保存")
    note(story, "5. 点击「导出 PDF」生成正式报价单文件")
    note(story, "6. 客户确认后将状态改为已接受，系统自动创建收款记录")
    spacer(story, 3)

    sub_title(story, "6.2  收款管理")
    body(story, "追踪所有已接受报价单的收款进度。")
    spacer(story, 2)
    t = table([
        [Paragraph("状态", s_th), Paragraph("说明", s_th)],
        [Paragraph("待收款", s_td), Paragraph("尚未收到任何款项", s_td)],
        [Paragraph("部分收款", s_td), Paragraph("已收金额 > 0 但未达到合同总额", s_td)],
        [Paragraph("已收款", s_td), Paragraph("已收金额 = 合同总额，自动更新", s_td)],
    ], [W*0.25, W*0.75])
    story.append(t)
    spacer(story, 2)
    body(story, "<b>操作步骤：</b>")
    note(story, "1. 找到对应报价单记录，点击「登记收款」")
    note(story, "2. 填写已收金额、收款日期、付款方式（对公转账 / 现金 / 支票 / 其他）、备注")
    note(story, "3. 系统自动更新收款状态")
    note(story, "4. 如需删除收款记录，点击「删除」并确认")

    # ── 7. 财务管理 ───────────────────────────────────────────────
    section_title(story, 7, "财务管理 — 支出")
    body(story, "记录项目相关支出，统计利润。支出类型：认证费 / 差旅 / 代理费 / 测试费 / 其他。")
    spacer(story, 2)
    body(story, "<b>统计面板：</b>")
    t = table([
        [Paragraph("指标", s_th), Paragraph("说明", s_th)],
        [Paragraph("总支出", s_td), Paragraph("筛选期间内所有支出合计", s_td)],
        [Paragraph("总回款", s_td), Paragraph("同期已收款金额合计", s_td)],
        [Paragraph("利润", s_td), Paragraph("总回款 − 总支出", s_td)],
        [Paragraph("利润率", s_td), Paragraph("利润 ÷ 总回款 × 100%", s_td)],
    ], [W*0.25, W*0.75])
    story.append(t)
    spacer(story, 2)
    body(story, "<b>操作步骤：</b>")
    note(story, "1. 点击「新增支出」")
    note(story, "2. 选择支出类型、填写金额、付款日期、供应商名称")
    note(story, "3. 可关联对应的「客户」和「报价单」，便于按项目统计成本")
    note(story, "4. 支持按支出类型和日期范围筛选查询")

    # ── 8. 任务管理 ───────────────────────────────────────────────
    section_title(story, 8, "任务管理")

    sub_title(story, "8.1  认证项目")
    body(story, "管理每个认证项目的整体进度。")
    spacer(story, 2)
    t = table([
        [Paragraph("字段", s_th), Paragraph("说明", s_th)],
        [Paragraph("关联客户", s_td), Paragraph("所属客户", s_td)],
        [Paragraph("认证标准 / 范围", s_td), Paragraph("项目认证内容", s_td)],
        [Paragraph("审核阶段", s_td), Paragraph("初审 / 监督审核 / 再认证", s_td)],
        [Paragraph("状态", s_td), Paragraph("筹备中 / 进行中 / 已完成 / 已取消", s_td)],
        [Paragraph("进度", s_td), Paragraph("0 – 100%，手动更新", s_td)],
        [Paragraph("项目经理 / 计划日期", s_td), Paragraph("负责人与时间计划", s_td)],
    ], [W*0.35, W*0.65])
    story.append(t)
    spacer(story, 3)

    sub_title(story, "8.2  审核任务")
    body(story, "项目下的具体执行任务，支持人员分配和优先级管理。")
    spacer(story, 2)
    t = table([
        [Paragraph("字段", s_th), Paragraph("说明", s_th)],
        [Paragraph("任务类型", s_td), Paragraph("文件审查 / 现场审核 / 报告编写 / 其他", s_td)],
        [Paragraph("优先级", s_td), Paragraph("紧急 / 高 / 普通 / 低", s_td)],
        [Paragraph("状态", s_td), Paragraph("待开始 → 进行中 → 已完成 / 已取消", s_td)],
        [Paragraph("负责人 / 计划日期", s_td), Paragraph("任务分配与时间节点", s_td)],
    ], [W*0.35, W*0.65])
    story.append(t)
    spacer(story, 2)
    body(story, "<b>操作步骤：</b>")
    note(story, "1. 点击「新增任务」，关联对应认证项目")
    note(story, "2. 指定负责人、优先级和计划日期")
    note(story, "3. 执行过程中更新任务状态")

    # ── 9. 系统管理 ───────────────────────────────────────────────
    section_title(story, 9, "系统管理")
    body(story, "仅管理员可见。")
    spacer(story, 2)

    sub_title(story, "9.1  用户管理")
    body(story, "管理系统登录账号。")
    spacer(story, 2)
    t = table([
        [Paragraph("操作", s_th), Paragraph("说明", s_th)],
        [Paragraph("新增用户", s_td), Paragraph("填写用户名、姓名、邮箱、电话，分配角色", s_td)],
        [Paragraph("编辑用户", s_td), Paragraph("修改基本信息和角色", s_td)],
        [Paragraph("启用 / 禁用", s_td), Paragraph("控制账号登录权限", s_td)],
        [Paragraph("重置密码", s_td), Paragraph("管理员为用户重置登录密码", s_td)],
    ], [W*0.25, W*0.75])
    story.append(t)
    spacer(story, 3)

    sub_title(story, "9.2  价格库")
    body(story, "维护认证项目参考报价数据，供创建报价单时自动填充。")
    spacer(story, 2)
    t = table([
        [Paragraph("字段", s_th), Paragraph("说明", s_th)],
        [Paragraph("国家 / 认证项目名称", s_td), Paragraph("主要搜索维度", s_td)],
        [Paragraph("交期（周）/ 包含测试", s_td), Paragraph("认证周期和测试要求", s_td)],
        [Paragraph("参考价格", s_td), Paragraph("报价单自动填充的默认单价", s_td)],
        [Paragraph("证书有效期 / 系列申请", s_td), Paragraph("认证特性参数", s_td)],
    ], [W*0.35, W*0.65])
    story.append(t)
    spacer(story, 2)
    note(story, "提示：在报价单明细中搜索国家 + 认证项目时，系统自动匹配价格库中的参考价格。")

    # ── 10. 业务流程总览 ──────────────────────────────────────────
    section_title(story, 10, "业务流程总览")
    spacer(story, 2)

    steps = [
        ("①", "线索录入", "记录来源、联系人、意向认证"),
        ("②", "线索跟进", "添加跟进记录，更新状态"),
        ("③", "创建商机", "关联线索，进入销售阶段管理"),
        ("④", "报价单", "创建报价单，填写认证明细，导出 PDF"),
        ("⑤", "合同生效", "状态改为「已接受」，自动创建收款记录"),
        ("⑥", "收款登记", "分期或全款登记，状态自动更新"),
        ("⑦", "支出记录", "关联报价单登记认证费/代理费等支出"),
        ("⑧", "认证项目", "创建认证项目，追踪整体进度"),
        ("⑨", "审核任务", "分配具体任务给执行人员"),
        ("⑩", "项目完成", "任务全部完成，项目状态更新为已完成"),
    ]
    t = table(
        [[Paragraph("步骤", s_th), Paragraph("环节", s_th), Paragraph("关键操作", s_th)]] +
        [[Paragraph(s, s_td_c), Paragraph(n, s_td), Paragraph(d, s_td)] for s, n, d in steps],
        [W*0.10, W*0.25, W*0.65]
    )
    story.append(t)
    spacer(story, 4)
    body(story, "如有功能问题或操作疑问，请联系系统管理员。")


# ── 页眉页脚 ──────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(fn, 8)
    canvas.setFillColor(C_GREY)
    canvas.drawString(18*mm, 8*mm, "任域通认证 ERP 系统使用手册")
    canvas.drawRightString(A4[0] - 18*mm, 8*mm, f"第 {doc.page} 页")
    canvas.restoreState()

# ── 主函数 ────────────────────────────────────────────────────────
def main():
    out_path = os.path.join(os.path.dirname(__file__), "使用手册.pdf")
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=15*mm, bottomMargin=18*mm,
    )
    story = []
    build_cover(story)
    build_toc(story)
    build_body(story)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"✓ 已生成：{out_path}")

if __name__ == "__main__":
    main()
