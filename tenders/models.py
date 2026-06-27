from django.db import models


class CompanyProfile(models.Model):
    name = models.CharField('企业名称', max_length=120)
    main_business = models.TextField('主营业务', blank=True)
    service_regions = models.CharField('服务地区', max_length=255, blank=True)
    max_project_amount = models.DecimalField('可承接最高金额', max_digits=14, decimal_places=2, null=True, blank=True)
    forbidden_conditions = models.TextField('禁投条件', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '企业能力档案'
        verbose_name_plural = '企业能力档案'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class Qualification(models.Model):
    company = models.ForeignKey(
        CompanyProfile,
        verbose_name='所属企业',
        related_name='qualifications',
        on_delete=models.CASCADE,
    )
    name = models.CharField('资质名称', max_length=160)
    certificate_no = models.CharField('证书编号', max_length=120, blank=True)
    issuer = models.CharField('发证机构', max_length=160, blank=True)
    valid_until = models.DateField('有效期至', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '资质证书'
        verbose_name_plural = '资质证书'
        ordering = ['company__name', 'name']

    def __str__(self):
        return self.name


class ProjectExperience(models.Model):
    company = models.ForeignKey(
        CompanyProfile,
        verbose_name='所属企业',
        related_name='experiences',
        on_delete=models.CASCADE,
    )
    name = models.CharField('项目名称', max_length=180)
    industry = models.CharField('所属行业', max_length=120, blank=True)
    amount = models.DecimalField('合同金额', max_digits=14, decimal_places=2, null=True, blank=True)
    client_name = models.CharField('客户名称', max_length=160, blank=True)
    completed_at = models.DateField('完成日期', null=True, blank=True)
    description = models.TextField('项目说明', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '历史业绩'
        verbose_name_plural = '历史业绩'
        ordering = ['company__name', '-completed_at', 'name']

    def __str__(self):
        return self.name


class TenderProject(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', '待分析'
        ANALYZING = 'analyzing', '分析中'
        ANALYZED = 'analyzed', '已分析'
        RECOMMENDED = 'recommended', '推荐报名'
        ABANDONED = 'abandoned', '已放弃'
        ARCHIVED = 'archived', '已归档'

    company = models.ForeignKey(
        CompanyProfile,
        verbose_name='匹配企业',
        related_name='tender_projects',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField('项目名称', max_length=220)
    procurement_method = models.CharField('采购方式', max_length=80, blank=True)
    project_type = models.CharField('项目类型', max_length=80, blank=True)
    region = models.CharField('项目地区', max_length=120, blank=True)
    budget_amount = models.DecimalField('预算金额', max_digits=14, decimal_places=2, null=True, blank=True)
    deadline = models.DateTimeField('投标截止时间', null=True, blank=True)
    source_text = models.TextField('招标文本', blank=True)
    status = models.CharField('项目状态', max_length=32, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '招标项目'
        verbose_name_plural = '招标项目'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class TenderDocument(models.Model):
    class ParseStatus(models.TextChoices):
        PENDING = 'pending', '待解析'
        PARSED = 'parsed', '已解析'
        FAILED = 'failed', '解析失败'

    tender_project = models.ForeignKey(
        TenderProject,
        verbose_name='招标项目',
        related_name='documents',
        on_delete=models.CASCADE,
    )
    file = models.FileField('PDF文件', upload_to='tender_documents/')
    original_name = models.CharField('原始文件名', max_length=255)
    file_size = models.PositiveIntegerField('文件大小', default=0)
    parse_status = models.CharField('解析状态', max_length=32, choices=ParseStatus.choices, default=ParseStatus.PENDING)
    extracted_text = models.TextField('提取文本', blank=True)
    error_message = models.TextField('错误信息', blank=True)
    created_at = models.DateTimeField('上传时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '招标文件'
        verbose_name_plural = '招标文件'
        ordering = ['-created_at']

    def __str__(self):
        return self.original_name


class ProjectNote(models.Model):
    class NoteType(models.TextChoices):
        FOLLOW_UP = 'follow_up', '跟进记录'
        RISK = 'risk', '风险说明'
        DECISION = 'decision', '决策记录'
        MATERIAL = 'material', '材料补充'
        STATUS = 'status', '状态变更'
        SYSTEM = 'system', '系统记录'

    tender_project = models.ForeignKey(
        TenderProject,
        verbose_name='招标项目',
        related_name='notes',
        on_delete=models.CASCADE,
    )
    note_type = models.CharField('记录类型', max_length=32, choices=NoteType.choices, default=NoteType.FOLLOW_UP)
    content = models.TextField('记录内容')
    operator_name = models.CharField('操作人', max_length=80, blank=True, default='系统')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '项目处理记录'
        verbose_name_plural = '项目处理记录'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.tender_project} - {self.get_note_type_display()}'


class AnalysisReport(models.Model):
    class Decision(models.TextChoices):
        RECOMMENDED = 'recommended', '推荐投标'
        CAUTIOUS = 'cautious', '谨慎投标'
        NOT_RECOMMENDED = 'not_recommended', '不建议投标'
        NEEDS_REVIEW = 'needs_review', '人工复核'

    tender_project = models.OneToOneField(
        TenderProject,
        verbose_name='招标项目',
        related_name='analysis_report',
        on_delete=models.CASCADE,
    )
    decision = models.CharField('投标建议', max_length=32, choices=Decision.choices)
    match_score = models.PositiveSmallIntegerField('匹配评分', default=0)
    summary = models.TextField('报告摘要', blank=True)
    risks = models.JSONField('风险清单', default=list, blank=True)
    missing_materials = models.JSONField('缺失材料', default=list, blank=True)
    next_actions = models.JSONField('下一步动作', default=list, blank=True)
    raw_report = models.JSONField('智能体原始报告', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = 'AI分析报告'
        verbose_name_plural = 'AI分析报告'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.tender_project} - {self.get_decision_display()}'
