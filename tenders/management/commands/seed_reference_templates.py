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
        "title": "校园弱电系统改造工程参考标书",
        "project_type": "弱电集成",
        "industry": "教育信息化",
        "region": "浙江",
        "issuing_organization": "某职业技术学院",
        "budget_amount": 2650000,
        "summary": "适合参考综合布线、视频监控、门禁、广播、校园网络改造项目。",
        "reference_points": "重点关注施工周期、人员持证、材料品牌、售后巡检、质保期限。",
        "source_text": "第一章 工程概况\n第二章 施工技术要求\n第三章 设备材料清单\n第四章 验收及售后要求",
        "tags": "弱电、校园、施工组织",
    },
    {
        "title": "医院信息集成平台与数据中心参考标书",
        "project_type": "医疗信息化",
        "industry": "智慧医疗",
        "region": "广东",
        "issuing_organization": "某三级医院",
        "budget_amount": 7800000,
        "summary": "适合参考HIS、EMR、LIS、PACS等系统集成和院内数据中心建设项目。",
        "reference_points": "重点关注接口标准、数据治理、院内停机窗口、医疗数据安全和驻场服务。",
        "source_text": "第一章 招标范围\n第二章 医疗数据标准\n第三章 系统接口要求\n第四章 培训与运维\n第五章 评分细则",
        "tags": "医疗信息化、数据中心、系统集成",
    },
    {
        "title": "工业互联网数据中台建设参考标书",
        "project_type": "数据中台",
        "industry": "工业互联网",
        "region": "浙江",
        "issuing_organization": "某制造业集团",
        "budget_amount": 12600000,
        "summary": "适合参考工业数据采集、治理、指标体系、可视化分析和AI预测应用项目。",
        "reference_points": "重点关注数据源接入、数据质量、指标模型、平台扩展性和安全边界。",
        "source_text": "第一章 项目背景\n第二章 数据治理要求\n第三章 平台能力要求\n第四章 集成接口\n第五章 交付验收",
        "tags": "数据中台、工业互联网、数据治理",
    },
    {
        "title": "城市运行数字孪生平台参考标书",
        "project_type": "数字孪生",
        "industry": "智慧城市",
        "region": "北京",
        "issuing_organization": "某城市运行管理中心",
        "budget_amount": 9800000,
        "summary": "适合参考城市运行感知、三维可视化、事件联动、指挥调度类项目。",
        "reference_points": "重点关注三维底座、物联感知接入、事件闭环、可视化性能和数据更新机制。",
        "source_text": "第一章 建设目标\n第二章 数字孪生底座\n第三章 物联感知接入\n第四章 指挥调度场景\n第五章 运维保障",
        "tags": "数字孪生、智慧城市、物联网",
    },
    {
        "title": "网络安全态势感知平台参考标书",
        "project_type": "网络安全",
        "industry": "安全运营",
        "region": "四川",
        "issuing_organization": "某政务单位",
        "budget_amount": 5600000,
        "summary": "适合参考日志采集、安全告警、资产画像、威胁分析和安全运营项目。",
        "reference_points": "重点关注日志接入范围、告警准确率、等保合规、应急响应和安全服务团队。",
        "source_text": "第一章 安全建设背景\n第二章 态势感知平台能力\n第三章 安全运营服务\n第四章 应急响应要求\n第五章 评分办法",
        "tags": "网络安全、态势感知、SOC",
    },
    {
        "title": "政企运维服务外包参考标书",
        "project_type": "运维服务",
        "industry": "IT服务",
        "region": "全国",
        "issuing_organization": "某大型集团",
        "budget_amount": 3600000,
        "summary": "适合参考桌面运维、系统运维、网络运维、巡检、SLA和驻场服务项目。",
        "reference_points": "重点关注响应时间、驻场人数、服务报告、重大故障处置和绩效考核。",
        "source_text": "第一章 服务范围\n第二章 服务级别协议\n第三章 驻场人员要求\n第四章 考核办法\n第五章 报价要求",
        "tags": "运维服务、SLA、驻场",
    },
    {
        "title": "AI智能客服平台建设参考标书",
        "project_type": "AI应用平台",
        "industry": "政企服务",
        "region": "山东",
        "issuing_organization": "某公共服务中心",
        "budget_amount": 4200000,
        "summary": "适合参考知识库、智能问答、工单流转、多渠道接入和运营分析项目。",
        "reference_points": "重点关注模型安全、知识库维护、人工兜底机制、准确率验收和隐私保护。",
        "source_text": "第一章 项目需求\n第二章 智能问答能力\n第三章 知识库建设\n第四章 数据安全\n第五章 验收指标",
        "tags": "AI客服、知识库、智能问答",
    },
    {
        "title": "企业协同办公平台升级参考标书",
        "project_type": "办公协同",
        "industry": "企业数字化",
        "region": "福建",
        "issuing_organization": "某国有企业",
        "budget_amount": 3100000,
        "summary": "适合参考门户、流程审批、移动办公、统一身份认证和消息集成项目。",
        "reference_points": "重点关注组织架构同步、权限模型、移动端适配、历史流程迁移和培训计划。",
        "source_text": "第一章 建设内容\n第二章 协同办公功能\n第三章 统一身份认证\n第四章 数据迁移\n第五章 培训服务",
        "tags": "办公协同、流程审批、门户",
    },
    {
        "title": "智慧水务监测平台参考标书",
        "project_type": "物联网平台",
        "industry": "智慧水务",
        "region": "湖北",
        "issuing_organization": "某水务集团",
        "budget_amount": 6800000,
        "summary": "适合参考水质监测、管网压力、泵站监控、告警联动和移动巡检项目。",
        "reference_points": "重点关注传感器接入、通信稳定性、GIS展示、移动端巡检和数据校准。",
        "source_text": "第一章 项目概况\n第二章 感知设备接入\n第三章 平台功能\n第四章 巡检管理\n第五章 运维要求",
        "tags": "智慧水务、物联网、GIS",
    },
    {
        "title": "智慧停车运营管理平台参考标书",
        "project_type": "智慧交通",
        "industry": "城市交通",
        "region": "重庆",
        "issuing_organization": "某城市停车公司",
        "budget_amount": 5200000,
        "summary": "适合参考停车资源接入、支付结算、诱导屏、运营分析和监管平台项目。",
        "reference_points": "重点关注设备兼容、支付安全、数据对账、运营指标和接口开放。",
        "source_text": "第一章 项目范围\n第二章 停车设备接入\n第三章 支付与结算\n第四章 运营分析\n第五章 平台验收",
        "tags": "智慧停车、支付、交通",
    },
    {
        "title": "公共资源交易平台升级参考标书",
        "project_type": "电子交易",
        "industry": "公共资源",
        "region": "安徽",
        "issuing_organization": "某公共资源交易中心",
        "budget_amount": 8800000,
        "summary": "适合参考电子招投标、专家抽取、远程开标、监管留痕和数据交换项目。",
        "reference_points": "重点关注合规性、电子签章、CA接入、开标稳定性和审计追溯。",
        "source_text": "第一章 建设目标\n第二章 交易业务流程\n第三章 远程开标\n第四章 安全与合规\n第五章 数据交换",
        "tags": "电子招投标、公共资源、远程开标",
    },
    {
        "title": "智慧工地监管平台参考标书",
        "project_type": "智慧工地",
        "industry": "住建监管",
        "region": "河南",
        "issuing_organization": "某住建局",
        "budget_amount": 4500000,
        "summary": "适合参考实名制、扬尘监测、视频AI识别、塔吊监测和监管驾驶舱项目。",
        "reference_points": "重点关注设备接入、视频算法准确率、监管报表、施工现场网络条件。",
        "source_text": "第一章 监管目标\n第二章 工地感知设备\n第三章 AI识别能力\n第四章 数据驾驶舱\n第五章 运维服务",
        "tags": "智慧工地、视频AI、监管",
    },
    {
        "title": "档案数字化加工服务参考标书",
        "project_type": "数字化服务",
        "industry": "档案管理",
        "region": "江西",
        "issuing_organization": "某档案馆",
        "budget_amount": 2400000,
        "summary": "适合参考纸质档案扫描、OCR识别、目录著录、质检和安全保密项目。",
        "reference_points": "重点关注加工场地、保密制度、质检比例、图像质量和数据移交格式。",
        "source_text": "第一章 服务内容\n第二章 数字化加工规范\n第三章 质量检查\n第四章 保密要求\n第五章 成果交付",
        "tags": "档案数字化、OCR、保密",
    },
    {
        "title": "企业数据安全治理参考标书",
        "project_type": "数据安全",
        "industry": "安全合规",
        "region": "深圳",
        "issuing_organization": "某金融科技公司",
        "budget_amount": 7400000,
        "summary": "适合参考数据分类分级、脱敏、审计、访问控制和合规评估项目。",
        "reference_points": "重点关注数据资产梳理、分类分级规则、敏感数据识别、审计留痕和制度建设。",
        "source_text": "第一章 数据安全目标\n第二章 分类分级\n第三章 脱敏与审计\n第四章 合规评估\n第五章 运营服务",
        "tags": "数据安全、分类分级、审计",
    },
]


