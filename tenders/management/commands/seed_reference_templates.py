from django.core.management.base import BaseCommand

from tenders.models import Contract, TenderReference


REFERENCE_TEMPLATES = [
    {
        "title": "智慧园区综合管理平台建设参考标书",
        "project_type": "软件信息化",
        "industry": "园区数字化",
        "region": "江苏",
        "issuing_organization": "某高新区管理委员会",
        "budget_amount": 4800000,
        "summary": "适合参考园区门户、招商管理、企业服务、数据驾驶舱等软件平台类项目。",
        "reference_points": "重点关注项目经理资历、驻场团队、原厂授权、同类案例、验收里程碑。",
        "source_text": "第一章 招标公告\n第二章 投标人须知\n第三章 技术规范\n第四章 项目实施要求\n第五章 评分办法",
        "tags": "智慧园区、数字平台、软件实施",
    },
    {
        "title": "电子政务云资源池扩容参考标书",
        "project_type": "云平台建设",
        "industry": "政务信息化",
        "region": "上海",
        "issuing_organization": "某市大数据中心",
        "budget_amount": 9200000,
        "summary": "适合参考云资源扩容、灾备、监控审计、等保整改和运维服务条款。",
        "reference_points": "重点关注SLA、等保三级、割接窗口、资源池配额、应急演练。",
        "source_text": "第一章 项目概况\n第二章 云资源要求\n第三章 安全合规要求\n第四章 运维响应机制\n第五章 商务条款",
        "tags": "政务云、扩容、等保、运维",
    },
    {
        "title": "医院信息集成平台与数据中心参考标书",
        "project_type": "医疗信息化",
        "industry": "智慧医疗",
        "region": "广东",
        "issuing_organization": "某三级医院",
        "budget_amount": 7800000,
        "summary": "适合参考HIS、EMR、LIS、PACS等系统集成和院内数据中心建设项目。",
        "reference_points": "重点关注接口标准、数据治理、停机窗口、医疗数据安全和驻场服务。",
        "source_text": "第一章 招标范围\n第二章 医疗数据标准\n第三章 系统接口要求\n第四章 培训与运维\n第五章 评分细则",
        "tags": "医疗信息化、数据中心、系统集成",
    },
    {
        "title": "网络安全态势感知平台参考标书",
        "project_type": "网络安全",
        "industry": "政企安全",
        "region": "浙江",
        "issuing_organization": "某市网信中心",
        "budget_amount": 6500000,
        "summary": "适合参考资产测绘、日志采集、威胁检测、告警联动和安全运营服务项目。",
        "reference_points": "重点关注等保合规、日志接入范围、告警准确率、应急响应和安全服务资质。",
        "source_text": "第一章 招标公告\n第二章 安全能力要求\n第三章 平台功能清单\n第四章 服务响应要求\n第五章 评分办法",
        "tags": "网络安全、态势感知、安全运营",
    },
    {
        "title": "城市运行数字孪生平台参考标书",
        "project_type": "智慧城市",
        "industry": "城市治理",
        "region": "四川",
        "issuing_organization": "某市城市运行中心",
        "budget_amount": 12800000,
        "summary": "适合参考三维底座、物联接入、事件联动、指挥调度和专题场景建设。",
        "reference_points": "重点关注三维引擎性能、数据更新机制、物联接口、专题场景边界和展示效果。",
        "source_text": "第一章 项目背景\n第二章 建设内容\n第三章 数字孪生能力\n第四章 数据接入要求\n第五章 验收标准",
        "tags": "数字孪生、智慧城市、指挥调度",
    },
    {
        "title": "工业互联网数据中台参考标书",
        "project_type": "工业互联网",
        "industry": "制造业数字化",
        "region": "山东",
        "issuing_organization": "某智能制造产业园",
        "budget_amount": 11000000,
        "summary": "适合参考工业数据采集、数据治理、指标体系、设备画像和预测性维护。",
        "reference_points": "重点关注生产网络隔离、采集网关、数据质量、指标模型和工厂现场实施条件。",
        "source_text": "第一章 招标公告\n第二章 工业数据采集\n第三章 数据治理要求\n第四章 安全隔离方案\n第五章 服务要求",
        "tags": "工业互联网、数据中台、制造业",
    },
    {
        "title": "智慧水务监测平台参考标书",
        "project_type": "物联网平台",
        "industry": "智慧水务",
        "region": "湖北",
        "issuing_organization": "某水务集团",
        "budget_amount": 6200000,
        "summary": "适合参考水质监测、管网压力、泵站监控、GIS展示和移动巡检项目。",
        "reference_points": "重点关注传感器接入、通信稳定性、GIS定位、移动巡检和数据校准机制。",
        "source_text": "第一章 项目概况\n第二章 监测设备要求\n第三章 平台功能\n第四章 运维服务\n第五章 评分细则",
        "tags": "智慧水务、物联网、GIS",
    },
    {
        "title": "公共资源交易平台升级参考标书",
        "project_type": "电子交易",
        "industry": "公共资源",
        "region": "重庆",
        "issuing_organization": "某公共资源交易中心",
        "budget_amount": 8600000,
        "summary": "适合参考电子招投标、专家抽取、远程开标、监管留痕和 CA 接入。",
        "reference_points": "重点关注电子签章、CA兼容、远程开标稳定性、审计追溯和合规要求。",
        "source_text": "第一章 招标公告\n第二章 业务功能\n第三章 安全合规\n第四章 接口规范\n第五章 项目实施",
        "tags": "公共资源、电子招投标、远程开标",
    },
    {
        "title": "智慧工地监管平台参考标书",
        "project_type": "工程监管",
        "industry": "住建监管",
        "region": "河南",
        "issuing_organization": "某住房和城乡建设局",
        "budget_amount": 5200000,
        "summary": "适合参考实名制、扬尘监测、视频AI识别、塔吊监测和监管驾驶舱。",
        "reference_points": "重点关注现场网络、视频算法准确率、设备维护、监管报表和安全文明施工。",
        "source_text": "第一章 项目范围\n第二章 设备接入\n第三章 AI识别要求\n第四章 监管报表\n第五章 服务保障",
        "tags": "智慧工地、住建监管、视频AI",
    },
    {
        "title": "校园弱电系统改造工程参考标书",
        "project_type": "弱电集成",
        "industry": "教育信息化",
        "region": "安徽",
        "issuing_organization": "某职业技术学院",
        "budget_amount": 3800000,
        "summary": "适合参考综合布线、视频监控、门禁广播、校园网络和机房配套工程。",
        "reference_points": "重点关注施工周期、持证人员、设备品牌、暑期施工窗口和售后巡检。",
        "source_text": "第一章 招标公告\n第二章 工程量清单\n第三章 设备参数\n第四章 施工组织\n第五章 售后服务",
        "tags": "弱电工程、校园网络、综合布线",
    },
]


