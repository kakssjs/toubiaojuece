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
from django.contrib.staticfiles.views import serve as staticfiles_serve
from django.urls import path

from tenders.views import (
    analyze_tender_agent,
    analyze_tender_blob_agent,
    analyze_tender_pdf_agent,
    auth_login_api,
    auth_register_api,
    auth_logout_api,
    auth_change_password_api,
    auth_status,
    authorize_blob_upload,
    ask_report_question,
    company_profile_detail,
    contracts_collection,
    contracts_page,
    historical_bid_cases,
    project_radar,
    bid_prediction,
    generate_bid_outline,
    run_agent_team,
    community_articles,
    community_posts,
    contract_detail_api,
    create_project_note,
    download_tender_document,
    export_report_pdf,
    export_report_word,
    frontend_app,
    frontend_static,
    list_companies,
    list_reference_tenders,
    list_task_notifications,
    mark_task_notification_read,
    project_dashboard,
    project_detail,
    recent_projects,
    report_detail,
    system_status,
    staff_account_management,
    update_project_status,
    update_project_task_status,
    api_root,
)

urlpatterns = [
    path('static/frontend/<path:path>', frontend_static, name='frontend_static'),
    path('static/<path:path>', staticfiles_serve, {'insecure': True}, name='staticfiles'),
    path('api/', api_root, name='api_root'),
    path('api/agent/analyze/', analyze_tender_agent, name='agent_analyze'),
    path('api/agent/analyze-blob/', analyze_tender_blob_agent, name='agent_analyze_blob'),
    path('api/agent/analyze-pdf/', analyze_tender_pdf_agent, name='agent_analyze_pdf'),
    path('api/auth/status/', auth_status, name='auth_status'),
    path('api/auth/login/', auth_login_api, name='auth_login'),
    path('api/auth/register/', auth_register_api, name='auth_register'),
    path('api/auth/logout/', auth_logout_api, name='auth_logout'),
    path('api/auth/change-password/', auth_change_password_api, name='auth_change_password'),
    path('api/auth/upload-authorize/', authorize_blob_upload, name='upload_authorize'),
    path('api/documents/<int:document_id>/download/', download_tender_document, name='document_download'),
    path('api/system/status/', system_status, name='system_status'),
    path('api/admin/accounts/', staff_account_management, name='staff_account_management'),
    path('api/companies/', list_companies, name='company_list'),
    path('api/contracts/', contracts_collection, name='contract_collection'),
    path('api/historical-bids/', historical_bid_cases, name='historical_bid_cases'),
    path('api/project-radar/', project_radar, name='project_radar'),
    path('api/bid-prediction/', bid_prediction, name='bid_prediction'),
    path('api/bid-generator/', generate_bid_outline, name='generate_bid_outline'),
    path('api/agent-team/run/', run_agent_team, name='run_agent_team'),
    path('api/community/articles/', community_articles, name='community_articles'),
    path('api/community/posts/', community_posts, name='community_posts'),
    path('api/contracts/<int:contract_id>/', contract_detail_api, name='contract_detail_api'),
    path('api/reference-tenders/', list_reference_tenders, name='reference_tender_list'),
    path('api/company-profile/', company_profile_detail, name='company_profile_detail'),
    path('api/projects/', project_dashboard, name='project_dashboard'),
    path('api/projects/recent/', recent_projects, name='recent_projects'),
    path('api/projects/<int:project_id>/', project_detail, name='project_detail'),
    path('api/projects/<int:project_id>/notes/', create_project_note, name='project_note_create'),
    path('api/projects/<int:project_id>/status/', update_project_status, name='project_status_update'),
    path('api/project-tasks/<int:task_id>/status/', update_project_task_status, name='project_task_status_update'),
    path('api/project-tasks/<int:task_id>/', update_project_task_status, name='project_task_update'),
    path('api/notifications/', list_task_notifications, name='task_notification_list'),
    path('api/notifications/<int:task_id>/read/', mark_task_notification_read, name='task_notification_read'),
    path('api/reports/<int:report_id>/', report_detail, name='report_detail'),
    path('api/reports/<int:report_id>/ask/', ask_report_question, name='report_ask'),
    path('api/reports/<int:report_id>/export/pdf/', export_report_pdf, name='report_export_pdf'),
    path('api/reports/<int:report_id>/export/word/', export_report_word, name='report_export_word'),
    path('', frontend_app, name='frontend_app'),
    path('product/', frontend_app, name='frontend_product'),
    path('community/', frontend_app, name='frontend_community'),
    path('workspace/', frontend_app, name='frontend_workspace'),
    path('solutions/', frontend_app, name='frontend_solutions'),
    path('process/', frontend_app, name='frontend_process'),
    path('scenes/', frontend_app, name='frontend_scenes'),
    path('agent/', frontend_app, name='frontend_agent'),
    path('company/', frontend_app, name='frontend_company'),
    path('accounts/', frontend_app, name='frontend_accounts'),
    path('register/', frontend_app, name='frontend_register'),
    path('contracts/', contracts_page, name='contracts_page'),
    path('projects/', frontend_app, name='frontend_projects'),
    path('projects/<int:project_id>/', frontend_app, name='frontend_project_detail'),
    path('reports/<int:report_id>/', frontend_app, name='frontend_report_detail'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
