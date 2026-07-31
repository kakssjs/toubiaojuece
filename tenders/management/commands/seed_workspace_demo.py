from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from tenders.models import (
    AnalysisReport,
    CompanyProfile,
    ProjectExperience,
    ProjectNote,
    Qualification,
    TenderProject,
)


COMPANIES = [
    {
        "name": "小苏科技有限公司",
        "main_business": "AI应用开发、政企信息化系统集成、数据治理与智能分析平台建设",
        "service_regions": "全国、江苏、上海、浙江、广东",
        "max_project_amount": "15000000",
        "forbidden_conditions": "不接受纯垫资项目；不承接无明确验收标准或付款周期超过18个月的项目",
        "qualifications": [
            ("ISO9001质量管理体系认证", "ISO-2026-001"),
            ("信息安全管理体系认证", "ISMS-2026-008"),
            ("软件企业能力证明", "SOFT-2026-021"),
            ("CMMI三级软件能力证明", "CMMI3-2026-013"),
        ],
        "experiences": [
            ("智慧园区综合管理平台", "园区数字化", "3600000", "某高新区管委会"),
            ("政企智能客服与知识库平台", "AI应用", "2800000", "某政务服务中心"),
            ("公共服务数据驾驶舱", "数据可视化", "4200000", "某区大数据局"),
        ],
    },
    {
        "name": "云衡数据科技有限公司",
        "main_business": "云平台建设、数据中台、工业互联网、网络安全与运维服务",
        "service_regions": "华东、华中、华南",
        "max_project_amount": "20000000",
        "forbidden_conditions": "不承接要求源码完全转让且无知识产权边界的项目",
        "qualifications": [
            ("ISO27001信息安全管理体系认证", "ISO27001-2026-019"),
            ("云服务能力评估证书", "CLOUD-2026-006"),
            ("ITSS运维服务能力三级", "ITSS3-2026-010"),
        ],
        "experiences": [
            ("电子政务云资源池扩容", "政务云", "9200000", "某市大数据中心"),
            ("工业互联网数据中台", "制造业数字化", "11800000", "某智能制造集团"),
            ("网络安全态势感知平台", "网络安全", "6500000", "某市网信中心"),
        ],
    },
    {
        "name": "星澜智能工程有限公司",
        "main_business": "弱电集成、物联网平台、智慧工地、智慧水务和校园信息化工程",
        "service_regions": "江苏、安徽、湖北、河南、四川",
        "max_project_amount": "12000000",
        "forbidden_conditions": "不承接无法进场踏勘且设备品牌锁定不透明的项目",
        "qualifications": [
            ("电子与智能化工程专业承包二级", "EIC-2026-088"),
            ("安全生产许可证", "SAFE-2026-031"),
            ("安防工程企业能力证书", "SEC-2026-056"),
        ],
        "experiences": [
            ("校园弱电系统改造工程", "教育信息化", "3800000", "某职业技术学院"),
            ("智慧工地监管平台", "住建监管", "5200000", "某住建局"),
            ("智慧水务监测平台", "智慧水务", "6200000", "某水务集团"),
        ],
    },
]


PROJECTS = [
    ("智慧园区综合管理平台建设项目", "小苏科技有限公司", "软件信息化", "江苏", 4800000, AnalysisReport.Decision.RECOMMENDED, 88, "低"),
    ("电子政务云资源池扩容及运维服务项目", "云衡数据科技有限公司", "云平台建设", "上海", 9200000, AnalysisReport.Decision.RECOMMENDED, 84, "中"),
    ("AI智能客服平台建设项目", "小苏科技有限公司", "AI应用平台", "浙江", 3200000, AnalysisReport.Decision.RECOMMENDED, 82, "低"),
    ("工业互联网数据中台建设项目", "云衡数据科技有限公司", "工业互联网", "山东", 11800000, AnalysisReport.Decision.CAUTIOUS, 76, "中"),
    ("医院信息集成平台与数据中心建设项目", "小苏科技有限公司", "医疗信息化", "广东", 7800000, AnalysisReport.Decision.CAUTIOUS, 73, "中"),
    ("网络安全态势感知平台项目", "云衡数据科技有限公司", "网络安全", "浙江", 6500000, AnalysisReport.Decision.CAUTIOUS, 71, "高"),
    ("智慧水务监测平台项目", "星澜智能工程有限公司", "物联网平台", "湖北", 6200000, AnalysisReport.Decision.RECOMMENDED, 86, "低"),
    ("智慧工地监管平台项目", "星澜智能工程有限公司", "工程监管", "河南", 5200000, AnalysisReport.Decision.CAUTIOUS, 75, "中"),
    ("公共资源交易平台升级项目", "云衡数据科技有限公司", "电子交易", "重庆", 8600000, AnalysisReport.Decision.CAUTIOUS, 69, "高"),
    ("校园弱电系统改造工程项目", "星澜智能工程有限公司", "弱电集成", "安徽", 3800000, AnalysisReport.Decision.RECOMMENDED, 81, "中"),
    ("城市运行数字孪生平台建设项目", "云衡数据科技有限公司", "智慧城市", "四川", 12800000, AnalysisReport.Decision.NOT_RECOMMENDED, 52, "高"),
    ("档案数字化加工服务项目", "星澜智能工程有限公司", "数字化服务", "江苏", 2600000, AnalysisReport.Decision.NEEDS_REVIEW, 64, "中"),
]


