-- ============================================================
-- 认证服务公司 ERP 系统 - 数据库 Schema
-- 数据库: PostgreSQL 15+
-- 版本: v0.1
-- 日期: 2026-02-18
-- ============================================================

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 公共函数：自动更新 updated_at 字段
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 1. 系统用户与权限
-- ============================================================

CREATE TABLE sys_user (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    username    VARCHAR(50) NOT NULL UNIQUE,
    full_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE,
    phone       VARCHAR(20),
    password_hash VARCHAR(200) NOT NULL,
    role        VARCHAR(30) NOT NULL,          -- ROLE_ADMIN / ROLE_MANAGER / ROLE_SALES /
                                               -- ROLE_AUDITOR / ROLE_AUDIT_MGR / ROLE_FINANCE / ROLE_CS
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    last_login  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_sys_user_updated_at
    BEFORE UPDATE ON sys_user
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 2. 市场需求管理
-- ============================================================

-- 线索
CREATE TABLE lead (
    id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name           VARCHAR(200) NOT NULL,
    contact_name           VARCHAR(100),
    contact_phone          VARCHAR(20)  NOT NULL,
    contact_email          VARCHAR(100),
    source                 VARCHAR(30)  NOT NULL,  -- 展会/网络/转介绍/电话/其他
    industry               VARCHAR(100),
    province               VARCHAR(50),
    city                   VARCHAR(50),
    certification_interest VARCHAR(500),           -- 意向认证项目（自由文本）
    status                 VARCHAR(20)  NOT NULL DEFAULT '待跟进',
                                                   -- 待跟进/跟进中/已转化/已放弃
    assigned_to            UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    next_follow_up_date    DATE,
    remark                 TEXT,
    created_by             UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_lead_updated_at
    BEFORE UPDATE ON lead
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 线索跟进记录
CREATE TABLE lead_follow_up (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id      UUID        NOT NULL REFERENCES lead(id) ON DELETE CASCADE,
    follow_type  VARCHAR(20) NOT NULL,  -- 电话/拜访/邮件/微信/其他
    content      TEXT        NOT NULL,
    next_date    DATE,
    created_by   UUID        REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 商机
CREATE TABLE opportunity (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    opp_name            VARCHAR(200)    NOT NULL,
    lead_id             UUID            REFERENCES lead(id) ON DELETE SET NULL,
    customer_id         UUID,           -- 关联已有客户（建立后填写，FK 在 customer 表创建后添加）
    company_name        VARCHAR(200)    NOT NULL,
    stage               VARCHAR(20)     NOT NULL DEFAULT '初步接触',
                                        -- 初步接触/需求确认/报价/谈判/赢单/输单
    certification_type  VARCHAR(200)    NOT NULL,
    estimated_amount    NUMERIC(12,2),
    expected_close_date DATE,
    win_probability     SMALLINT        CHECK (win_probability BETWEEN 0 AND 100),
    competitor          VARCHAR(200),
    loss_reason         TEXT,
    assigned_to         UUID            NOT NULL REFERENCES sys_user(id) ON DELETE RESTRICT,
    created_by          UUID            REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_opportunity_updated_at
    BEFORE UPDATE ON opportunity
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 商机跟进记录
CREATE TABLE opportunity_follow_up (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    opp_id       UUID        NOT NULL REFERENCES opportunity(id) ON DELETE CASCADE,
    follow_type  VARCHAR(20) NOT NULL,
    content      TEXT        NOT NULL,
    next_date    DATE,
    created_by   UUID        REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 报价单
CREATE TABLE quotation (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    opp_id          UUID        REFERENCES opportunity(id) ON DELETE RESTRICT,
    customer_id     UUID        REFERENCES customer(id) ON DELETE SET NULL,
    quote_no        VARCHAR(50) NOT NULL UNIQUE,  -- 系统自动生成，如 QT-2026-0001
    version         SMALLINT    NOT NULL DEFAULT 1,
    items           JSONB       NOT NULL DEFAULT '[]',
    -- items 结构: [{"name":"...", "standard":"...", "qty":1, "unit_price":1000, "discount":1.0, "amount":1000}]
    total_amount    NUMERIC(12,2) NOT NULL,
    discount_amount NUMERIC(12,2),
    discount_rate   NUMERIC(5,2),
    valid_until     DATE        NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT '草稿',
                                -- 草稿/待审批/已发送/已接受/已拒绝/已过期
    contact_name    VARCHAR(50),
    contact_phone   VARCHAR(30),
    deliver_to_address TEXT,
    product_name    VARCHAR(200),
    product_model   VARCHAR(200),
    payment_terms   TEXT,
    remark          TEXT,
    created_by      UUID        REFERENCES sys_user(id) ON DELETE SET NULL,
    approved_by     UUID        REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_quotation_updated_at
    BEFORE UPDATE ON quotation
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 3. 客户管理
-- ============================================================

-- 客户
CREATE TABLE customer (
    id                         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_no                VARCHAR(50) NOT NULL UNIQUE,  -- 系统自动生成，如 CU-2026-0001
    company_name               VARCHAR(200) NOT NULL,
    company_short_name         VARCHAR(100),
    unified_social_credit_code VARCHAR(20)  UNIQUE,
    legal_representative       VARCHAR(100),
    industry                   VARCHAR(100),
    company_size               VARCHAR(10),  -- 小微/中/大
    province                   VARCHAR(50),
    city                       VARCHAR(50),
    address                    VARCHAR(500),
    customer_level             CHAR(1),      -- A/B/C
    status                     VARCHAR(20)  NOT NULL DEFAULT '潜在',
                                             -- 潜在/在服务/已到期/已流失
    assigned_sales             UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    source_opp_id              UUID         REFERENCES opportunity(id) ON DELETE SET NULL,
    remark                     TEXT,
    created_by                 UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at                 TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at                 TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_customer_updated_at
    BEFORE UPDATE ON customer
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 补充 opportunity.customer_id 的外键
ALTER TABLE opportunity
    ADD CONSTRAINT fk_opportunity_customer
    FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE SET NULL;

-- 客户联系人
CREATE TABLE contact (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id  UUID        NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    name         VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    department   VARCHAR(100),
    phone        VARCHAR(20)  NOT NULL,
    email        VARCHAR(100),
    wechat       VARCHAR(100),
    is_primary   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_contact_updated_at
    BEFORE UPDATE ON contact
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 客户跟进记录
CREATE TABLE customer_follow_up (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id  UUID        NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    follow_type  VARCHAR(20) NOT NULL,  -- 电话/拜访/邮件/微信/其他
    content      TEXT        NOT NULL,
    next_date    DATE,
    created_by   UUID        REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 4. 订单 / 合同 / 付款管理
-- ============================================================

-- 合同
CREATE TABLE contract (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_no           VARCHAR(50) NOT NULL UNIQUE,  -- 系统自动生成，如 HT-2026-0001
    customer_id           UUID        NOT NULL REFERENCES customer(id) ON DELETE RESTRICT,
    opp_id                UUID        REFERENCES opportunity(id) ON DELETE SET NULL,
    contract_name         VARCHAR(200) NOT NULL,
    contract_type         VARCHAR(20)  NOT NULL,  -- 新签/续签/变更/补充协议
    certification_standard VARCHAR(200) NOT NULL,
    service_scope         TEXT        NOT NULL,
    total_amount          NUMERIC(12,2) NOT NULL,
    tax_rate              NUMERIC(5,2)  DEFAULT 6.00,
    sign_date             DATE,
    start_date            DATE,
    end_date              DATE,
    status                VARCHAR(20)  NOT NULL DEFAULT '草稿',
                                       -- 草稿/审批中/待签署/执行中/已完成/已终止
    signed_file_url       VARCHAR(500),
    sales_person          UUID         NOT NULL REFERENCES sys_user(id) ON DELETE RESTRICT,
    approved_by           UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    remark                TEXT,
    created_by            UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_contract_updated_at
    BEFORE UPDATE ON contract
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 合同变更记录
CREATE TABLE contract_change_log (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id   UUID        NOT NULL REFERENCES contract(id) ON DELETE CASCADE,
    change_reason TEXT        NOT NULL,
    change_detail TEXT        NOT NULL,
    changed_by    UUID        REFERENCES sys_user(id) ON DELETE SET NULL,
    changed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 合同服务项目明细
CREATE TABLE contract_item (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id    UUID        NOT NULL REFERENCES contract(id) ON DELETE CASCADE,
    item_name      VARCHAR(200) NOT NULL,
    standard       VARCHAR(100),
    audit_days     NUMERIC(6,1),  -- 人天数
    unit_price     NUMERIC(12,2) NOT NULL,
    quantity       NUMERIC(6,2)  NOT NULL DEFAULT 1,
    discount       NUMERIC(5,4)  NOT NULL DEFAULT 1.0000,
    amount         NUMERIC(12,2) NOT NULL,
    item_type      VARCHAR(20),   -- 初审/监督审核/再认证
    sort_order     SMALLINT      NOT NULL DEFAULT 0
);

-- 付款计划
CREATE TABLE payment_plan (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id     UUID        NOT NULL REFERENCES contract(id) ON DELETE CASCADE,
    installment_no  SMALLINT    NOT NULL,
    description     VARCHAR(200),          -- 首付款/尾款 等
    plan_amount     NUMERIC(12,2) NOT NULL,
    due_date        DATE         NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT '待支付',
                                 -- 待支付/部分支付/已支付/已逾期
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (contract_id, installment_no)
);

CREATE TRIGGER trg_payment_plan_updated_at
    BEFORE UPDATE ON payment_plan
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 收款记录
CREATE TABLE payment_record (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id          UUID        NOT NULL REFERENCES payment_plan(id) ON DELETE RESTRICT,
    contract_id      UUID        NOT NULL REFERENCES contract(id) ON DELETE RESTRICT,
    received_amount  NUMERIC(12,2) NOT NULL,
    received_date    DATE         NOT NULL,
    payment_method   VARCHAR(20)  NOT NULL,  -- 对公转账/现金/支票/其他
    bank_reference   VARCHAR(200),
    received_by      UUID         NOT NULL REFERENCES sys_user(id) ON DELETE RESTRICT,
    remark           TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 发票
CREATE TABLE invoice (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id     UUID        NOT NULL REFERENCES contract(id) ON DELETE RESTRICT,
    record_id       UUID        REFERENCES payment_record(id) ON DELETE SET NULL,
    invoice_type    VARCHAR(30)  NOT NULL,   -- 增值税普通发票/增值税专用发票
    invoice_title   VARCHAR(200) NOT NULL,
    tax_no          VARCHAR(50),
    invoice_amount  NUMERIC(12,2) NOT NULL,
    invoice_no      VARCHAR(50),
    issue_date      DATE,
    status          VARCHAR(20)  NOT NULL DEFAULT '待开具',
                                 -- 待开具/已开具/已邮寄/已上传
    file_url        VARCHAR(500),
    created_by      UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_invoice_updated_at
    BEFORE UPDATE ON invoice
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 5. 任务管理
-- ============================================================

-- 认证项目
CREATE TABLE cert_project (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_no           VARCHAR(50) NOT NULL UNIQUE,  -- 系统自动生成，如 PRJ-2026-0001
    contract_id          UUID        NOT NULL REFERENCES contract(id) ON DELETE RESTRICT,
    customer_id          UUID        NOT NULL REFERENCES customer(id) ON DELETE RESTRICT,
    standard             VARCHAR(100) NOT NULL,
    certification_scope  TEXT        NOT NULL,
    phase                VARCHAR(30)  NOT NULL DEFAULT '待启动',
                                     -- 待启动/文件审查/审核准备/现场审核/报告整理/发证/监督审核/再认证
    project_manager      UUID         NOT NULL REFERENCES sys_user(id) ON DELETE RESTRICT,
    planned_start_date   DATE,
    planned_end_date     DATE,
    actual_end_date      DATE,
    progress             SMALLINT     NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    status               VARCHAR(20)  NOT NULL DEFAULT '待启动',
                                     -- 待启动/进行中/已完成/已终止
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_cert_project_updated_at
    BEFORE UPDATE ON cert_project
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 证书（发证后记录）
CREATE TABLE certificate (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID        NOT NULL REFERENCES customer(id) ON DELETE RESTRICT,
    project_id          UUID        REFERENCES cert_project(id) ON DELETE SET NULL,
    related_contract_id UUID        REFERENCES contract(id) ON DELETE SET NULL,
    cert_no             VARCHAR(100) NOT NULL,
    standard            VARCHAR(100) NOT NULL,
    scope               TEXT         NOT NULL,
    issue_date          DATE         NOT NULL,
    expiry_date         DATE         NOT NULL,
    status              VARCHAR(20)  NOT NULL DEFAULT '有效',
                                     -- 有效/暂停/撤销/已过期
    cert_file_url       VARCHAR(500),
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_certificate_updated_at
    BEFORE UPDATE ON certificate
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 任务
CREATE TABLE task (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id     UUID        NOT NULL REFERENCES cert_project(id) ON DELETE CASCADE,
    task_name      VARCHAR(200) NOT NULL,
    task_type      VARCHAR(30)  NOT NULL,
                               -- 文件审查/现场审核/监督审核/再认证/报告编写
    description    TEXT,
    assigned_to    UUID         NOT NULL REFERENCES sys_user(id) ON DELETE RESTRICT,
    co_auditors    UUID[]       NOT NULL DEFAULT '{}',  -- 协同审核员 ID 数组
    priority       VARCHAR(10)  NOT NULL DEFAULT '中',  -- 低/中/高/紧急
    planned_start  TIMESTAMPTZ  NOT NULL,
    planned_end    TIMESTAMPTZ  NOT NULL,
    actual_start   TIMESTAMPTZ,
    actual_end     TIMESTAMPTZ,
    actual_hours   NUMERIC(6,2),
    status         VARCHAR(20)  NOT NULL DEFAULT '待开始',
                               -- 待开始/进行中/待审阅/已完成/已取消
    result         TEXT,
    created_by     UUID         NOT NULL REFERENCES sys_user(id) ON DELETE RESTRICT,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_task_updated_at
    BEFORE UPDATE ON task
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 不符合项
CREATE TABLE non_conformity (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id          UUID        NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    nc_type          VARCHAR(20)  NOT NULL,   -- 一般不符合/严重不符合/观察项
    standard_clause  VARCHAR(100),
    description      TEXT         NOT NULL,
    evidence         TEXT,
    corrective_action TEXT,
    due_date         DATE,
    close_status     VARCHAR(20)  NOT NULL DEFAULT '开放',
                                  -- 开放/待验证/已关闭
    closed_by        UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    closed_at        DATE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_non_conformity_updated_at
    BEFORE UPDATE ON non_conformity
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 审核报告
CREATE TABLE audit_report (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id       UUID        NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    version       SMALLINT    NOT NULL DEFAULT 1,
    report_type   VARCHAR(30)  NOT NULL,   -- 初审报告/监督报告/再认证报告
    conclusion    VARCHAR(30)  NOT NULL,   -- 推荐认证/不推荐/待整改后推荐
    summary       TEXT,
    file_url      VARCHAR(500),
    status        VARCHAR(20)  NOT NULL DEFAULT '草稿',
                               -- 草稿/待审阅/已批准/已发送
    submitted_by  UUID         NOT NULL REFERENCES sys_user(id) ON DELETE RESTRICT,
    approved_by   UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    approved_at   TIMESTAMPTZ,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, version)
);

CREATE TRIGGER trg_audit_report_updated_at
    BEFORE UPDATE ON audit_report
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 6. 公共服务
-- ============================================================

-- 附件（统一附件表，通过 entity_type + entity_id 关联任意实体）
CREATE TABLE attachment (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type  VARCHAR(50)  NOT NULL,   -- lead/customer/contract/task/report/...
    entity_id    UUID         NOT NULL,
    file_name    VARCHAR(200) NOT NULL,
    file_url     VARCHAR(500) NOT NULL,
    file_size    BIGINT,                  -- 字节数
    mime_type    VARCHAR(100),
    uploaded_by  UUID         REFERENCES sys_user(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_attachment_entity ON attachment (entity_type, entity_id);

-- 操作日志
CREATE TABLE operation_log (
    id           BIGSERIAL   PRIMARY KEY,
    user_id      UUID        REFERENCES sys_user(id) ON DELETE SET NULL,
    username     VARCHAR(50),
    action       VARCHAR(100) NOT NULL,   -- CREATE / UPDATE / DELETE / LOGIN / EXPORT ...
    entity_type  VARCHAR(50),
    entity_id    UUID,
    detail       JSONB,
    ip           VARCHAR(45),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_operation_log_user    ON operation_log (user_id);
CREATE INDEX idx_operation_log_entity  ON operation_log (entity_type, entity_id);
CREATE INDEX idx_operation_log_created ON operation_log (created_at DESC);

-- 系统通知
CREATE TABLE notification (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID        NOT NULL REFERENCES sys_user(id) ON DELETE CASCADE,
    title        VARCHAR(200) NOT NULL,
    content      TEXT,
    link_type    VARCHAR(50),  -- contract/task/payment_plan/... （点击跳转目标类型）
    link_id      UUID,
    is_read      BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notification_user ON notification (user_id, is_read, created_at DESC);

-- ============================================================
-- 7. 常用索引
-- ============================================================

-- 线索
CREATE INDEX idx_lead_status       ON lead (status);
CREATE INDEX idx_lead_assigned_to  ON lead (assigned_to);
CREATE INDEX idx_lead_company      ON lead (company_name);

-- 商机
CREATE INDEX idx_opp_stage         ON opportunity (stage);
CREATE INDEX idx_opp_assigned_to   ON opportunity (assigned_to);
CREATE INDEX idx_opp_customer      ON opportunity (customer_id);

-- 客户
CREATE INDEX idx_customer_status   ON customer (status);
CREATE INDEX idx_customer_sales    ON customer (assigned_sales);
CREATE INDEX idx_customer_company  ON customer (company_name);

-- 合同
CREATE INDEX idx_contract_customer ON contract (customer_id);
CREATE INDEX idx_contract_status   ON contract (status);
CREATE INDEX idx_contract_sales    ON contract (sales_person);

-- 付款计划
CREATE INDEX idx_payment_plan_due  ON payment_plan (due_date, status);

-- 证书到期预警
CREATE INDEX idx_certificate_expiry ON certificate (expiry_date, status);

-- 任务
CREATE INDEX idx_task_project      ON task (project_id);
CREATE INDEX idx_task_assigned     ON task (assigned_to);
CREATE INDEX idx_task_status       ON task (status);
CREATE INDEX idx_task_planned_end  ON task (planned_end);

-- 认证项目
CREATE INDEX idx_cert_project_customer  ON cert_project (customer_id);
CREATE INDEX idx_cert_project_status    ON cert_project (status);

-- ============================================================
-- 8. 编号序列（用于生成业务编号）
-- ============================================================

CREATE SEQUENCE seq_customer_no  START 1 INCREMENT 1;
CREATE SEQUENCE seq_contract_no  START 1 INCREMENT 1;
CREATE SEQUENCE seq_quotation_no START 1 INCREMENT 1;
CREATE SEQUENCE seq_project_no   START 1 INCREMENT 1;

-- ============================================================
-- 9. 编号序列（用于生成业务编号）
-- ============================================================
--   customer_no  = 'CU-' || to_char(NOW(), 'YYYY') || '-' || lpad(nextval('seq_customer_no')::text, 4, '0')
--   contract_no  = 'HT-' || to_char(NOW(), 'YYYY') || '-' || lpad(nextval('seq_contract_no')::text, 4, '0')
--   quotation_no = 'QT-' || to_char(NOW(), 'YYYY') || '-' || lpad(nextval('seq_quotation_no')::text, 4, '0')

-- ============================================================
-- 10. 价格库
-- ============================================================

CREATE TABLE price_catalog (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    country             VARCHAR(100),
    name                VARCHAR(200)  NOT NULL,
    cert_type           VARCHAR(50),
    sample_qty          SMALLINT,
    based_on_report     VARCHAR(10),
    lead_weeks          SMALLINT,
    includes_testing    VARCHAR(10),
    cert_validity_years SMALLINT,
    series_apply        VARCHAR(10),
    ref_price           NUMERIC(12,2),
    remark              TEXT,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_price_catalog_updated_at
    BEFORE UPDATE ON price_catalog
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
--   project_no   = 'PRJ-' || to_char(NOW(), 'YYYY') || '-' || lpad(nextval('seq_project_no')::text, 4, '0')