CONTRACT_TEMPLATES = [
    {
        "basic_info": "智慧园区综合管理平台模板\n采购方式：公开招标\n预算区间：300万-800万元\n适用地区：全国",
        "tender_content": "建设园区数字底座、企业服务门户、招商管理、物业服务、可视化驾驶舱和移动端应用。",
        "reference_points": "重点参考项目经理资历、实施团队、原厂授权、同类园区案例、验收里程碑。",
        "scoring_rules": "技术方案50分，实施团队15分，同类业绩15分，商务报价20分。",
        "risk_tags": "驻场服务风险\n原厂授权风险\n跨系统接口风险",
        "material_checklist": "营业执照\nISO9001\nCMMI或软件能力证明\n同类业绩合同\n项目经理简历\n原厂授权函",
        "source_maintenance_info": "来源：参考模板库\n维护人：投标管理部\n适用：软件平台类项目",
    },
    {
        "basic_info": "政务云资源池扩容模板\n采购方式：公开招标\n预算区间：800万-1500万元\n适用地区：政务行业",
        "tender_content": "扩容计算、存储、网络与安全资源，完善灾备、监控、日志审计、等保整改和运维响应机制。",
        "reference_points": "重点参考SLA、等保三级、资源迁移、割接窗口、应急演练和驻场值守。",
        "scoring_rules": "技术能力45分，安全合规20分，运维服务20分，报价15分。",
        "risk_tags": "割接失败风险\n等保合规风险\n7x24运维压力",
        "material_checklist": "云平台能力证明\n等保案例\n运维人员清单\n应急预案\nSLA承诺函",
        "source_maintenance_info": "来源：参考模板库\n维护人：云平台解决方案组\n适用：云资源与运维类项目",
    },
    {
        "basic_info": "医院信息集成平台模板\n采购方式：公开招标\n预算区间：500万-1000万元\n适用地区：医疗行业",
        "tender_content": "建设医院数据中心、集成平台、主数据管理、统一接口服务和运营分析驾驶舱。",
        "reference_points": "重点参考医疗系统接口、停机窗口、数据安全、院内培训和驻场服务能力。",
        "scoring_rules": "技术方案45分，医疗案例20分，服务团队15分，报价20分。",
        "risk_tags": "接口复杂风险\n医疗数据安全风险\n上线窗口风险",
        "material_checklist": "医疗信息化案例\n接口清单响应表\n数据安全方案\n驻场人员简历\n培训计划",
        "source_maintenance_info": "来源：参考模板库\n维护人：医疗行业售前组\n适用：医院信息化项目",
    },
    {
        "basic_info": "网络安全态势感知平台模板\n采购方式：竞争性磋商\n预算区间：300万-700万元\n适用地区：政企单位",
        "tender_content": "建设资产发现、日志采集、威胁检测、安全告警、事件处置和安全运营服务体系。",
        "reference_points": "重点参考日志接入范围、告警准确率、等保合规、应急响应和安全服务资质。",
        "scoring_rules": "平台能力40分，安全服务25分，实施案例15分，报价20分。",
        "risk_tags": "误报漏报风险\n日志接入风险\n安全事件响应压力",
        "material_checklist": "安全服务资质\n等保案例\n平台功能截图\n应急响应预案\n安全工程师证书",
        "source_maintenance_info": "来源：参考模板库\n维护人：安全解决方案组\n适用：网络安全项目",
    },
    {
        "basic_info": "数字孪生城市运行平台模板\n采购方式：公开招标\n预算区间：800万-1500万元\n适用地区：智慧城市",
        "tender_content": "建设城市三维底座、物联感知接入、事件联动、指挥调度、专题场景和数据驾驶舱。",
        "reference_points": "重点参考三维引擎能力、物联接入、场景建设、数据更新机制和展示性能。",
        "scoring_rules": "平台架构35分，场景方案25分，类似案例20分，报价20分。",
        "risk_tags": "数据更新风险\n三维性能风险\n场景边界不清",
        "material_checklist": "数字孪生案例\n三维平台说明\n物联接入方案\n项目团队简历\n演示材料",
        "source_maintenance_info": "来源：参考模板库\n维护人：智慧城市事业部\n适用：城市运行与数字孪生项目",
    },
]


class Command(BaseCommand):
    help = "Seed reusable tender reference templates and contract-style bid templates."

    def handle(self, *args, **options):
        reference_count = 0
        contract_count = 0

        for index, template in enumerate(REFERENCE_TEMPLATES, start=1):
            defaults = {
                **template,
                "published_at": None,
                "is_featured": index <= 10,
            }
            TenderReference.objects.update_or_create(
                title=template["title"],
                defaults=defaults,
            )
            reference_count += 1

        for template in CONTRACT_TEMPLATES:
            Contract.objects.update_or_create(
                basic_info=template["basic_info"],
                defaults=template,
            )
            contract_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {reference_count} tender references and {contract_count} contract templates."
            )
        )