class Command(BaseCommand):
    help = "Seed complete demo data for the workspace, company profile, project board, reports, and templates."

    def handle(self, *args, **options):
        call_command("seed_reference_templates", verbosity=0)

        companies = self._seed_companies()
        project_count = self._seed_projects(companies)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(companies)} companies and {project_count} workspace projects with reports."
            )
        )

    def _seed_companies(self):
        companies = {}
        for item in COMPANIES:
            company, _ = CompanyProfile.objects.update_or_create(
                name=item["name"],
                defaults={
                    "main_business": item["main_business"],
                    "service_regions": item["service_regions"],
                    "max_project_amount": Decimal(item["max_project_amount"]),
                    "forbidden_conditions": item["forbidden_conditions"],
                },
            )
            company.qualifications.all().delete()
            for name, cert_no in item["qualifications"]:
                Qualification.objects.create(company=company, name=name, certificate_no=cert_no)

            company.experiences.all().delete()
            for name, industry, amount, client_name in item["experiences"]:
                ProjectExperience.objects.create(
                    company=company,
                    name=name,
                    industry=industry,
                    amount=Decimal(amount),
                    client_name=client_name,
                    description=f"{client_name} {name}实施与交付经验。",
                )

            companies[company.name] = company
        return companies

    def _seed_projects(self, companies):
        count = 0
        base_deadline = timezone.now() + timedelta(days=10)
        for index, row in enumerate(PROJECTS):
            name, company_name, project_type, region, budget, decision, score, risk_level = row
            company = companies[company_name]
            project, _ = TenderProject.objects.update_or_create(
                name=name,
                defaults={
                    "company": company,
                    "procurement_method": "公开招标" if index % 3 != 1 else "竞争性磋商",
                    "project_type": project_type,
                    "region": region,
                    "budget_amount": Decimal(str(budget)),
                    "deadline": base_deadline + timedelta(days=index * 3),
                    "source_text": self._source_text(name, project_type, risk_level),
                    "status": TenderProject.Status.ANALYZED,
                },
            )

            report_payload = self._report_payload(name, company, project_type, risk_level, decision, score)
            AnalysisReport.objects.update_or_create(
                tender_project=project,
                defaults={
                    "decision": decision,
                    "match_score": score,
                    "summary": report_payload["decision_reason"],
                    "risks": report_payload["risks"],
                    "missing_materials": report_payload["qualification_match"]["missing"],
                    "next_actions": report_payload["next_actions"],
                    "raw_report": report_payload,
                },
            )
            if not project.notes.exists():
                ProjectNote.objects.create(
                    tender_project=project,
                    note_type=ProjectNote.NoteType.SYSTEM,
                    content="系统初始化演示项目，已生成基础分析报告。",
                    operator_name="系统",
                )
            count += 1
        return count

    def _source_text(self, name, project_type, risk_level):
        return (
            f"{name}\n项目类型：{project_type}\n资格要求：具备相关资质、同类项目业绩和稳定实施团队。\n"
            f"评分规则：技术方案、实施团队、同类业绩、报价和服务承诺综合评分。\n风险等级参考：{risk_level}。"
        )

    def _report_payload(self, name, company, project_type, risk_level, decision, score):
        missing = [] if score >= 80 else ["原厂授权函", "项目经理社保证明"][: 1 if score >= 70 else 2]
        risk_map = {
            "高": [
                {"type": "商务风险", "level": "高", "description": "付款周期或验收条件需要重点复核。"},
                {"type": "材料风险", "level": "中", "description": "部分强制材料需在投标前补齐。"},
            ],
            "中": [{"type": "交付风险", "level": "中", "description": "实施周期较紧，建议提前锁定项目团队。"}],
            "低": [{"type": "提示", "level": "低", "description": "常规材料齐备后可进入投标准备。"}],
        }
        decision_label = dict(AnalysisReport.Decision.choices)[decision]
        return {
            "project_name": name,
            "procurement_method": "公开招标",
            "project_type": project_type,
            "match_score": score,
            "decision": decision_label,
            "decision_reason": f"{company.name}与{project_type}方向匹配度为{score}分，建议按“{decision_label}”推进。",
            "qualification_match": {
                "status": "matched" if not missing else "partial",
                "score": max(score - 4, 0),
                "matched": [item.name for item in company.qualifications.all()[:3]],
                "missing": missing,
            },
            "experience_match": {
                "score": min(score + 3, 100),
                "summary": "已找到可支撑本项目的同类业绩。",
                "matched_cases": [item.name for item in company.experiences.all()[:2]],
            },
            "risks": risk_map[risk_level],
            "material_checklist": [
                {"category": "资格材料", "name": "营业执照", "status": "required"},
                {"category": "资质证书", "name": "体系认证或行业资质", "status": "required"},
                {"category": "业绩材料", "name": "同类项目合同与验收证明", "status": "required"},
                {"category": "商务材料", "name": "报价明细与服务承诺", "status": "required"},
            ],
            "next_actions": [
                "确认报名截止时间和保证金要求",
                "复核评分办法中对资质、业绩和人员的硬性要求",
                "安排投标负责人完善材料清单",
            ],
            "agent_trace": [
                {"agent": "信息抽取Agent", "status": "completed"},
                {"agent": "资质匹配Agent", "status": "completed"},
                {"agent": "风险分析Agent", "status": "completed"},
                {"agent": "投标决策Agent", "status": "completed"},
            ],
        }