CONTRACT_TEMPLATES = [
    {
        "basic_info": "智慧园区综合管理平台建设项目\n采购方式：公开招标\n预算区间：400万-800万元\n适用地区：全国",
        "tender_content": "建设园区数字底座、企业服务门户、招商管理、物业服务、可视化驾驶舱和移动端应用，支持统一身份认证和多系统数据接入。",
        "reference_points": "参考项目经理资历、实施团队、原厂授权、同类园区案例、阶段验收里程碑和驻场服务承诺。",
        "scoring_rules": "技术方案50分，实施团队15分，同类业绩15分，商务报价20分。",
        "risk_tags": "驻场服务风险\n原厂授权风险\n跨系统接口风险",
        "material_checklist": "营业执照\nISO9001\nCMMI或软件能力证明\n同类业绩合同\n项目经理简历\n原厂授权函",
        "source_maintenance_info": "来源：参考模板库\n维护人：投标管理部\n适用：软件平台类项目",
    },
    {
        "basic_info": "电子政务云资源池扩容项目\n采购方式：公开招标\n预算区间：700万-1500万元\n适用地区：政务行业",
        "tender_content": "扩容计算、存储、网络与安全资源，完善灾备、监控、日志审计、等保整改和运维响应机制。",
        "reference_points": "参考SLA、等保三级、资源迁移、割接窗口、应急演练和7x24值守要求。",
        "scoring_rules": "技术能力45分，安全合规20分，运维服务20分，报价15分。",
        "risk_tags": "割接失败风险\n等保合规风险\n7x24运维压力",
        "material_checklist": "云平台能力证明\n等保案例\n运维人员清单\n应急预案\nSLA承诺函",
        "source_maintenance_info": "来源：参考模板库\n维护人：云平台解决方案组\n适用：云资源与运维类项目",
    },
    {
        "basic_info": "医院信息集成平台建设项目\n采购方式：公开招标\n预算区间：500万-1000万元\n适用地区：医疗行业",
        "tender_content": "建设医院数据中心、集成平台、主数据管理、统一接口服务和运营分析驾驶舱。",
        "reference_points": "参考医疗系统接口、停机窗口、数据安全、院内培训和驻场服务能力。",
        "scoring_rules": "技术方案45分，医疗案例20分，服务团队15分，报价20分。",
        "risk_tags": "接口复杂风险\n医疗数据安全风险\n上线窗口风险",
        "material_checklist": "医疗信息化案例\n接口清单响应表\n数据安全方案\n驻场人员简历\n培训计划",
        "source_maintenance_info": "来源：参考模板库\n维护人：医疗行业售前组\n适用：医院信息化项目",
    },
    {
        "basic_info": "网络安全态势感知平台项目\n采购方式：竞争性磋商\n预算区间：300万-700万元\n适用地区：政企单位",
        "tender_content": "建设资产发现、日志采集、威胁检测、安全告警、事件处置和安全运营服务体系。",
        "reference_points": "参考日志接入范围、告警准确率、等保合规、应急响应和安全服务资质。",
        "scoring_rules": "平台能力40分，安全服务25分，实施案例15分，报价20分。",
        "risk_tags": "误报漏报风险\n日志接入风险\n安全事件响应压力",
        "material_checklist": "安全服务资质\n等保案例\n平台功能截图\n应急响应预案\n安全工程师证书",
        "source_maintenance_info": "来源：参考模板库\n维护人：安全解决方案组\n适用：网络安全项目",
    },
    {
        "basic_info": "城市运行数字孪生平台项目\n采购方式：公开招标\n预算区间：800万-1500万元\n适用地区：智慧城市",
        "tender_content": "建设城市三维底座、物联感知接入、事件联动、指挥调度、专题场景和数据驾驶舱。",
        "reference_points": "参考三维引擎能力、物联接入、场景建设、数据更新机制和展示性能。",
        "scoring_rules": "平台架构35分，场景方案25分，类似案例20分，报价20分。",
        "risk_tags": "数据更新风险\n三维性能风险\n场景边界不清",
        "material_checklist": "数字孪生案例\n三维平台说明\n物联接入方案\n项目团队简历\n演示材料",
        "source_maintenance_info": "来源：参考模板库\n维护人：智慧城市事业部\n适用：城市运行与数字孪生项目",
    },
    {
        "basic_info": "工业互联网数据中台建设项目\n采购方式：公开招标\n预算区间：900万-1600万元\n适用地区：制造业",
        "tender_content": "建设工业数据采集、数据治理、指标体系、可视化分析、设备画像和AI预测应用。",
        "reference_points": "参考数据源接入、数据质量、指标模型、平台扩展性和工厂网络安全边界。",
        "scoring_rules": "数据治理35分，平台能力25分，工业案例20分，报价20分。",
        "risk_tags": "现场采集风险\n数据质量风险\n生产网络隔离风险",
        "material_checklist": "工业互联网案例\n数据治理方案\n采集网关说明\n安全隔离方案\n实施计划",
        "source_maintenance_info": "来源：参考模板库\n维护人：工业互联网团队\n适用：制造业数据项目",
    },
    {
        "basic_info": "AI智能客服平台建设项目\n采购方式：竞争性磋商\n预算区间：250万-500万元\n适用地区：政企服务",
        "tender_content": "建设知识库、智能问答、工单流转、多渠道接入、人工兜底和运营分析能力。",
        "reference_points": "参考模型安全、知识库维护、人工兜底机制、准确率验收和隐私保护。",
        "scoring_rules": "产品能力35分，知识库方案20分，服务能力20分，案例10分，报价15分。",
        "risk_tags": "回答准确率风险\n隐私数据风险\n知识库维护压力",
        "material_checklist": "产品白皮书\n知识库建设方案\n安全合规说明\n客服案例\n验收指标表",
        "source_maintenance_info": "来源：参考模板库\n维护人：AI应用组\n适用：智能客服与知识库项目",
    },
    {
        "basic_info": "企业协同办公平台升级项目\n采购方式：公开招标\n预算区间：200万-450万元\n适用地区：企业数字化",
        "tender_content": "升级门户、流程审批、移动办公、统一身份认证、消息集成和组织架构同步能力。",
        "reference_points": "参考组织同步、权限模型、移动端适配、历史流程迁移和培训计划。",
        "scoring_rules": "功能方案40分，迁移方案20分，实施团队15分，报价25分。",
        "risk_tags": "历史数据迁移风险\n权限模型风险\n用户培训风险",
        "material_checklist": "协同办公案例\n迁移方案\n权限设计说明\n培训计划\n售后服务承诺",
        "source_maintenance_info": "来源：参考模板库\n维护人：企业数字化团队\n适用：OA与门户升级项目",
    },
    {
        "basic_info": "智慧水务监测平台项目\n采购方式：公开招标\n预算区间：400万-800万元\n适用地区：水务行业",
        "tender_content": "建设水质监测、管网压力、泵站监控、告警联动、GIS展示和移动巡检管理。",
        "reference_points": "参考传感器接入、通信稳定性、GIS展示、移动巡检和数据校准机制。",
        "scoring_rules": "物联接入30分，平台功能30分，运维服务20分，报价20分。",
        "risk_tags": "设备兼容风险\n通信不稳定风险\n现场运维风险",
        "material_checklist": "物联设备清单\n平台演示材料\n水务案例\n运维巡检计划\n数据校准方案",
        "source_maintenance_info": "来源：参考模板库\n维护人：智慧水务团队\n适用：物联网监测项目",
    },
    {
        "basic_info": "智慧停车运营管理平台项目\n采购方式：公开招标\n预算区间：300万-700万元\n适用地区：城市交通",
        "tender_content": "接入停车资源、支付结算、诱导屏、运营分析、监管平台和移动端服务。",
        "reference_points": "参考设备兼容、支付安全、数据对账、运营指标和接口开放。",
        "scoring_rules": "平台功能35分，设备接入20分，运营服务20分，报价25分。",
        "risk_tags": "支付对账风险\n设备兼容风险\n运营数据准确性风险",
        "material_checklist": "停车平台案例\n支付安全说明\n设备接入清单\n运营报表样例\n接口文档",
        "source_maintenance_info": "来源：参考模板库\n维护人：交通行业团队\n适用：停车运营项目",
    },
    {
        "basic_info": "公共资源交易平台升级项目\n采购方式：公开招标\n预算区间：600万-1000万元\n适用地区：公共资源",
        "tender_content": "升级电子招投标、专家抽取、远程开标、监管留痕、CA接入和数据交换能力。",
        "reference_points": "参考合规性、电子签章、CA接入、开标稳定性和审计追溯。",
        "scoring_rules": "业务理解35分，合规安全25分，平台案例20分，报价20分。",
        "risk_tags": "合规审计风险\n远程开标稳定性风险\nCA兼容风险",
        "material_checklist": "公共资源案例\nCA接入方案\n电子签章说明\n安全审计方案\n数据交换接口",
        "source_maintenance_info": "来源：参考模板库\n维护人：电子交易团队\n适用：公共资源交易项目",
    },
    {
        "basic_info": "智慧工地监管平台项目\n采购方式：竞争性磋商\n预算区间：300万-600万元\n适用地区：住建监管",
        "tender_content": "建设实名制、扬尘监测、视频AI识别、塔吊监测、监管驾驶舱和移动巡查。",
        "reference_points": "参考设备接入、视频算法准确率、监管报表、施工现场网络条件。",
        "scoring_rules": "监管场景30分，AI能力20分，设备接入20分，运维服务15分，报价15分。",
        "risk_tags": "现场网络风险\n视频算法误判风险\n设备维护风险",
        "material_checklist": "智慧工地案例\nAI算法说明\n设备清单\n现场实施计划\n运维方案",
        "source_maintenance_info": "来源：参考模板库\n维护人：住建行业团队\n适用：工地监管项目",
    },
    {
        "basic_info": "档案数字化加工服务项目\n采购方式：竞争性磋商\n预算区间：150万-350万元\n适用地区：档案管理",
        "tender_content": "提供纸质档案扫描、OCR识别、目录著录、质检、成果移交和安全保密管理。",
        "reference_points": "参考加工场地、保密制度、质检比例、图像质量和数据移交格式。",
        "scoring_rules": "服务方案35分，质量控制25分，保密措施20分，报价20分。",
        "risk_tags": "保密风险\n质检返工风险\n交付格式不一致",
        "material_checklist": "保密承诺\n加工流程方案\n质检制度\n人员名单\n成果移交清单",
        "source_maintenance_info": "来源：参考模板库\n维护人：档案数字化团队\n适用：数字化加工服务项目",
    },
    {
        "basic_info": "企业数据安全治理项目\n采购方式：公开招标\n预算区间：500万-900万元\n适用地区：金融与大型企业",
        "tender_content": "开展数据资产梳理、分类分级、敏感数据识别、脱敏、访问控制、审计和合规评估。",
        "reference_points": "参考数据资产梳理、分类分级规则、敏感数据识别、审计留痕和制度建设。",
        "scoring_rules": "治理方法35分，安全产品25分，行业案例20分，报价20分。",
        "risk_tags": "敏感数据识别风险\n业务配合风险\n合规边界风险",
        "material_checklist": "数据安全案例\n分类分级方案\n安全产品说明\n实施计划\n合规评估报告样例",
        "source_maintenance_info": "来源：参考模板库\n维护人：数据安全团队\n适用：数据安全治理项目",
    },
    {
        "basic_info": "校园弱电系统改造工程项目\n采购方式：公开招标\n预算区间：200万-500万元\n适用地区：教育行业",
        "tender_content": "改造综合布线、视频监控、门禁广播、校园网络和机房配套，包含施工组织和售后巡检。",
        "reference_points": "参考施工周期、持证人员、材料品牌、售后巡检、质保期限和安全文明施工。",
        "scoring_rules": "施工组织30分，设备材料25分，人员资质15分，业绩10分，报价20分。",
        "risk_tags": "暑期工期风险\n材料品牌偏离风险\n现场施工安全风险",
        "material_checklist": "施工资质\n人员证书\n设备品牌响应表\n施工组织方案\n售后服务承诺",
        "source_maintenance_info": "来源：参考模板库\n维护人：教育行业团队\n适用：弱电集成与校园改造项目",
    },
]


