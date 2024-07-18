# custom_admin/urls.py

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.admin_login_page, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('mfa-page', views.admin_mfa_page, name='admin_mfa'),
    path('admin-dashboard', views.admin_dashoard, name='admin_dashboard'),
    path('user-dashboard', views.user_dashoard, name='user_dashboard'),
    path('user-registration', views.user_registration, name='user_registration'),
    path('admin-profile', views.admin_profile, name='admin_profile'),


    # mfa-start
    path('generate-qr', views.generate_qr_code, name='generate_qr_code'),
    path('verify-otp', views.verify_otp, name='verify_otp'),
    path('verify-otp-after-mfa', views.admin_otp_verification_page, name='otp_verification_page'),
    path('user-verify-otp-after-mfa', views.user_otp_verification_page, name='user_otp_verification_page'),
    path('disable-mfa/', views.disable_mfa, name='disable_mfa'),
    # mfa-end

    # admin-manage users data-start
    path('user-list', views.user_list, name='user_list'),
    path('user-list/<int:pk>/', views.user_detail, name='user_detail'),
    path('user-list/create/', views.user_create, name='user_create'),
    path('user-list/<int:pk>/update/', views.user_update, name='user_update'),
    path('user-list/<int:pk>/delete/', views.user_delete, name='user_delete'), 
    # admin-manage users data-end

    # polls data management-start
    path('polls/', views.poll_list, name='poll_list'),
    path('polls-create/', views.poll_create, name='poll_create'),
    path('polls/<int:poll_id>/', views.poll_detail, name='poll_detail'),
    path('polls/<int:poll_id>/update/', views.poll_update, name='poll_update'),
    path('polls/<int:poll_id>/delete/', views.poll_delete, name='poll_delete'),
    path('resultsdata/<int:question_id>/', views.resultsData, name='resultsdata'),
    path('poll/analytics/<int:question_id>/', views.dashboard_analytics, name='dashboard_analytics'), #polls
    path('poll/dashboard/', views.dashboard_analytics, name='dashboard_analytics'),

    path('export_votes/<int:question_id>/', views.export_votes_csv, name='export_votes_csv'),

    # polls data management-end

    # admin survey management-start
    path('admin-survey-list/', views.admin_survey_list, name='admin_survey_list'),
    path('admin-survey-create/', views.admin_survey_create, name='admin_survey_create'),
    path('admin-surveys/<int:survey_id>/add-question/', views.admin_question_create, name='admin_question_create'),
    path('admin-surveys/<int:survey_id>/answer/', views.admin_answer_survey, name='admin_answer_survey'),
    path('admin-surveys/<int:survey_id>/edit/', views.admin_edit_survey, name='admin_edit_survey'),
    path('admin-surveys/<int:survey_id>/delete/', views.admin_delete_survey, name='admin_delete_survey'),
    path('delete-question/<int:question_id>/', views.admin_delete_question, name='admin_delete_question'),
    path('admin-surveys-analytics/<int:survey_id>/analytics/', views.survey_analytics, name='admin_survey_analytics'),
    path('admin-surveys/<int:survey_id>/export-csv/', views.export_survey_responses_csv_admin, name='export_survey_responses_csv_admin'),

    path('admin-surveys/<int:survey_id>/generate-private-link/', views.admin_generate_private_link, name='admin_generate_private_link'),
    path('answer-private-survey/<uuid:link_uuid>/', views.admin_answer_private_survey, name='admin_answer_private_survey'),
    path('survey/<int:survey_id>/thank-you/', views.admin_private_survey_answered, name='admin_private_survey_answered'),

    # admin survey management-end
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

