from django.contrib import admin

from .models import (
    AnalysisReport,
    CompanyProfile,
    Contract,
    ProjectExperience,
    ProjectNote,
    Qualification,
    TenderDocument,
    TenderProject,
    TenderReference,
)


class QualificationInline(admin.TabularInline):
    model = Qualification
    extra = 0
    fields = ('name', 'certificate_no', 'issuer', 'valid_until')


class ProjectExperienceInline(admin.TabularInline):
    model = ProjectExperience
    extra = 0
    fields = ('name', 'industry', 'amount', 'client_name', 'completed_at')


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_regions', 'max_project_amount', 'updated_at')
    search_fields = ('name', 'main_business', 'service_regions')
    list_filter = ('created_at', 'updated_at')
    inlines = (QualificationInline, ProjectExperienceInline)


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'certificate_no', 'issuer', 'valid_until')
    search_fields = ('name', 'certificate_no', 'issuer', 'company__name')
    list_filter = ('valid_until',)


@admin.register(ProjectExperience)
class ProjectExperienceAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'industry', 'amount', 'client_name', 'completed_at')
    search_fields = ('name', 'industry', 'client_name', 'company__name')
    list_filter = ('industry', 'completed_at')


@admin.register(TenderProject)
class TenderProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'project_type', 'procurement_method', 'budget_amount', 'status', 'created_at')
    search_fields = ('name', 'company__name', 'project_type', 'procurement_method', 'region')
    list_filter = ('status', 'project_type', 'procurement_method', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TenderDocument)
class TenderDocumentAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'tender_project', 'parse_status', 'file_size', 'created_at')
    search_fields = ('original_name', 'tender_project__name', 'extracted_text')
    list_filter = ('parse_status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TenderReference)
class TenderReferenceAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_type', 'industry', 'region', 'issuing_organization', 'published_at', 'is_featured')
    search_fields = ('title', 'project_type', 'industry', 'region', 'issuing_organization', 'tags', 'summary', 'source_text')
    list_filter = ('is_featured', 'project_type', 'industry', 'region', 'published_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'basic_info_preview', 'risk_tags_preview', 'source_maintenance_preview')
    search_fields = ('basic_info', 'tender_content', 'reference_points', 'scoring_rules', 'risk_tags', 'material_checklist', 'source_maintenance_info')
    list_per_page = 20

    @admin.display(description='基础信息')
    def basic_info_preview(self, obj):
        return _preview_text(obj.basic_info)

    @admin.display(description='风险标签')
    def risk_tags_preview(self, obj):
        return _preview_text(obj.risk_tags)

    @admin.display(description='来源与维护信息')
    def source_maintenance_preview(self, obj):
        return _preview_text(obj.source_maintenance_info)


@admin.register(ProjectNote)
class ProjectNoteAdmin(admin.ModelAdmin):
    list_display = ('tender_project', 'note_type', 'operator_name', 'created_at')
    search_fields = ('tender_project__name', 'content', 'operator_name')
    list_filter = ('note_type', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(AnalysisReport)
class AnalysisReportAdmin(admin.ModelAdmin):
    list_display = ('tender_project', 'decision', 'match_score', 'created_at')
    search_fields = ('tender_project__name', 'summary')
    list_filter = ('decision', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


def _preview_text(value, length=48):
    text = ' '.join(str(value or '').split())
    if len(text) <= length:
        return text or '-'
    return f'{text[:length]}...'
