-- 价格库导入脚本（先导入5条测试）
-- 执行方式: docker exec rerp_db psql -U rerp -d rerp -f /tmp/import_price_catalog.sql

-- 清空旧数据（如需全量重导时取消注释）
-- TRUNCATE price_catalog;

-- 字段说明:
--   country            国家（英文）
--   name               认证名称
--   cert_type          强制性/自愿性
--   sample_qty         样机数量
--   based_on_report    基于CE/FCC报告转证（Y/N/当地测试）
--   lead_weeks         认证周期（周，取最大值）
--   cert_validity_years 证书有效期（年，永久=NULL）
--   series_apply       可系列申请（Y/N）
--   ref_price          预估总体费用（元，0或空=NULL）
--   remark             备注

INSERT INTO price_catalog (country, name, cert_type, sample_qty, based_on_report, lead_weeks, cert_validity_years, series_apply, ref_price, remark) VALUES
-- 1. Abu Dhabi - TDRA，5周，3年，4500元
('Abu Dhabi', 'TDRA', '强制', 0, 'Y', 5, 3, 'N', 4500.00, 'TDRA 3年'),

-- 2. Algeria - ARPCE，10-12周取12，2年，22500元，需1pcs样机
('Algeria', 'ARPCE', '强制', 1, 'Y', 12, 2, 'N', 22500.00, NULL),

-- 3. Australia - RCM，2周，永久，1500元，可系列
('Australia', 'RCM', '强制', 0, 'Y', 2, NULL, 'Y', 1500.00, NULL),

-- 4. Brazil - Anatel，8-10周取10，永久，48000元，当地测试
('Brazil', 'Anatel', '强制', 0, 'N', 10, NULL, 'N', 48000.00, '1pcs传导定频样机，1pcs正常样机'),

-- 5. Korea, Republic of - KC，2周，永久，65000元，当地测试
('Korea, Republic of', 'KC', '强制', 0, 'N', 2, NULL, 'N', 65000.00, '1pcs传导定频样机，1pcs正常样机');
