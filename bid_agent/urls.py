"""
URL configuration for bid_agent project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from tenders.views import (
    analyze_tender_agent,
    analyze_tender_pdf_agent,
    ask_report_question,
    company_profile_detail,
    create_project_note,
    export_report_pdf,
    export_report_word,
    frontend_app,
    list_companies,
    project_dashboard,
    project_detail,
    recent_projects,
    report_detail,
    update_project_status,
)

urlpatterns = [
    path('api/agent/analyze/', analyze_tender_agent, name='agent_analyze'),
    path('api/agent/analyze-pdf/', analyze_tender_pdf_agent, name='agent_analyze_pdf'),
    path('api/companies/', list_companies, name='company_list'),
    path('api/company-profile/', company_profile_detail, name='company_profile_detail'),
    path('api/projects/', project_dashboard, name='project_dashboard'),
    path('api/projects/recent/', recent_projects, name='recent_projects'),
    path('api/projects/<int:project_id>/', project_detail, name='project_detail'),
    path('api/projects/<int:project_id>/notes/', create_project_note, name='project_note_create'),
    path('api/projects/<int:project_id>/status/', update_project_status, name='project_status_update'),
    path('api/reports/<int:report_id>/', report_detail, name='report_detail'),
    path('api/reports/<int:report_id>/ask/', ask_report_question, name='report_ask'),
    path('api/reports/<int:report_id>/export/pdf/', export_report_pdf, name='report_export_pdf'),
    path('api/reports/<int:report_id>/export/word/', export_report_word, name='report_export_word'),
    path('', frontend_app, name='frontend_app'),
    path('product/', frontend_app, name='frontend_product'),
    path('solutions/', frontend_app, name='frontend_solutions'),
    path('process/', frontend_app, name='frontend_process'),
    path('scenes/', frontend_app, name='frontend_scenes'),
    path('agent/', frontend_app, name='frontend_agent'),
    path('company/', frontend_app, name='frontend_company'),
    path('projects/', frontend_app, name='frontend_projects'),
    path('projects/<int:project_id>/', frontend_app, name='frontend_project_detail'),
    path('reports/<int:report_id>/', frontend_app, name='frontend_report_detail'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