# Additional industry coverage. Together with the curated templates above this
# produces 55 managed reference tenders and 56 managed contract templates.
# Historical migrations contribute a few original rows, keeping the visible
# database catalogue within the requested 50-60 range without deleting data.
# catalogue data-driven makes it easy to review and extend without duplicating
# large blocks of boilerplate tender text.
ADDITIONAL_REFERENCE_BLUEPRINTS = [
    ("政务数据共享交换平台", "政务信息化", "数字政府", "北京", "政务服务和大数据管理局", 760, "数据共享、接口治理、目录管理"),
    ("城市一网统管指挥平台", "智慧城市", "城市治理", "上海", "城市运行管理中心", 1380, "一网统管、事件处置、指挥调度"),
    ("基层社会治理网格化平台", "软件信息化", "社会治理", "浙江", "社会治理中心", 520, "网格治理、移动巡查、事件闭环"),
    ("行政审批电子证照系统", "软件信息化", "数字政府", "福建", "行政审批服务局", 410, "电子证照、电子签章、数据共享"),
    ("政务热线智能客服平台", "人工智能", "政务服务", "四川", "政务服务热线中心", 360, "智能客服、知识库、工单分析"),
    ("全民健康信息平台升级", "医疗信息化", "智慧医疗", "江苏", "卫生健康委员会", 980, "健康档案、互联互通、数据治理"),
    ("医院电子病历五级改造", "医疗信息化", "智慧医疗", "山东", "三级综合医院", 680, "电子病历、临床决策、互联互通"),
    ("区域医学影像云平台", "云平台建设", "智慧医疗", "河南", "区域卫生健康中心", 860, "影像云、PACS、远程诊断"),
    ("医保智能审核系统", "人工智能", "医疗保障", "安徽", "医疗保障局", 590, "智能审核、规则引擎、基金监管"),
    ("智慧校园综合服务平台", "软件信息化", "教育信息化", "湖北", "高等院校", 450, "智慧校园、统一门户、数据中台"),
    ("职业院校实训室建设", "设备集成", "职业教育", "湖南", "职业技术学院", 720, "实训设备、教学平台、系统集成"),
    ("中小学教育专网改造", "网络集成", "教育信息化", "广东", "教育局", 630, "教育专网、网络安全、运维"),
    ("高校科研数据管理平台", "软件信息化", "高等教育", "陕西", "综合大学", 390, "科研管理、数据治理、成果管理"),
    ("智能工厂MES系统建设", "工业互联网", "智能制造", "重庆", "制造企业", 880, "MES、生产追溯、设备联网"),
    ("工业设备预测性维护平台", "人工智能", "智能制造", "辽宁", "装备制造企业", 640, "设备监测、故障预测、工业AI"),
    ("制造企业ERP升级改造", "软件信息化", "企业数字化", "广东", "制造企业", 750, "ERP、供应链、财务集成"),
    ("工业园区能耗管理平台", "物联网平台", "节能管理", "山东", "工业园区管委会", 480, "能耗监测、节能分析、物联网"),
    ("新能源场站智能运维平台", "物联网平台", "新能源", "甘肃", "新能源企业", 920, "新能源、智能运维、设备监测"),
    ("电力调度数据平台", "数据平台", "能源电力", "内蒙古", "电力企业", 1260, "电力调度、数据中台、安全生产"),
    ("燃气管网安全监测系统", "物联网平台", "城市燃气", "河北", "燃气集团", 570, "燃气监测、泄漏预警、GIS"),
    ("智慧矿山安全监管平台", "工业互联网", "矿山安全", "山西", "能源集团", 1180, "智慧矿山、安全监管、视频AI"),
    ("高速公路机电系统升级", "设备集成", "智慧交通", "江西", "高速公路运营公司", 1560, "高速公路、机电系统、收费监控"),
    ("城市公交智能调度平台", "软件信息化", "智慧交通", "广西", "公共交通集团", 690, "公交调度、车辆定位、客流分析"),
    ("轨道交通综合监控系统", "系统集成", "轨道交通", "天津", "轨道交通集团", 1880, "轨道交通、综合监控、应急联动"),
    ("港口物流数字化平台", "软件信息化", "智慧港口", "浙江", "港口集团", 1320, "港口物流、智能调度、物联网"),
    ("银行数据治理平台", "数据平台", "金融科技", "北京", "商业银行", 980, "数据治理、监管报送、数据质量"),
    ("金融机构灾备中心建设", "云平台建设", "金融科技", "上海", "金融机构", 1680, "灾备中心、业务连续性、容灾演练"),
    ("保险智能理赔系统", "人工智能", "保险科技", "深圳", "保险公司", 780, "智能理赔、OCR、反欺诈"),
    ("证券统一身份认证平台", "网络安全", "金融科技", "广东", "证券公司", 460, "身份认证、零信任、权限治理"),
    ("农业农村大数据平台", "数据平台", "数字农业", "黑龙江", "农业农村厅", 820, "农业数据、产业分析、数据治理"),
    ("高标准农田监测系统", "物联网平台", "数字农业", "河南", "农业农村局", 540, "农田监测、遥感、物联网"),
    ("农产品质量追溯平台", "软件信息化", "食品安全", "云南", "市场监督管理局", 430, "质量追溯、二维码、监管分析"),
    ("智慧文旅综合服务平台", "软件信息化", "文化旅游", "贵州", "文化和旅游局", 660, "智慧文旅、游客服务、营销分析"),
    ("博物馆数字化保护项目", "数字化加工", "文化遗产", "陕西", "博物馆", 510, "文物数字化、三维采集、数字资产"),
    ("景区智慧票务系统", "软件信息化", "文化旅游", "海南", "旅游景区", 350, "智慧票务、客流监测、支付对账"),
    ("国有企业档案数字化项目", "数字化加工", "档案管理", "北京", "国有企业", 420, "档案扫描、OCR、数据质检"),
    ("自然资源国土空间基础平台", "GIS平台", "自然资源", "四川", "自然资源厅", 1150, "国土空间、GIS、数据治理"),
    ("生态环境监测数据平台", "数据平台", "生态环保", "江苏", "生态环境厅", 890, "环境监测、数据分析、预警"),
    ("河湖长制信息管理平台", "软件信息化", "水利治理", "湖北", "水利厅", 560, "河湖治理、移动巡查、GIS"),
    ("城市排水防涝监测平台", "物联网平台", "城市治理", "福建", "住房和城乡建设局", 730, "排水防涝、监测预警、应急调度"),
    ("应急管理综合指挥平台", "智慧城市", "应急管理", "湖南", "应急管理厅", 1480, "应急指挥、融合通信、预案管理"),
    ("消防物联网远程监控平台", "物联网平台", "消防安全", "浙江", "消防救援支队", 620, "消防物联网、远程监控、告警联动"),
    ("企业安全生产风险管控平台", "软件信息化", "安全生产", "山东", "应急管理局", 580, "双重预防、隐患排查、安全生产"),
    ("数据中心基础设施运维服务", "运维服务", "信息技术服务", "广东", "政务数据中心", 680, "数据中心、驻场运维、SLA"),
    ("桌面终端与网络运维服务", "运维服务", "信息技术服务", "江苏", "事业单位", 320, "桌面运维、网络运维、服务台"),
]


