from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

ARTICLES = [
    ('如何用评分办法反推技术标目录', '招投标知识', '从分值、评分证据和响应位置三个维度建立可检查的技术标目录。', True),
    ('2026政务数字化项目趋势观察', '行业分析', '梳理数据治理、人工智能、安全合规与信创适配的重点机会。', True),
    ('资格审查中最容易忽略的8个细节', '招投标知识', '覆盖证书有效期、授权链、签章、社保和业绩证明等常见问题。', False),
    ('智慧医院项目投标复盘方法', '案例分享', '从需求拆解、接口边界、实施组织与验收指标进行结构化复盘。', True),
    ('价格评分公式与报价策略入门', '投标技巧', '理解基准价、偏离率和价格分之间的关系，避免盲目低价。', False),
    ('AI如何辅助标书终稿检查', 'AI投标', '使用AI检查缺项、偏离参数、前后矛盾与格式问题的实践流程。', False),
]
POSTS = [
    ('智慧城市项目的类似业绩如何组织更有说服力？', '项目经验', '投标顾问林老师', '大家通常如何呈现跨地区、不同金额的类似业绩？欢迎分享结构。', 328, 12, True),
    ('技术方案页数很多，如何保证评分点不遗漏', '投标技巧', '方案经理周工', '分享一个评分点矩阵与章节双向索引的方法。', 246, 8, True),
    ('近期医疗信息化项目更关注哪些能力？', '行业机会', '医疗行业观察员', '从互联互通、数据治理和安全合规三个方向讨论。', 189, 6, False),
]

def seed_community(apps, schema_editor):
    Article=apps.get_model('tenders','CommunityArticle');Post=apps.get_model('tenders','CommunityPost')
    for title,category,summary,featured in ARTICLES: Article.objects.update_or_create(title=title,defaults={'category':category,'summary':summary,'content':summary,'read_minutes':6,'is_featured':featured})
    for title,category,author,content,views,replies,featured in POSTS: Post.objects.update_or_create(title=title,defaults={'category':category,'author_name':author,'content':content,'view_count':views,'reply_count':replies,'is_featured':featured})

class Migration(migrations.Migration):
    dependencies=[('tenders','0014_companyprofile_ai_profile_fields'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='CommunityArticle',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('title',models.CharField(max_length=220,unique=True,verbose_name='文章标题')),('category',models.CharField(db_index=True,max_length=60,verbose_name='内容分类')),('summary',models.TextField(verbose_name='内容摘要')),('content',models.TextField(blank=True,verbose_name='正文内容')),('read_minutes',models.PositiveSmallIntegerField(default=5,verbose_name='阅读分钟数')),('is_featured',models.BooleanField(default=False,verbose_name='重点推荐')),('published_at',models.DateTimeField(auto_now_add=True,verbose_name='发布时间'))],options={'ordering':['-is_featured','-published_at']}),
        migrations.CreateModel(name='CommunityPost',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('author_name',models.CharField(max_length=80,verbose_name='作者显示名')),('title',models.CharField(max_length=220,verbose_name='帖子标题')),('category',models.CharField(db_index=True,max_length=60,verbose_name='交流分类')),('content',models.TextField(verbose_name='帖子内容')),('view_count',models.PositiveIntegerField(default=0,verbose_name='浏览次数')),('reply_count',models.PositiveIntegerField(default=0,verbose_name='回复数量')),('is_featured',models.BooleanField(default=False,verbose_name='精华内容')),('created_at',models.DateTimeField(auto_now_add=True,verbose_name='发布时间')),('author',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='bid_community_posts',to=settings.AUTH_USER_MODEL))],options={'ordering':['-is_featured','-created_at']}),
        migrations.RunPython(seed_community,migrations.RunPython.noop),
    ]
