-- Canonical system-table baseline converted from the approved MySQL 8.4 schema.
-- Apply through a versioned PostgreSQL migration; this reference contains no DROP statements or seed rows.
-- Preserve the project bootstrap requirement for vector and pgcrypto extensions separately.

CREATE TABLE icoolkj_sys_ai_skill (
    id varchar(20) NOT NULL,
    skill_code varchar(64) NOT NULL,
    tool_name varchar(64) NOT NULL,
    category varchar(32) NOT NULL DEFAULT 'OFFICE',
    skill_name varchar(100) NOT NULL,
    name_i18n jsonb NULL,
    description varchar(500) NULL DEFAULT NULL,
    description_i18n jsonb NULL,
    required_permission varchar(128) NOT NULL,
    tool_description varchar(1000) NOT NULL,
    parameters_schema_json text NOT NULL,
    sort_no integer NOT NULL DEFAULT 0,
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NOT NULL DEFAULT '0',
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NOT NULL DEFAULT '0',
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_ai_skill PRIMARY KEY (id),
    CONSTRAINT uk_sys_ai_skill_code UNIQUE (skill_code),
    CONSTRAINT uk_sys_ai_skill_tool_name UNIQUE (tool_name)
);
COMMENT ON TABLE icoolkj_sys_ai_skill IS '平台 AI Skill 能力目录';
CREATE INDEX idx_sys_ai_skill_category_status ON icoolkj_sys_ai_skill (category, status, sort_no);
COMMENT ON COLUMN icoolkj_sys_ai_skill.id IS '主键';
COMMENT ON COLUMN icoolkj_sys_ai_skill.skill_code IS '稳定编码，与 Handler 绑定';
COMMENT ON COLUMN icoolkj_sys_ai_skill.tool_name IS 'OpenAI tool function name';
COMMENT ON COLUMN icoolkj_sys_ai_skill.category IS 'OFFICE/TOOL/OPS';
COMMENT ON COLUMN icoolkj_sys_ai_skill.skill_name IS '默认显示名（中文兜底）';
COMMENT ON COLUMN icoolkj_sys_ai_skill.name_i18n IS 'locale -> 显示名';
COMMENT ON COLUMN icoolkj_sys_ai_skill.description IS '默认描述（中文兜底）';
COMMENT ON COLUMN icoolkj_sys_ai_skill.description_i18n IS 'locale -> 描述';
COMMENT ON COLUMN icoolkj_sys_ai_skill.required_permission IS '调用所需业务权限码';
COMMENT ON COLUMN icoolkj_sys_ai_skill.tool_description IS '模型侧工具说明（英文）';
COMMENT ON COLUMN icoolkj_sys_ai_skill.parameters_schema_json IS 'OpenAI parameters JSON Schema';
COMMENT ON COLUMN icoolkj_sys_ai_skill.sort_no IS '排序，越小越前';
COMMENT ON COLUMN icoolkj_sys_ai_skill.status IS '0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_ai_skill.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_ai_skill.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_ai_skill.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_ai_skill.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_ai_skill.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_ai_skill.deleted IS '逻辑删除 0否 1是';