def _build_additional_templates():
    references = []
    contracts = []
    for index, (name, project_type, industry, region, organization, budget, tags) in enumerate(
        ADDITIONAL_REFERENCE_BLUEPRINTS, start=1
    ):
        title = f"{name}参考标书"
        reference_points = (
            f"重点核验{tags.replace('、', '、')}相关能力、项目负责人经验、同类业绩、实施计划、"
            "数据安全、验收指标、售后服务和关键人员稳定性。"
        )
        source_text = (
            f"第一章 招标公告：{name}，预算约{budget}万元，采购方式为公开招标。\n"
            f"第二章 投标人须知：投标人应具备{industry}领域履约能力及近三年类似项目业绩。\n"
            f"第三章 技术需求：建设范围包括{tags}，要求提供完整架构、实施与迁移方案。\n"
            "第四章 商务要求：明确工期、付款节点、人员投入、知识产权、保密和质保责任。\n"
            "第五章 评分办法：技术方案40分，团队与业绩20分，服务保障10分，报价30分。\n"
            "第六章 验收要求：按功能、性能、安全、数据质量和用户培训成果分阶段验收。"
        )
        references.append({
            "title": title,
            "project_type": project_type,
            "industry": industry,
            "region": region,
            "issuing_organization": f"某{organization}",
            "budget_amount": budget * 10000,
            "summary": f"适用于{name}及同类{industry}项目的资格、技术、商务和评分条款参考。",
            "reference_points": reference_points,
            "source_text": source_text,
            "tags": tags,
        })
        contracts.append({
            "basic_info": f"{name}\n项目类型：{project_type}\n行业：{industry}\n地区：{region}\n预算：{budget}万元",
            "tender_content": source_text,
            "reference_points": reference_points,
            "scoring_rules": "技术方案40分；团队配置10分；同类业绩10分；服务保障10分；投标报价30分。",
            "risk_tags": "资格条件偏离风险\n关键技术参数偏离风险\n工期与人员投入风险\n数据安全与验收风险\n付款及质保责任风险",
            "material_checklist": "营业执照\n资质与体系证书\n项目负责人简历及证明\n同类项目合同与验收证明\n技术实施方案\n服务与质保承诺\n报价明细表",
            "source_maintenance_info": f"来源：策标行业参考模板库\n模板编号：CB-{index + 15:03d}\n适用：{industry}/{project_type}",
        })
    return references, contracts


