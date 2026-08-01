from django.db import migrations, models


CASES = [
    ('智慧医院一体化平台建设项目', '医疗', '江苏', 2026, 28000000, '华康数字科技有限公司', 18, 26500000, 26180000, '电子病历、数据中心、影像云与互联互通平台建设。', '智慧医院、数据平台、医疗信息化'),
    ('区域教育数字基座建设项目', '教育', '浙江', 2026, 16800000, '启明教育科技有限公司', 14, 15700000, 15460000, '建设区域教育数据中台、统一身份和教学应用中心。', '教育数字化、数据中台、统一门户'),
    ('城市运行一网统管平台项目', '政府', '上海', 2026, 42000000, '城智科技股份有限公司', 22, 39800000, 39280000, '建设城市运行中心、事件闭环和多部门协同指挥体系。', '一网统管、智慧城市、指挥调度'),
    ('政务大模型应用服务平台', 'AI', '北京', 2026, 19500000, '智政云科技有限公司', 16, 18100000, 17850000, '建设政务知识库、智能问答和公文辅助应用。', '大模型、知识库、政务AI'),
    ('工业互联网生产协同平台', '软件', '广东', 2026, 12600000, '数制融合科技有限公司', 11, 11800000, 11620000, '建设MES集成、设备联网和生产质量追溯平台。', '工业互联网、MES、系统集成'),
    ('公共建筑智能化改造工程', '建筑', '湖北', 2026, 33600000, '中联智能工程有限公司', 25, 31400000, 30960000, '完成综合布线、楼宇自控、安防和机房配套建设。', '智能建筑、弱电工程、机房'),
    ('全民健康信息平台升级项目', '医疗', '山东', 2025, 23800000, '云医信息股份有限公司', 15, 22400000, 22050000, '升级居民健康档案、数据治理和跨院互联互通能力。', '健康档案、数据治理、互联互通'),
    ('智慧校园综合管理平台', '教育', '四川', 2025, 9800000, '校园云科技有限公司', 13, 9100000, 8980000, '建设统一门户、移动校园、数据中心和业务协同平台。', '智慧校园、移动端、数据中心'),
    ('省级政务云扩容服务项目', '政府', '福建', 2025, 56000000, '东南云计算有限公司', 20, 52900000, 51800000, '提供云资源扩容、迁移、灾备和安全运维服务。', '政务云、灾备、等保'),
    ('企业知识智能问答平台', 'AI', '深圳', 2025, 7600000, '深智软件有限公司', 9, 7100000, 6960000, '建设企业知识库、检索增强生成与智能客服平台。', '知识库、RAG、智能客服'),
    ('国企财务共享平台升级', '软件', '北京', 2025, 14800000, '融信软件科技有限公司', 12, 13700000, 13480000, '升级财务共享、预算管理和数据分析能力。', '财务共享、数据分析、ERP'),
    ('产业园智慧工地监管项目', '建筑', '安徽', 2025, 11200000, '筑联科技有限公司', 17, 10300000, 10120000, '建设实名制、视频AI、扬尘监测和安全监管平台。', '智慧工地、视频AI、工程监管'),
]


def seed_cases(apps, schema_editor):
    HistoricalBidCase = apps.get_model('tenders', 'HistoricalBidCase')
    for row in CASES:
        HistoricalBidCase.objects.update_or_create(
            title=row[0],
            defaults={
                'industry': row[1], 'region': row[2], 'year': row[3], 'budget_amount': row[4],
                'winning_company': row[5], 'participant_count': row[6], 'average_bid_amount': row[7],
                'winning_bid_amount': row[8], 'summary': row[9], 'tags': row[10],
            },
        )


class Migration(migrations.Migration):
    dependencies = [('tenders', '0012_projecttask_assignee_name_projecttask_remind_at_and_more')]
    operations = [
        migrations.CreateModel(
            name='HistoricalBidCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=220, unique=True, verbose_name='历史项目名称')),
                ('industry', models.CharField(db_index=True, max_length=80, verbose_name='所属行业')),
                ('region', models.CharField(blank=True, max_length=80, verbose_name='项目地区')),
                ('year', models.PositiveSmallIntegerField(db_index=True, verbose_name='招标年份')),
                ('budget_amount', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='项目预算')),
                ('winning_company', models.CharField(max_length=180, verbose_name='中标单位')),
                ('participant_count', models.PositiveSmallIntegerField(default=0, verbose_name='竞争企业数量')),
                ('average_bid_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='平均报价')),
                ('winning_bid_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='中标金额')),
                ('summary', models.TextField(blank=True, verbose_name='项目摘要')),
                ('tags', models.CharField(blank=True, max_length=255, verbose_name='标签')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={'verbose_name': '历史招标案例', 'verbose_name_plural': '历史招标案例', 'ordering': ['-year', '-budget_amount', '-id']},
        ),
        migrations.RunPython(seed_cases, migrations.RunPython.noop),
    ]