CREATE TABLE icoolkj_sys_banner (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    banner_title varchar(200) NOT NULL,
    image_file_id varchar(20) NOT NULL,
    display_positions varchar(100) NOT NULL,
    position_config text NULL,
    sort_no integer NOT NULL DEFAULT 99,
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_banner PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_banner IS '轮播图表';
CREATE INDEX idx_sys_banner_tenant_id ON icoolkj_sys_banner (tenant_id);
CREATE INDEX idx_sys_banner_status ON icoolkj_sys_banner (status);
CREATE INDEX idx_sys_banner_sort_no ON icoolkj_sys_banner (sort_no);
CREATE INDEX idx_sys_banner_created_at ON icoolkj_sys_banner (created_at);
COMMENT ON COLUMN icoolkj_sys_banner.id IS '轮播图ID';
COMMENT ON COLUMN icoolkj_sys_banner.tenant_id IS '租户ID，0表示平台轮播';
COMMENT ON COLUMN icoolkj_sys_banner.banner_title IS '标题';
COMMENT ON COLUMN icoolkj_sys_banner.image_file_id IS '图片文件ID(infra_file)';
COMMENT ON COLUMN icoolkj_sys_banner.display_positions IS '展示位置(逗号分隔字典值)';
COMMENT ON COLUMN icoolkj_sys_banner.position_config IS '各位置点击配置(JSON数组)';
COMMENT ON COLUMN icoolkj_sys_banner.sort_no IS '排序号(越小越靠前)';
COMMENT ON COLUMN icoolkj_sys_banner.status IS '状态 0启用 1停用';
COMMENT ON COLUMN icoolkj_sys_banner.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_banner.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_banner.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_banner.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_banner.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_banner.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_brand_pack (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    product_name varchar(64) NOT NULL DEFAULT '',
    product_name_i18n jsonb NULL,
    copyright_brand varchar(64) NULL DEFAULT NULL,
    icp_no varchar(64) NULL DEFAULT NULL,
    icp_url varchar(256) NULL DEFAULT NULL,
    domain varchar(128) NULL DEFAULT NULL,
    site_url varchar(256) NULL DEFAULT NULL,
    email varchar(128) NULL DEFAULT NULL,
    contact_name varchar(64) NULL DEFAULT NULL,
    contact_phone varchar(32) NULL DEFAULT NULL,
    assets_json jsonb NULL,
    labels_json jsonb NULL,
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_brand_pack PRIMARY KEY (id),
    CONSTRAINT uk_sys_brand_pack_tenant UNIQUE (tenant_id, deleted)
);
COMMENT ON TABLE icoolkj_sys_brand_pack IS '站点品牌/OEM 表';
CREATE INDEX idx_sys_brand_pack_tenant_id ON icoolkj_sys_brand_pack (tenant_id);
COMMENT ON COLUMN icoolkj_sys_brand_pack.id IS '品牌包ID';
COMMENT ON COLUMN icoolkj_sys_brand_pack.tenant_id IS '租户ID，0表示平台默认；业务租户有行即整包覆盖';
COMMENT ON COLUMN icoolkj_sys_brand_pack.product_name IS '产品名称（默认）';
COMMENT ON COLUMN icoolkj_sys_brand_pack.product_name_i18n IS 'locale→产品名';
COMMENT ON COLUMN icoolkj_sys_brand_pack.copyright_brand IS '版权品牌';
COMMENT ON COLUMN icoolkj_sys_brand_pack.icp_no IS '备案号';
COMMENT ON COLUMN icoolkj_sys_brand_pack.icp_url IS '备案链接';
COMMENT ON COLUMN icoolkj_sys_brand_pack.domain IS '站点域名';
COMMENT ON COLUMN icoolkj_sys_brand_pack.site_url IS '站点 URL';
COMMENT ON COLUMN icoolkj_sys_brand_pack.email IS '联系邮箱';
COMMENT ON COLUMN icoolkj_sys_brand_pack.contact_name IS '联系人';
COMMENT ON COLUMN icoolkj_sys_brand_pack.contact_phone IS '联系人电话';
COMMENT ON COLUMN icoolkj_sys_brand_pack.assets_json IS '品牌素材 profile_code→fileId（brand_logo_sm/md/lg、favicon、login_bg、qr_*）';
COMMENT ON COLUMN icoolkj_sys_brand_pack.labels_json IS '素材说明文案 profile_code→label（如二维码 caption）';
COMMENT ON COLUMN icoolkj_sys_brand_pack.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_brand_pack.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_brand_pack.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_brand_pack.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_brand_pack.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_brand_pack.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_config (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    config_name varchar(100) NOT NULL,
    config_key varchar(100) NOT NULL,
    config_value text NOT NULL,
    config_type char(1) NOT NULL DEFAULT 'N',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_config PRIMARY KEY (id),
    CONSTRAINT uk_sys_config_tenant_config_key UNIQUE (tenant_id, config_key, deleted)
);
COMMENT ON TABLE icoolkj_sys_config IS '系统参数表';
CREATE INDEX idx_sys_config_tenant_id ON icoolkj_sys_config (tenant_id);
COMMENT ON COLUMN icoolkj_sys_config.id IS '参数ID';
COMMENT ON COLUMN icoolkj_sys_config.tenant_id IS '租户ID，0表示平台级';
COMMENT ON COLUMN icoolkj_sys_config.config_name IS '参数名称';
COMMENT ON COLUMN icoolkj_sys_config.config_key IS '参数键名';
COMMENT ON COLUMN icoolkj_sys_config.config_value IS '参数键值（支持 JSON 大包）';
COMMENT ON COLUMN icoolkj_sys_config.config_type IS '是否系统内置 Y是 N否';
COMMENT ON COLUMN icoolkj_sys_config.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_config.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_config.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_config.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_config.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_config.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_dept (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    parent_id varchar(20) NOT NULL DEFAULT '0',
    ancestors varchar(1000) NOT NULL DEFAULT '0',
    region_id varchar(20) NULL DEFAULT NULL,
    dept_type varchar(20) NOT NULL DEFAULT 'INTERNAL',
    admin_level varchar(20) NULL DEFAULT NULL,
    competent_id varchar(20) NULL DEFAULT NULL,
    dept_name varchar(100) NOT NULL,
    dept_code varchar(50) NULL DEFAULT NULL,
    leader_name varchar(50) NULL DEFAULT NULL,
    phone varchar(20) NULL DEFAULT NULL,
    email varchar(100) NULL DEFAULT NULL,
    sort_no integer NOT NULL DEFAULT 0,
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_dept PRIMARY KEY (id),
    CONSTRAINT uk_sys_dept_tenant_dept_code UNIQUE (tenant_id, dept_code, deleted)
);
COMMENT ON TABLE icoolkj_sys_dept IS '部门表';
CREATE INDEX idx_sys_dept_tenant_id ON icoolkj_sys_dept (tenant_id);
CREATE INDEX idx_sys_dept_tenant_parent_id ON icoolkj_sys_dept (tenant_id, parent_id);
CREATE INDEX idx_sys_dept_tenant_ancestors ON icoolkj_sys_dept (tenant_id, left(ancestors, 255));
CREATE INDEX idx_sys_dept_tenant_region_type ON icoolkj_sys_dept (tenant_id, region_id, dept_type);
CREATE INDEX idx_sys_dept_tenant_competent ON icoolkj_sys_dept (tenant_id, competent_id);
CREATE INDEX idx_sys_dept_status ON icoolkj_sys_dept (status);
COMMENT ON COLUMN icoolkj_sys_dept.id IS '部门ID';
COMMENT ON COLUMN icoolkj_sys_dept.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_dept.parent_id IS '父部门ID';
COMMENT ON COLUMN icoolkj_sys_dept.ancestors IS '祖级部门ID链，逗号分隔';
COMMENT ON COLUMN icoolkj_sys_dept.region_id IS '归属区划ID';
COMMENT ON COLUMN icoolkj_sys_dept.dept_type IS 'COMPETENT主管部门 INTERNAL内设机构';
COMMENT ON COLUMN icoolkj_sys_dept.admin_level IS 'PROVINCE/CITY/COUNTY/DISTRICT/STREET/NONE';
COMMENT ON COLUMN icoolkj_sys_dept.competent_id IS '内设机构所属主管部门ID';
COMMENT ON COLUMN icoolkj_sys_dept.dept_name IS '部门名称';
COMMENT ON COLUMN icoolkj_sys_dept.dept_code IS '部门编码';
COMMENT ON COLUMN icoolkj_sys_dept.leader_name IS '负责人';
COMMENT ON COLUMN icoolkj_sys_dept.phone IS '联系电话';
COMMENT ON COLUMN icoolkj_sys_dept.email IS '邮箱';
COMMENT ON COLUMN icoolkj_sys_dept.sort_no IS '显示顺序';
COMMENT ON COLUMN icoolkj_sys_dept.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_dept.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_dept.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_dept.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_dept.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_dept.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_dept.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_dict_item (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    dict_type_id varchar(20) NOT NULL,
    dict_label varchar(100) NOT NULL,
    dict_value varchar(100) NOT NULL,
    value_type varchar(20) NOT NULL DEFAULT 'string',
    css_class varchar(100) NULL DEFAULT NULL,
    icon varchar(64) NULL DEFAULT NULL,
    list_class varchar(100) NULL DEFAULT NULL,
    is_default char(1) NOT NULL DEFAULT '0',
    sort_no integer NOT NULL DEFAULT 0,
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_dict_item PRIMARY KEY (id),
    CONSTRAINT uk_sys_dict_item_tenant_type_value UNIQUE (tenant_id, dict_type_id, dict_value, deleted)
);
COMMENT ON TABLE icoolkj_sys_dict_item IS '字典数据项表';
CREATE INDEX idx_sys_dict_item_tenant_id ON icoolkj_sys_dict_item (tenant_id);
CREATE INDEX idx_sys_dict_item_dict_type_id ON icoolkj_sys_dict_item (dict_type_id);
CREATE INDEX idx_sys_dict_item_status ON icoolkj_sys_dict_item (status);
COMMENT ON COLUMN icoolkj_sys_dict_item.id IS '字典项ID';
COMMENT ON COLUMN icoolkj_sys_dict_item.tenant_id IS '租户ID，0表示平台级';
COMMENT ON COLUMN icoolkj_sys_dict_item.dict_type_id IS '字典类型ID';
COMMENT ON COLUMN icoolkj_sys_dict_item.dict_label IS '字典标签';
COMMENT ON COLUMN icoolkj_sys_dict_item.dict_value IS '字典值';
COMMENT ON COLUMN icoolkj_sys_dict_item.value_type IS '值类型';
COMMENT ON COLUMN icoolkj_sys_dict_item.css_class IS '可选 CSS 类名';
COMMENT ON COLUMN icoolkj_sys_dict_item.icon IS 'Element Plus 图标 PascalCase 名（与 sys_menu.icon 约定一致）';
COMMENT ON COLUMN icoolkj_sys_dict_item.list_class IS '表格回显样式（Tag 色调）';
COMMENT ON COLUMN icoolkj_sys_dict_item.is_default IS '是否默认 0否 1是';
COMMENT ON COLUMN icoolkj_sys_dict_item.sort_no IS '显示顺序';
COMMENT ON COLUMN icoolkj_sys_dict_item.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_dict_item.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_dict_item.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_dict_item.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_dict_item.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_dict_item.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_dict_item.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_dict_type (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    dict_name varchar(100) NOT NULL,
    dict_type varchar(100) NOT NULL,
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_dict_type PRIMARY KEY (id),
    CONSTRAINT uk_sys_dict_type_tenant_dict_type UNIQUE (tenant_id, dict_type, deleted)
);
COMMENT ON TABLE icoolkj_sys_dict_type IS '字典类型表';
CREATE INDEX idx_sys_dict_type_tenant_id ON icoolkj_sys_dict_type (tenant_id);
CREATE INDEX idx_sys_dict_type_status ON icoolkj_sys_dict_type (status);
COMMENT ON COLUMN icoolkj_sys_dict_type.id IS '字典类型ID';
COMMENT ON COLUMN icoolkj_sys_dict_type.tenant_id IS '租户ID，0表示平台级';
COMMENT ON COLUMN icoolkj_sys_dict_type.dict_name IS '字典名称';
COMMENT ON COLUMN icoolkj_sys_dict_type.dict_type IS '字典类型';
COMMENT ON COLUMN icoolkj_sys_dict_type.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_dict_type.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_dict_type.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_dict_type.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_dict_type.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_dict_type.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_dict_type.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_i18n_locale (
    id varchar(20) NOT NULL,
    locale_code varchar(16) NOT NULL,
    locale_name varchar(64) NOT NULL,
    native_name varchar(64) NOT NULL,
    sort_no integer NOT NULL DEFAULT 0,
    is_default char(1) NOT NULL DEFAULT 'N',
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(256) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_i18n_locale PRIMARY KEY (id),
    CONSTRAINT uk_sys_i18n_locale_code_deleted UNIQUE (locale_code, deleted)
);
COMMENT ON TABLE icoolkj_sys_i18n_locale IS '国际化语言配置表';
CREATE INDEX idx_sys_i18n_locale_deleted ON icoolkj_sys_i18n_locale (deleted);
COMMENT ON COLUMN icoolkj_sys_i18n_locale.id IS '主键';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.locale_code IS '语言代码 zh-CN/en-US';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.locale_name IS '语言名称（管理端展示）';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.native_name IS '原生语言名称';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.sort_no IS '排序';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.is_default IS '是否默认 Y/N';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_i18n_locale.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_i18n_message (
    id varchar(20) NOT NULL,
    message_key varchar(128) NOT NULL,
    locale varchar(16) NOT NULL,
    message_value text NOT NULL,
    module varchar(64) NOT NULL DEFAULT 'common',
    scope varchar(16) NOT NULL DEFAULT 'frontend',
    remark varchar(256) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_i18n_message PRIMARY KEY (id),
    CONSTRAINT uk_sys_i18n_message_key_locale_deleted UNIQUE (message_key, locale, deleted)
);
COMMENT ON TABLE icoolkj_sys_i18n_message IS '平台国际化文案表';
CREATE INDEX idx_sys_i18n_message_locale ON icoolkj_sys_i18n_message (locale);
CREATE INDEX idx_sys_i18n_message_module ON icoolkj_sys_i18n_message (module);
CREATE INDEX idx_sys_i18n_message_scope ON icoolkj_sys_i18n_message (scope);
CREATE INDEX idx_sys_i18n_message_deleted ON icoolkj_sys_i18n_message (deleted);
COMMENT ON COLUMN icoolkj_sys_i18n_message.id IS '主键';
COMMENT ON COLUMN icoolkj_sys_i18n_message.message_key IS '消息键';
COMMENT ON COLUMN icoolkj_sys_i18n_message.locale IS '语言代码';
COMMENT ON COLUMN icoolkj_sys_i18n_message.message_value IS '消息内容';
COMMENT ON COLUMN icoolkj_sys_i18n_message.module IS '模块分组';
COMMENT ON COLUMN icoolkj_sys_i18n_message.scope IS '作用域 backend/frontend/all';
COMMENT ON COLUMN icoolkj_sys_i18n_message.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_i18n_message.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_i18n_message.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_i18n_message.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_i18n_message.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_i18n_message.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_ip_access_rule (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    rule_name varchar(100) NOT NULL,
    ip_address varchar(255) NOT NULL,
    match_type char(1) NOT NULL DEFAULT '1',
    rule_type char(1) NOT NULL,
    apply_scope char(1) NOT NULL DEFAULT '1',
    priority_no integer NOT NULL DEFAULT 0,
    status char(1) NOT NULL DEFAULT '0',
    start_at timestamp(3) without time zone NULL DEFAULT NULL,
    end_at timestamp(3) without time zone NULL DEFAULT NULL,
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_ip_access_rule PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_ip_access_rule IS 'IP访问规则表';
CREATE INDEX idx_sys_ip_access_rule_tenant_id ON icoolkj_sys_ip_access_rule (tenant_id);
CREATE INDEX idx_sys_ip_access_rule_status ON icoolkj_sys_ip_access_rule (status);
CREATE INDEX idx_sys_ip_access_rule_rule_type ON icoolkj_sys_ip_access_rule (rule_type);
CREATE INDEX idx_sys_ip_access_rule_apply_scope ON icoolkj_sys_ip_access_rule (apply_scope);
CREATE INDEX idx_sys_ip_access_rule_priority_no ON icoolkj_sys_ip_access_rule (priority_no);
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.id IS '规则ID';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.tenant_id IS '租户ID，0表示平台级';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.rule_name IS '规则名称';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.ip_address IS 'IP地址或CIDR网段';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.match_type IS '匹配类型 1单IP 2IP段 3CIDR';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.rule_type IS '规则类型 1允许 2禁止';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.apply_scope IS '应用范围 1登录 2后台访问 3开放接口 4全部';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.priority_no IS '优先级，值越大越优先';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.start_at IS '生效开始时间';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.end_at IS '生效结束时间';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_ip_access_rule.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_job (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    job_code varchar(64) NOT NULL,
    job_name varchar(100) NOT NULL,
    job_group varchar(64) NOT NULL DEFAULT 'PLATFORM',
    cron_expression varchar(100) NOT NULL,
    misfire_policy char(1) NOT NULL DEFAULT '3',
    allow_concurrent char(1) NOT NULL DEFAULT '0',
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_job PRIMARY KEY (id),
    CONSTRAINT uk_sys_job_code UNIQUE (job_code, deleted)
);
COMMENT ON TABLE icoolkj_sys_job IS '平台定时任务定义';
CREATE INDEX idx_sys_job_tenant_status ON icoolkj_sys_job (tenant_id, status, deleted);
COMMENT ON COLUMN icoolkj_sys_job.id IS '主键';
COMMENT ON COLUMN icoolkj_sys_job.tenant_id IS '租户ID（平台运维=0）';
COMMENT ON COLUMN icoolkj_sys_job.job_code IS '任务编码（绑定 JobHandler）';
COMMENT ON COLUMN icoolkj_sys_job.job_name IS '任务名称';
COMMENT ON COLUMN icoolkj_sys_job.job_group IS '任务分组';
COMMENT ON COLUMN icoolkj_sys_job.cron_expression IS 'Cron 表达式';
COMMENT ON COLUMN icoolkj_sys_job.misfire_policy IS 'misfire：1立即 2一次 3放弃';
COMMENT ON COLUMN icoolkj_sys_job.allow_concurrent IS '是否允许并发：0禁止 1允许';
COMMENT ON COLUMN icoolkj_sys_job.status IS '状态：0正常 1暂停';
COMMENT ON COLUMN icoolkj_sys_job.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_job.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_job.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_job.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_job.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_job.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_job_log (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    job_id varchar(20) NOT NULL,
    job_code varchar(64) NOT NULL,
    trigger_type varchar(16) NOT NULL,
    trigger_user_id varchar(20) NULL DEFAULT NULL,
    status varchar(16) NOT NULL,
    job_message varchar(500) NULL DEFAULT NULL,
    exception_info text NULL,
    request_param text NULL,
    result_summary text NULL,
    started_at timestamp(3) without time zone NOT NULL,
    finished_at timestamp(3) without time zone NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_sys_job_log PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_job_log IS '平台定时任务执行日志';
CREATE INDEX idx_sys_job_log_job_code ON icoolkj_sys_job_log (job_code, started_at);
CREATE INDEX idx_sys_job_log_job_id ON icoolkj_sys_job_log (job_id, started_at);
CREATE INDEX idx_sys_job_log_status ON icoolkj_sys_job_log (status, started_at);
CREATE INDEX idx_sys_job_log_trigger_user ON icoolkj_sys_job_log (trigger_user_id, started_at);
COMMENT ON COLUMN icoolkj_sys_job_log.id IS '主键';
COMMENT ON COLUMN icoolkj_sys_job_log.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_job_log.job_id IS '任务定义ID';
COMMENT ON COLUMN icoolkj_sys_job_log.job_code IS '任务编码';
COMMENT ON COLUMN icoolkj_sys_job_log.trigger_type IS '触发类型 CRON|MANUAL';
COMMENT ON COLUMN icoolkj_sys_job_log.trigger_user_id IS '手动触发人（Cron为空）';
COMMENT ON COLUMN icoolkj_sys_job_log.status IS 'RUNNING|SUCCESS|FAILED';
COMMENT ON COLUMN icoolkj_sys_job_log.job_message IS '摘要消息';
COMMENT ON COLUMN icoolkj_sys_job_log.exception_info IS '异常信息';
COMMENT ON COLUMN icoolkj_sys_job_log.request_param IS '请求/上下文 JSON';
COMMENT ON COLUMN icoolkj_sys_job_log.result_summary IS '结果摘要 JSON';
COMMENT ON COLUMN icoolkj_sys_job_log.started_at IS '开始时间';
COMMENT ON COLUMN icoolkj_sys_job_log.finished_at IS '结束时间';
COMMENT ON COLUMN icoolkj_sys_job_log.created_at IS '创建时间';

CREATE TABLE icoolkj_sys_login_log (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    username varchar(50) NOT NULL,
    login_type varchar(20) NOT NULL DEFAULT 'password',
    login_status char(1) NOT NULL,
    message varchar(500) NULL DEFAULT NULL,
    ip varchar(64) NULL DEFAULT NULL,
    location varchar(255) NULL DEFAULT NULL,
    user_agent varchar(500) NULL DEFAULT NULL,
    browser varchar(100) NULL DEFAULT NULL,
    os varchar(100) NULL DEFAULT NULL,
    login_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    prev_hash varchar(64) NULL DEFAULT NULL,
    row_hash varchar(64) NULL DEFAULT NULL,
    CONSTRAINT pk_sys_login_log PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_login_log IS '登录日志表';
CREATE INDEX idx_sys_login_log_tenant_id ON icoolkj_sys_login_log (tenant_id);
CREATE INDEX idx_sys_login_log_username ON icoolkj_sys_login_log (username);
CREATE INDEX idx_sys_login_log_status ON icoolkj_sys_login_log (login_status);
CREATE INDEX idx_sys_login_log_login_at ON icoolkj_sys_login_log (login_at);
COMMENT ON COLUMN icoolkj_sys_login_log.id IS '日志ID';
COMMENT ON COLUMN icoolkj_sys_login_log.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_login_log.username IS '登录账号';
COMMENT ON COLUMN icoolkj_sys_login_log.login_type IS '登录方式';
COMMENT ON COLUMN icoolkj_sys_login_log.login_status IS '登录状态 0成功 1失败';
COMMENT ON COLUMN icoolkj_sys_login_log.message IS '提示消息';
COMMENT ON COLUMN icoolkj_sys_login_log.ip IS '登录IP';
COMMENT ON COLUMN icoolkj_sys_login_log.location IS '登录地点';
COMMENT ON COLUMN icoolkj_sys_login_log.user_agent IS '用户代理';
COMMENT ON COLUMN icoolkj_sys_login_log.browser IS '浏览器';
COMMENT ON COLUMN icoolkj_sys_login_log.os IS '操作系统';
COMMENT ON COLUMN icoolkj_sys_login_log.login_at IS '登录时间';
COMMENT ON COLUMN icoolkj_sys_login_log.prev_hash IS '审计链上一行哈希';
COMMENT ON COLUMN icoolkj_sys_login_log.row_hash IS '本行完整性哈希';

CREATE TABLE icoolkj_sys_login_log_archive (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    username varchar(50) NOT NULL,
    login_type varchar(20) NOT NULL DEFAULT 'password',
    login_status char(1) NOT NULL,
    message varchar(500) NULL DEFAULT NULL,
    ip varchar(64) NULL DEFAULT NULL,
    location varchar(255) NULL DEFAULT NULL,
    user_agent varchar(500) NULL DEFAULT NULL,
    browser varchar(100) NULL DEFAULT NULL,
    os varchar(100) NULL DEFAULT NULL,
    login_at timestamp(3) without time zone NOT NULL,
    prev_hash varchar(64) NULL DEFAULT NULL,
    row_hash varchar(64) NULL DEFAULT NULL,
    archived_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_sys_login_log_archive PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_login_log_archive IS '登录日志归档';
CREATE INDEX idx_sys_login_log_archive_tenant_login_at ON icoolkj_sys_login_log_archive (tenant_id, login_at);
CREATE INDEX idx_sys_login_log_archive_login_at ON icoolkj_sys_login_log_archive (login_at);
CREATE INDEX idx_sys_login_log_archive_archived_at ON icoolkj_sys_login_log_archive (archived_at);

CREATE TABLE icoolkj_sys_menu (
    id varchar(20) NOT NULL,
    parent_id varchar(20) NOT NULL DEFAULT '0',
    menu_type char(1) NOT NULL,
    menu_name varchar(50) NOT NULL,
    name_i18n jsonb NULL,
    route_name varchar(100) NULL DEFAULT NULL,
    route_path varchar(200) NULL DEFAULT NULL,
    component_path varchar(200) NULL DEFAULT NULL,
    permission_code varchar(100) NULL DEFAULT NULL,
    icon varchar(100) NULL DEFAULT NULL,
    sort_no integer NOT NULL DEFAULT 0,
    visible char(1) NOT NULL DEFAULT '0',
    status char(1) NOT NULL DEFAULT '0',
    is_external char(1) NOT NULL DEFAULT '0',
    is_cache char(1) NOT NULL DEFAULT '1',
    remark varchar(500) NULL DEFAULT NULL,
    assign_scope varchar(20) NOT NULL DEFAULT 'TENANT',
    product_code varchar(32) NOT NULL DEFAULT 'platform',
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_menu PRIMARY KEY (id),
    CONSTRAINT uk_sys_menu_permission_scope UNIQUE (permission_code, assign_scope, deleted)
);
COMMENT ON TABLE icoolkj_sys_menu IS '菜单权限资源表';
CREATE INDEX idx_sys_menu_parent_id ON icoolkj_sys_menu (parent_id);
CREATE INDEX idx_sys_menu_menu_type ON icoolkj_sys_menu (menu_type);
CREATE INDEX idx_sys_menu_status ON icoolkj_sys_menu (status);
CREATE INDEX idx_sys_menu_product_code ON icoolkj_sys_menu (product_code);
COMMENT ON COLUMN icoolkj_sys_menu.id IS '资源ID';
COMMENT ON COLUMN icoolkj_sys_menu.parent_id IS '父资源ID';
COMMENT ON COLUMN icoolkj_sys_menu.menu_type IS '资源类型 M目录 C菜单 F按钮';
COMMENT ON COLUMN icoolkj_sys_menu.menu_name IS '资源名称';
COMMENT ON COLUMN icoolkj_sys_menu.name_i18n IS '菜单多语言名称 {\"zh-CN\":\"...\",\"en-US\":\"...\"}';
COMMENT ON COLUMN icoolkj_sys_menu.route_name IS '路由名称';
COMMENT ON COLUMN icoolkj_sys_menu.route_path IS '路由地址';
COMMENT ON COLUMN icoolkj_sys_menu.component_path IS '组件路径';
COMMENT ON COLUMN icoolkj_sys_menu.permission_code IS '权限标识';
COMMENT ON COLUMN icoolkj_sys_menu.icon IS '菜单图标';
COMMENT ON COLUMN icoolkj_sys_menu.sort_no IS '显示顺序';
COMMENT ON COLUMN icoolkj_sys_menu.visible IS '显示状态 0显示 1隐藏';
COMMENT ON COLUMN icoolkj_sys_menu.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_menu.is_external IS '是否外链 0否 1是';
COMMENT ON COLUMN icoolkj_sys_menu.is_cache IS '是否缓存 0否 1是';
COMMENT ON COLUMN icoolkj_sys_menu.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_menu.assign_scope IS '授权范围 PLATFORM/TENANT';
COMMENT ON COLUMN icoolkj_sys_menu.product_code IS '产品宇宙编码 platform/oa/files/ai/业务码';
COMMENT ON COLUMN icoolkj_sys_menu.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_menu.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_menu.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_menu.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_menu.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_notice (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    notice_title varchar(200) NOT NULL,
    notice_type char(1) NOT NULL DEFAULT '1',
    cover_file_id varchar(20) NULL DEFAULT NULL,
    notice_content text NULL,
    notice_summary varchar(60) NOT NULL,
    sort_no integer NOT NULL DEFAULT 99,
    publish_locations varchar(100) NULL DEFAULT NULL,
    approve_status varchar(20) NOT NULL DEFAULT 'draft',
    process_instance_id varchar(64) NULL DEFAULT NULL,
    process_definition_key varchar(64) NULL DEFAULT NULL,
    starter_user_id varchar(20) NULL DEFAULT NULL,
    submitted_at timestamp(3) without time zone NULL DEFAULT NULL,
    finished_at timestamp(3) without time zone NULL DEFAULT NULL,
    release_status varchar(20) NOT NULL DEFAULT 'unpublished',
    published_at timestamp(3) without time zone NULL DEFAULT NULL,
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_notice PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_notice IS '通知公告表';
CREATE INDEX idx_sys_notice_tenant_id ON icoolkj_sys_notice (tenant_id);
CREATE INDEX idx_sys_notice_status ON icoolkj_sys_notice (status);
CREATE INDEX idx_sys_notice_approve_status ON icoolkj_sys_notice (approve_status);
CREATE INDEX idx_sys_notice_release_status ON icoolkj_sys_notice (release_status);
CREATE INDEX idx_sys_notice_process_instance ON icoolkj_sys_notice (process_instance_id);
CREATE INDEX idx_sys_notice_sort_no ON icoolkj_sys_notice (sort_no);
CREATE INDEX idx_sys_notice_created_at ON icoolkj_sys_notice (created_at);
COMMENT ON COLUMN icoolkj_sys_notice.id IS '公告ID';
COMMENT ON COLUMN icoolkj_sys_notice.tenant_id IS '租户ID，0表示平台公告';
COMMENT ON COLUMN icoolkj_sys_notice.notice_title IS '公告标题';
COMMENT ON COLUMN icoolkj_sys_notice.notice_type IS '公告类型 1通知 2公告 3警告';
COMMENT ON COLUMN icoolkj_sys_notice.cover_file_id IS '封面图文件ID(infra_file)';
COMMENT ON COLUMN icoolkj_sys_notice.notice_content IS '公告内容(富文本HTML)';
COMMENT ON COLUMN icoolkj_sys_notice.notice_summary IS '摘要';
COMMENT ON COLUMN icoolkj_sys_notice.sort_no IS '排序号(越小越靠前)';
COMMENT ON COLUMN icoolkj_sys_notice.publish_locations IS '发布位置(逗号分隔字典值)';
COMMENT ON COLUMN icoolkj_sys_notice.approve_status IS '审批状态 draft/running/approved/rejected/cancelled/returned/closed';
COMMENT ON COLUMN icoolkj_sys_notice.process_instance_id IS 'Flowable流程实例ID';
COMMENT ON COLUMN icoolkj_sys_notice.process_definition_key IS '流程定义Key';
COMMENT ON COLUMN icoolkj_sys_notice.starter_user_id IS '发起人用户ID';
COMMENT ON COLUMN icoolkj_sys_notice.submitted_at IS '提交审批时间';
COMMENT ON COLUMN icoolkj_sys_notice.finished_at IS '审批结束时间';
COMMENT ON COLUMN icoolkj_sys_notice.release_status IS '上架状态 unpublished/published（仅 approved 后可发布/下架）';
COMMENT ON COLUMN icoolkj_sys_notice.published_at IS '最近上架时间（发布时写入）';
COMMENT ON COLUMN icoolkj_sys_notice.status IS '状态 0正常 1关闭';
COMMENT ON COLUMN icoolkj_sys_notice.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_notice.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_notice.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_notice.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_notice.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_notice.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_operation_log (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    trace_id varchar(64) NULL DEFAULT NULL,
    module_name varchar(100) NULL DEFAULT NULL,
    business_type varchar(50) NULL DEFAULT NULL,
    method varchar(255) NULL DEFAULT NULL,
    request_method varchar(20) NULL DEFAULT NULL,
    operator_id varchar(20) NULL DEFAULT NULL,
    operator_name varchar(50) NULL DEFAULT NULL,
    operation_url varchar(255) NULL DEFAULT NULL,
    operation_ip varchar(64) NULL DEFAULT NULL,
    operation_location varchar(255) NULL DEFAULT NULL,
    request_param text NULL,
    response_result text NULL,
    operation_status char(1) NOT NULL DEFAULT '0',
    error_message text NULL,
    cost_time integer NULL DEFAULT NULL,
    operation_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    prev_hash varchar(64) NULL DEFAULT NULL,
    row_hash varchar(64) NULL DEFAULT NULL,
    CONSTRAINT pk_sys_operation_log PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_operation_log IS '操作日志表';
CREATE INDEX idx_sys_operation_log_tenant_id ON icoolkj_sys_operation_log (tenant_id);
CREATE INDEX idx_sys_operation_log_operator_id ON icoolkj_sys_operation_log (operator_id);
CREATE INDEX idx_sys_operation_log_operation_status ON icoolkj_sys_operation_log (operation_status);
CREATE INDEX idx_sys_operation_log_operation_at ON icoolkj_sys_operation_log (operation_at);
COMMENT ON COLUMN icoolkj_sys_operation_log.id IS '日志ID';
COMMENT ON COLUMN icoolkj_sys_operation_log.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_operation_log.trace_id IS '链路ID';
COMMENT ON COLUMN icoolkj_sys_operation_log.module_name IS '模块名称';
COMMENT ON COLUMN icoolkj_sys_operation_log.business_type IS '业务类型';
COMMENT ON COLUMN icoolkj_sys_operation_log.method IS '方法名(类名.方法)';
COMMENT ON COLUMN icoolkj_sys_operation_log.request_method IS '请求方式';
COMMENT ON COLUMN icoolkj_sys_operation_log.operator_id IS '操作人ID';
COMMENT ON COLUMN icoolkj_sys_operation_log.operator_name IS '操作人';
COMMENT ON COLUMN icoolkj_sys_operation_log.operation_url IS '请求URL';
COMMENT ON COLUMN icoolkj_sys_operation_log.operation_ip IS '请求IP';
COMMENT ON COLUMN icoolkj_sys_operation_log.operation_location IS '操作地点';
COMMENT ON COLUMN icoolkj_sys_operation_log.request_param IS '脱敏后请求参数';
COMMENT ON COLUMN icoolkj_sys_operation_log.response_result IS '脱敏后返回结果';
COMMENT ON COLUMN icoolkj_sys_operation_log.operation_status IS '操作状态 0成功 1失败';
COMMENT ON COLUMN icoolkj_sys_operation_log.error_message IS '错误消息';
COMMENT ON COLUMN icoolkj_sys_operation_log.cost_time IS '耗时毫秒';
COMMENT ON COLUMN icoolkj_sys_operation_log.operation_at IS '操作时间';
COMMENT ON COLUMN icoolkj_sys_operation_log.prev_hash IS '审计链上一行哈希';
COMMENT ON COLUMN icoolkj_sys_operation_log.row_hash IS '本行完整性哈希';

CREATE TABLE icoolkj_sys_operation_log_archive (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    trace_id varchar(64) NULL DEFAULT NULL,
    module_name varchar(100) NULL DEFAULT NULL,
    business_type varchar(50) NULL DEFAULT NULL,
    method varchar(255) NULL DEFAULT NULL,
    request_method varchar(20) NULL DEFAULT NULL,
    operator_id varchar(20) NULL DEFAULT NULL,
    operator_name varchar(50) NULL DEFAULT NULL,
    operation_url varchar(255) NULL DEFAULT NULL,
    operation_ip varchar(64) NULL DEFAULT NULL,
    operation_location varchar(255) NULL DEFAULT NULL,
    request_param text NULL,
    response_result text NULL,
    operation_status char(1) NOT NULL DEFAULT '0',
    error_message text NULL,
    cost_time integer NULL DEFAULT NULL,
    operation_at timestamp(3) without time zone NOT NULL,
    prev_hash varchar(64) NULL DEFAULT NULL,
    row_hash varchar(64) NULL DEFAULT NULL,
    archived_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_sys_operation_log_archive PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_operation_log_archive IS '操作日志归档';
CREATE INDEX idx_sys_operation_log_archive_tenant_op_at ON icoolkj_sys_operation_log_archive (tenant_id, operation_at);
CREATE INDEX idx_sys_operation_log_archive_operation_at ON icoolkj_sys_operation_log_archive (operation_at);
CREATE INDEX idx_sys_operation_log_archive_archived_at ON icoolkj_sys_operation_log_archive (archived_at);

CREATE TABLE icoolkj_sys_post (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    post_name varchar(50) NOT NULL,
    post_code varchar(50) NOT NULL,
    sort_no integer NOT NULL DEFAULT 0,
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_post PRIMARY KEY (id),
    CONSTRAINT uk_sys_post_tenant_post_code UNIQUE (tenant_id, post_code, deleted)
);
COMMENT ON TABLE icoolkj_sys_post IS '岗位表';
CREATE INDEX idx_sys_post_tenant_id ON icoolkj_sys_post (tenant_id);
CREATE INDEX idx_sys_post_status ON icoolkj_sys_post (status);
COMMENT ON COLUMN icoolkj_sys_post.id IS '岗位ID';
COMMENT ON COLUMN icoolkj_sys_post.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_post.post_name IS '岗位名称';
COMMENT ON COLUMN icoolkj_sys_post.post_code IS '岗位编码';
COMMENT ON COLUMN icoolkj_sys_post.sort_no IS '显示顺序';
COMMENT ON COLUMN icoolkj_sys_post.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_post.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_post.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_post.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_post.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_post.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_post.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_product (
    id varchar(20) NOT NULL,
    code varchar(32) NOT NULL,
    name varchar(50) NOT NULL,
    name_i18n jsonb NULL,
    icon varchar(100) NULL DEFAULT NULL,
    sort_no integer NOT NULL DEFAULT 100,
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_product PRIMARY KEY (id),
    CONSTRAINT uk_sys_product_code UNIQUE (code, deleted)
);
COMMENT ON TABLE icoolkj_sys_product IS '产品宇宙目录';
CREATE INDEX idx_sys_product_sort ON icoolkj_sys_product (sort_no, status);
COMMENT ON COLUMN icoolkj_sys_product.id IS '产品ID';
COMMENT ON COLUMN icoolkj_sys_product.code IS '产品编码 platform/oa/files/ai/geo…';
COMMENT ON COLUMN icoolkj_sys_product.name IS '产品名称';
COMMENT ON COLUMN icoolkj_sys_product.name_i18n IS '多语言名称 {\"zh-CN\":\"...\",\"en-US\":\"...\"}';
COMMENT ON COLUMN icoolkj_sys_product.icon IS '图标';
COMMENT ON COLUMN icoolkj_sys_product.sort_no IS '显示顺序：业务宇宙宜 1–49，内置能力 50–89，platform 建议 90+';
COMMENT ON COLUMN icoolkj_sys_product.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_product.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_product.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_product.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_product.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_product.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_product.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_region (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL DEFAULT '0',
    parent_id varchar(20) NOT NULL DEFAULT '0',
    ancestors varchar(1000) NOT NULL DEFAULT '0',
    region_code varchar(12) NOT NULL,
    region_name varchar(100) NOT NULL,
    region_level char(1) NOT NULL,
    sort_no integer NOT NULL DEFAULT 0,
    status char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_region PRIMARY KEY (id),
    CONSTRAINT uk_sys_region_code UNIQUE (region_code, deleted)
);
COMMENT ON TABLE icoolkj_sys_region IS '行政区划表';
CREATE INDEX idx_sys_region_parent ON icoolkj_sys_region (parent_id);
CREATE INDEX idx_sys_region_level ON icoolkj_sys_region (region_level);
CREATE INDEX idx_sys_region_ancestors ON icoolkj_sys_region (left(ancestors, 255));
COMMENT ON COLUMN icoolkj_sys_region.id IS '区划ID';
COMMENT ON COLUMN icoolkj_sys_region.tenant_id IS '固定0=平台国标库';
COMMENT ON COLUMN icoolkj_sys_region.parent_id IS '父区划ID';
COMMENT ON COLUMN icoolkj_sys_region.ancestors IS '祖级区划ID链，逗号分隔';
COMMENT ON COLUMN icoolkj_sys_region.region_code IS '国标行政区划代码';
COMMENT ON COLUMN icoolkj_sys_region.region_name IS '区划名称';
COMMENT ON COLUMN icoolkj_sys_region.region_level IS '0国家 1省 2市 3区县 4街道 5社区';
COMMENT ON COLUMN icoolkj_sys_region.sort_no IS '显示顺序';
COMMENT ON COLUMN icoolkj_sys_region.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_region.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_region.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_region.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_region.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_region.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_region.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_role (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    role_name varchar(50) NOT NULL,
    role_code varchar(50) NOT NULL,
    data_scope char(1) NOT NULL DEFAULT '1',
    sort_no integer NOT NULL DEFAULT 0,
    status char(1) NOT NULL DEFAULT '0',
    is_super_role char(1) NOT NULL DEFAULT '0',
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_role PRIMARY KEY (id),
    CONSTRAINT uk_sys_role_tenant_role_code UNIQUE (tenant_id, role_code, deleted)
);
COMMENT ON TABLE icoolkj_sys_role IS '角色表';
CREATE INDEX idx_sys_role_tenant_id ON icoolkj_sys_role (tenant_id);
CREATE INDEX idx_sys_role_status ON icoolkj_sys_role (status);
COMMENT ON COLUMN icoolkj_sys_role.id IS '角色ID';
COMMENT ON COLUMN icoolkj_sys_role.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_role.role_name IS '角色名称';
COMMENT ON COLUMN icoolkj_sys_role.role_code IS '角色编码';
COMMENT ON COLUMN icoolkj_sys_role.data_scope IS '数据范围 1全部 2本部门及以下 3本部门 4本人 5自定义部门 6本区划及下级 7本区划 8自定义区划';
COMMENT ON COLUMN icoolkj_sys_role.sort_no IS '显示顺序';
COMMENT ON COLUMN icoolkj_sys_role.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_role.is_super_role IS '是否超级管理员角色 0否 1是';
COMMENT ON COLUMN icoolkj_sys_role.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_role.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_role.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_role.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_role.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_role.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_role_dept (
    tenant_id varchar(20) NOT NULL,
    role_id varchar(20) NOT NULL,
    dept_id varchar(20) NOT NULL,
    CONSTRAINT pk_sys_role_dept PRIMARY KEY (tenant_id, role_id, dept_id)
);
COMMENT ON TABLE icoolkj_sys_role_dept IS '角色部门数据权限表';
CREATE INDEX idx_sys_role_dept_role_id ON icoolkj_sys_role_dept (role_id);
CREATE INDEX idx_sys_role_dept_dept_id ON icoolkj_sys_role_dept (dept_id);
COMMENT ON COLUMN icoolkj_sys_role_dept.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_role_dept.role_id IS '角色ID';
COMMENT ON COLUMN icoolkj_sys_role_dept.dept_id IS '部门ID';

CREATE TABLE icoolkj_sys_role_menu (
    tenant_id varchar(20) NOT NULL,
    role_id varchar(20) NOT NULL,
    menu_id varchar(20) NOT NULL,
    CONSTRAINT pk_sys_role_menu PRIMARY KEY (tenant_id, role_id, menu_id)
);
COMMENT ON TABLE icoolkj_sys_role_menu IS '角色资源关联表';
CREATE INDEX idx_sys_role_menu_role_id ON icoolkj_sys_role_menu (role_id);
CREATE INDEX idx_sys_role_menu_menu_id ON icoolkj_sys_role_menu (menu_id);
COMMENT ON COLUMN icoolkj_sys_role_menu.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_role_menu.role_id IS '角色ID';
COMMENT ON COLUMN icoolkj_sys_role_menu.menu_id IS '资源ID';

CREATE TABLE icoolkj_sys_role_region (
    tenant_id varchar(20) NOT NULL,
    role_id varchar(20) NOT NULL,
    region_id varchar(20) NOT NULL,
    CONSTRAINT pk_sys_role_region PRIMARY KEY (tenant_id, role_id, region_id)
);
COMMENT ON TABLE icoolkj_sys_role_region IS '角色区划数据权限表';
CREATE INDEX idx_sys_role_region_role_id ON icoolkj_sys_role_region (role_id);
CREATE INDEX idx_sys_role_region_region_id ON icoolkj_sys_role_region (region_id);
COMMENT ON COLUMN icoolkj_sys_role_region.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_role_region.role_id IS '角色ID';
COMMENT ON COLUMN icoolkj_sys_role_region.region_id IS '区划ID';

CREATE TABLE icoolkj_sys_site_message (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    message_subject varchar(200) NOT NULL,
    message_category varchar(20) NOT NULL,
    message_content text NOT NULL,
    sender_id varchar(20) NOT NULL,
    user_id varchar(20) NOT NULL,
    sender_name varchar(50) NULL DEFAULT NULL,
    sent_at timestamp(3) without time zone NOT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_site_message PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_site_message IS '站内信主表';
CREATE INDEX idx_sys_site_message_tenant_id ON icoolkj_sys_site_message (tenant_id);
CREATE INDEX idx_sys_site_message_category ON icoolkj_sys_site_message (message_category);
CREATE INDEX idx_sys_site_message_sent_at ON icoolkj_sys_site_message (sent_at);
CREATE INDEX idx_sys_site_message_owner ON icoolkj_sys_site_message (tenant_id, user_id);
CREATE INDEX idx_sys_site_message_deleted ON icoolkj_sys_site_message (deleted);
COMMENT ON COLUMN icoolkj_sys_site_message.id IS '消息ID';
COMMENT ON COLUMN icoolkj_sys_site_message.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_site_message.message_subject IS '主题';
COMMENT ON COLUMN icoolkj_sys_site_message.message_category IS '分类 system/business';
COMMENT ON COLUMN icoolkj_sys_site_message.message_content IS '正文';
COMMENT ON COLUMN icoolkj_sys_site_message.sender_id IS '发送人ID';
COMMENT ON COLUMN icoolkj_sys_site_message.user_id IS '归属用户';
COMMENT ON COLUMN icoolkj_sys_site_message.sender_name IS '发送人姓名';
COMMENT ON COLUMN icoolkj_sys_site_message.sent_at IS '发送时间';
COMMENT ON COLUMN icoolkj_sys_site_message.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_site_message.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_site_message.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_site_message.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_site_message.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_site_message_recipient (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    message_id varchar(20) NOT NULL,
    user_id varchar(20) NOT NULL,
    read_at timestamp(3) without time zone NULL DEFAULT NULL,
    deleted boolean NOT NULL DEFAULT FALSE,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_sys_site_message_recipient PRIMARY KEY (id),
    CONSTRAINT uk_sys_site_message_recipient_msg_user UNIQUE (tenant_id, message_id, user_id, deleted)
);
COMMENT ON TABLE icoolkj_sys_site_message_recipient IS '站内信收件表';
CREATE INDEX idx_sys_site_message_recipient_tenant_id ON icoolkj_sys_site_message_recipient (tenant_id);
CREATE INDEX idx_sys_site_message_recipient_message_id ON icoolkj_sys_site_message_recipient (message_id);
CREATE INDEX idx_sys_site_message_recipient_user_id ON icoolkj_sys_site_message_recipient (user_id);
CREATE INDEX idx_sys_site_message_recipient_read_at ON icoolkj_sys_site_message_recipient (read_at);
CREATE INDEX idx_sys_site_message_recipient_deleted ON icoolkj_sys_site_message_recipient (deleted);
COMMENT ON COLUMN icoolkj_sys_site_message_recipient.id IS '收件记录ID';
COMMENT ON COLUMN icoolkj_sys_site_message_recipient.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_site_message_recipient.message_id IS '消息ID';
COMMENT ON COLUMN icoolkj_sys_site_message_recipient.user_id IS '收件人ID';
COMMENT ON COLUMN icoolkj_sys_site_message_recipient.read_at IS '已读时间';
COMMENT ON COLUMN icoolkj_sys_site_message_recipient.deleted IS '用户侧删除';
COMMENT ON COLUMN icoolkj_sys_site_message_recipient.created_at IS '创建时间';

CREATE TABLE icoolkj_sys_tenant (
    id varchar(20) NOT NULL,
    tenant_code varchar(50) NOT NULL,
    tenant_name varchar(100) NOT NULL,
    contact_name varchar(50) NULL DEFAULT NULL,
    contact_phone varchar(20) NULL DEFAULT NULL,
    contact_email varchar(100) NULL DEFAULT NULL,
    license_no varchar(100) NULL DEFAULT NULL,
    expire_at timestamp(3) without time zone NULL DEFAULT NULL,
    account_limit integer NULL DEFAULT NULL,
    status char(1) NOT NULL DEFAULT '0',
    tenant_type varchar(20) NOT NULL DEFAULT 'ENTERPRISE',
    parent_tenant_id varchar(20) NULL DEFAULT NULL,
    ancestors varchar(1000) NOT NULL DEFAULT '0',
    root_region_id varchar(20) NULL DEFAULT NULL,
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_tenant PRIMARY KEY (id),
    CONSTRAINT uk_sys_tenant_tenant_code UNIQUE (tenant_code, deleted)
);
COMMENT ON TABLE icoolkj_sys_tenant IS '租户表';
CREATE INDEX idx_sys_tenant_status ON icoolkj_sys_tenant (status);
CREATE INDEX idx_sys_tenant_expire_at ON icoolkj_sys_tenant (expire_at);
CREATE INDEX idx_sys_tenant_root_region ON icoolkj_sys_tenant (root_region_id);
CREATE INDEX idx_sys_tenant_type ON icoolkj_sys_tenant (tenant_type);
CREATE INDEX idx_sys_tenant_parent ON icoolkj_sys_tenant (parent_tenant_id);
COMMENT ON COLUMN icoolkj_sys_tenant.id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_tenant.tenant_code IS '租户编码';
COMMENT ON COLUMN icoolkj_sys_tenant.tenant_name IS '租户名称';
COMMENT ON COLUMN icoolkj_sys_tenant.contact_name IS '联系人';
COMMENT ON COLUMN icoolkj_sys_tenant.contact_phone IS '联系电话';
COMMENT ON COLUMN icoolkj_sys_tenant.contact_email IS '联系邮箱';
COMMENT ON COLUMN icoolkj_sys_tenant.license_no IS '营业执照号';
COMMENT ON COLUMN icoolkj_sys_tenant.expire_at IS '到期时间';
COMMENT ON COLUMN icoolkj_sys_tenant.account_limit IS '账号上限';
COMMENT ON COLUMN icoolkj_sys_tenant.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_tenant.tenant_type IS 'ENTERPRISE企业租户 ORGANIZATION单位租户';
COMMENT ON COLUMN icoolkj_sys_tenant.parent_tenant_id IS '上级单位租户ID，企业租户必须为空';
COMMENT ON COLUMN icoolkj_sys_tenant.ancestors IS '上级租户ID链';
COMMENT ON COLUMN icoolkj_sys_tenant.root_region_id IS '租户服务根区划ID';
COMMENT ON COLUMN icoolkj_sys_tenant.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_tenant.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_tenant.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_tenant.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_tenant.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_tenant.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_user (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    dept_id varchar(20) NULL DEFAULT NULL,
    username varchar(50) NOT NULL,
    nickname varchar(50) NOT NULL,
    real_name varchar(50) NULL DEFAULT NULL,
    user_type varchar(20) NOT NULL DEFAULT 'system',
    email varchar(100) NULL DEFAULT NULL,
    phone varchar(20) NULL DEFAULT NULL,
    gender char(1) NOT NULL DEFAULT '2',
    avatar_url varchar(255) NULL DEFAULT NULL,
    avatar_url_sm varchar(255) NULL DEFAULT NULL,
    avatar_url_lg varchar(255) NULL DEFAULT NULL,
    avatar_file_id varchar(20) NULL DEFAULT NULL,
    password_hash varchar(100) NOT NULL,
    status char(1) NOT NULL DEFAULT '0',
    is_super_admin char(1) NOT NULL DEFAULT '0',
    login_fail_count integer NOT NULL DEFAULT 0,
    locked_until timestamp(3) without time zone NULL DEFAULT NULL,
    last_login_ip varchar(64) NULL DEFAULT NULL,
    last_login_at timestamp(3) without time zone NULL DEFAULT NULL,
    pwd_updated_at timestamp(3) without time zone NULL DEFAULT NULL,
    must_change_password char(1) NOT NULL DEFAULT '0',
    mfa_enabled char(1) NOT NULL DEFAULT '0',
    mfa_secret_enc varchar(512) NULL DEFAULT NULL,
    mfa_bound_at timestamp(3) without time zone NULL DEFAULT NULL,
    remark varchar(500) NULL DEFAULT NULL,
    created_by varchar(20) NULL DEFAULT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by varchar(20) NULL DEFAULT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sys_user PRIMARY KEY (id),
    CONSTRAINT uk_sys_user_tenant_username UNIQUE (tenant_id, username, deleted)
);
COMMENT ON TABLE icoolkj_sys_user IS '用户表';
CREATE INDEX idx_sys_user_tenant_id ON icoolkj_sys_user (tenant_id);
CREATE INDEX idx_sys_user_dept_id ON icoolkj_sys_user (dept_id);
CREATE INDEX idx_sys_user_status ON icoolkj_sys_user (status);
CREATE INDEX idx_sys_user_locked_until ON icoolkj_sys_user (locked_until);
CREATE INDEX idx_sys_user_created_at ON icoolkj_sys_user (created_at);
COMMENT ON COLUMN icoolkj_sys_user.id IS '用户ID';
COMMENT ON COLUMN icoolkj_sys_user.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_user.dept_id IS '部门ID';
COMMENT ON COLUMN icoolkj_sys_user.username IS '登录账号';
COMMENT ON COLUMN icoolkj_sys_user.nickname IS '用户昵称';
COMMENT ON COLUMN icoolkj_sys_user.real_name IS '真实姓名';
COMMENT ON COLUMN icoolkj_sys_user.user_type IS '用户类型 system/platform';
COMMENT ON COLUMN icoolkj_sys_user.email IS '邮箱';
COMMENT ON COLUMN icoolkj_sys_user.phone IS '手机号';
COMMENT ON COLUMN icoolkj_sys_user.gender IS '性别 0男 1女 2未知';
COMMENT ON COLUMN icoolkj_sys_user.avatar_url IS '头像地址(中图)';
COMMENT ON COLUMN icoolkj_sys_user.avatar_url_sm IS '头像小图地址';
COMMENT ON COLUMN icoolkj_sys_user.avatar_url_lg IS '头像大图地址';
COMMENT ON COLUMN icoolkj_sys_user.avatar_file_id IS '头像主文件ID(infra_file)';
COMMENT ON COLUMN icoolkj_sys_user.password_hash IS '密码哈希';
COMMENT ON COLUMN icoolkj_sys_user.status IS '状态 0正常 1停用';
COMMENT ON COLUMN icoolkj_sys_user.is_super_admin IS '是否超级管理员 0否 1是';
COMMENT ON COLUMN icoolkj_sys_user.login_fail_count IS '连续登录失败次数';
COMMENT ON COLUMN icoolkj_sys_user.locked_until IS '锁定截止时间';
COMMENT ON COLUMN icoolkj_sys_user.last_login_ip IS '最后登录IP';
COMMENT ON COLUMN icoolkj_sys_user.last_login_at IS '最后登录时间';
COMMENT ON COLUMN icoolkj_sys_user.pwd_updated_at IS '密码更新时间';
COMMENT ON COLUMN icoolkj_sys_user.must_change_password IS '是否必须修改密码 0否 1是';
COMMENT ON COLUMN icoolkj_sys_user.mfa_enabled IS '是否启用 MFA 0否 1是';
COMMENT ON COLUMN icoolkj_sys_user.mfa_secret_enc IS 'TOTP 密钥密文(AES-GCM)';
COMMENT ON COLUMN icoolkj_sys_user.mfa_bound_at IS 'MFA 绑定时间';
COMMENT ON COLUMN icoolkj_sys_user.remark IS '备注';
COMMENT ON COLUMN icoolkj_sys_user.created_by IS '创建人';
COMMENT ON COLUMN icoolkj_sys_user.created_at IS '创建时间';
COMMENT ON COLUMN icoolkj_sys_user.updated_by IS '更新人';
COMMENT ON COLUMN icoolkj_sys_user.updated_at IS '更新时间';
COMMENT ON COLUMN icoolkj_sys_user.deleted IS '是否删除';

CREATE TABLE icoolkj_sys_user_password_history (
    id varchar(20) NOT NULL,
    tenant_id varchar(20) NOT NULL,
    user_id varchar(20) NOT NULL,
    password_hash varchar(100) NOT NULL,
    created_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_sys_user_password_history PRIMARY KEY (id)
);
COMMENT ON TABLE icoolkj_sys_user_password_history IS '用户密码历史（防重用）';
CREATE INDEX idx_sys_user_pwd_hist_user ON icoolkj_sys_user_password_history (tenant_id, user_id, created_at);
COMMENT ON COLUMN icoolkj_sys_user_password_history.id IS '主键';
COMMENT ON COLUMN icoolkj_sys_user_password_history.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_user_password_history.user_id IS '用户ID';
COMMENT ON COLUMN icoolkj_sys_user_password_history.password_hash IS '历史密码哈希';
COMMENT ON COLUMN icoolkj_sys_user_password_history.created_at IS '写入时间';

CREATE TABLE icoolkj_sys_user_post (
    tenant_id varchar(20) NOT NULL,
    user_id varchar(20) NOT NULL,
    post_id varchar(20) NOT NULL,
    CONSTRAINT pk_sys_user_post PRIMARY KEY (tenant_id, user_id, post_id)
);
COMMENT ON TABLE icoolkj_sys_user_post IS '用户岗位关联表';
CREATE INDEX idx_sys_user_post_user_id ON icoolkj_sys_user_post (user_id);
CREATE INDEX idx_sys_user_post_post_id ON icoolkj_sys_user_post (post_id);
COMMENT ON COLUMN icoolkj_sys_user_post.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_user_post.user_id IS '用户ID';
COMMENT ON COLUMN icoolkj_sys_user_post.post_id IS '岗位ID';

CREATE TABLE icoolkj_sys_user_preference (
    tenant_id varchar(20) NOT NULL,
    user_id varchar(20) NOT NULL,
    pref_key varchar(64) NOT NULL,
    pref_value varchar(256) NOT NULL,
    updated_at timestamp(3) without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_sys_user_preference PRIMARY KEY (tenant_id, user_id, pref_key)
);
COMMENT ON TABLE icoolkj_sys_user_preference IS '用户偏好表';
COMMENT ON COLUMN icoolkj_sys_user_preference.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_user_preference.user_id IS '用户ID';
COMMENT ON COLUMN icoolkj_sys_user_preference.pref_key IS '偏好键';
COMMENT ON COLUMN icoolkj_sys_user_preference.pref_value IS '偏好值';
COMMENT ON COLUMN icoolkj_sys_user_preference.updated_at IS '更新时间';

CREATE TABLE icoolkj_sys_user_role (
    tenant_id varchar(20) NOT NULL,
    user_id varchar(20) NOT NULL,
    role_id varchar(20) NOT NULL,
    CONSTRAINT pk_sys_user_role PRIMARY KEY (tenant_id, user_id, role_id)
);
COMMENT ON TABLE icoolkj_sys_user_role IS '用户角色关联表';
CREATE INDEX idx_sys_user_role_user_id ON icoolkj_sys_user_role (user_id);
CREATE INDEX idx_sys_user_role_role_id ON icoolkj_sys_user_role (role_id);
COMMENT ON COLUMN icoolkj_sys_user_role.tenant_id IS '租户ID';
COMMENT ON COLUMN icoolkj_sys_user_role.user_id IS '用户ID';
COMMENT ON COLUMN icoolkj_sys_user_role.role_id IS '角色ID';

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$;

CREATE TRIGGER trg_sys_ai_skill_updated_at BEFORE UPDATE ON icoolkj_sys_ai_skill FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_banner_updated_at BEFORE UPDATE ON icoolkj_sys_banner FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_brand_pack_updated_at BEFORE UPDATE ON icoolkj_sys_brand_pack FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_config_updated_at BEFORE UPDATE ON icoolkj_sys_config FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_dept_updated_at BEFORE UPDATE ON icoolkj_sys_dept FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_dict_item_updated_at BEFORE UPDATE ON icoolkj_sys_dict_item FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_dict_type_updated_at BEFORE UPDATE ON icoolkj_sys_dict_type FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_i18n_locale_updated_at BEFORE UPDATE ON icoolkj_sys_i18n_locale FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_i18n_message_updated_at BEFORE UPDATE ON icoolkj_sys_i18n_message FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_ip_access_rule_updated_at BEFORE UPDATE ON icoolkj_sys_ip_access_rule FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_job_updated_at BEFORE UPDATE ON icoolkj_sys_job FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_menu_updated_at BEFORE UPDATE ON icoolkj_sys_menu FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_notice_updated_at BEFORE UPDATE ON icoolkj_sys_notice FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_post_updated_at BEFORE UPDATE ON icoolkj_sys_post FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_product_updated_at BEFORE UPDATE ON icoolkj_sys_product FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_region_updated_at BEFORE UPDATE ON icoolkj_sys_region FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_role_updated_at BEFORE UPDATE ON icoolkj_sys_role FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_site_message_updated_at BEFORE UPDATE ON icoolkj_sys_site_message FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_tenant_updated_at BEFORE UPDATE ON icoolkj_sys_tenant FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_user_updated_at BEFORE UPDATE ON icoolkj_sys_user FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sys_user_preference_updated_at BEFORE UPDATE ON icoolkj_sys_user_preference FOR EACH ROW EXECUTE FUNCTION set_updated_at();