_ADDITIONAL_REFERENCES, _ADDITIONAL_CONTRACTS = _build_additional_templates()
REFERENCE_TEMPLATES.extend(_ADDITIONAL_REFERENCES)
CONTRACT_TEMPLATES.extend(_ADDITIONAL_CONTRACTS[:41])


class Command(BaseCommand):
    help = "Seed reusable tender reference templates and contract-style bid templates."

    def handle(self, *args, **options):
        reference_fields = [
            "project_type", "industry", "region", "issuing_organization", "budget_amount",
            "published_at", "summary", "reference_points", "source_text", "tags", "is_featured",
        ]
        existing_references = {
            item.title: item
            for item in TenderReference.objects.filter(
                title__in=[template["title"] for template in REFERENCE_TEMPLATES]
            )
        }
        references_to_create = []
        references_to_update = []
        for index, template in enumerate(REFERENCE_TEMPLATES, start=1):
            values = {**template, "published_at": None, "is_featured": index <= 10}
            reference = existing_references.get(template["title"])
            if reference is None:
                references_to_create.append(TenderReference(**values))
                continue
            for field in reference_fields:
                setattr(reference, field, values[field])
            references_to_update.append(reference)

        TenderReference.objects.bulk_create(references_to_create, batch_size=100)
        if references_to_update:
            TenderReference.objects.bulk_update(references_to_update, reference_fields, batch_size=100)

        contract_fields = [
            "tender_content", "reference_points", "scoring_rules", "risk_tags",
            "material_checklist", "source_maintenance_info",
        ]
        existing_contracts = {
            item.basic_info: item
            for item in Contract.objects.filter(
                basic_info__in=[template["basic_info"] for template in CONTRACT_TEMPLATES]
            )
        }
        contracts_to_create = []
        contracts_to_update = []
        for template in CONTRACT_TEMPLATES:
            contract = existing_contracts.get(template["basic_info"])
            if contract is None:
                contracts_to_create.append(Contract(**template))
                continue
            for field in contract_fields:
                setattr(contract, field, template[field])
            contracts_to_update.append(contract)

        Contract.objects.bulk_create(contracts_to_create, batch_size=100)
        if contracts_to_update:
            Contract.objects.bulk_update(contracts_to_update, contract_fields, batch_size=100)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(REFERENCE_TEMPLATES)} tender references and {len(CONTRACT_TEMPLATES)} contract templates."
            )
        )
