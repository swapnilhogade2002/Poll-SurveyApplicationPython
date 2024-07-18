# user_dashboard/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from survey_admin.views import admin_logout

urlpatterns = [
    path('user-dashboard', views.user_dashboard, name='user_dashboard'),
    path('user-logout/',views.user_logout, name='user_logout'),  # Logout and redirect
    path('generate-qr', views.generate_qr_code, name='qr_code'),
    path('user-disable-mfa/', views.user_disable_mfa, name='user_disable_mfa'),
    path('user-profile', views.user_profile, name='user_profile'),

    # polls
    path('user-polls/', views.user_poll_list, name='user_poll_list'),
    path('polls-create/', views.user_poll_create, name='user_poll_create'),
    path('user-poll-detail/<int:poll_id>/', views.user_poll_detail, name='user_poll_detail'),
    path('user-poll/<int:poll_id>/update/', views.user_poll_update, name='user_poll_update'),
    path('user-polls/<int:poll_id>/delete/', views.user_poll_delete, name='user_poll_delete'),
    path('user-polls-graph/<int:question_id>/', views.user_polls_graph, name='user_polls_graph'),
    path('user-dashboard/analytics/<int:question_id>/', views.user_dashboard_analytics, name='user_dashboard_analytics'),
    path('user_export_votes/<int:question_id>/', views.user_export_votes_csv, name='user_export_votes_csv'), #poll analytics

    # survey
    path('user-survey-list/', views.user_survey_list, name='user_survey_list'),
    path('user-survey-create/', views.user_survey_create, name='user_survey_create'),
    path('user-surveys/<int:survey_id>/add-question/', views.user_question_create, name='user_question_create'),
    path('user-surveys/<int:survey_id>/answer/', views.user_answer_survey, name='user_answer_survey'),
    path('user-surveys/<int:survey_id>/edit/', views.user_edit_survey, name='user_edit_survey'),
    path('user-surveys/<int:survey_id>/delete/', views.user_delete_survey, name='user_delete_survey'),
    path('user-surveys-analytics/<int:survey_id>/analytics/', views.user_survey_analytics, name='user_survey_analytics'),
    path('user-surveys/<int:survey_id>/export-csv/', views.export_survey_responses_csv, name='export_survey_responses_csv'),

    path('user-surveys/<int:survey_id>/generate-private-link/', views.generate_private_link, name='generate_private_link'),
    path('answer-private-survey/<uuid:link_uuid>/', views.answer_private_survey, name='answer_private_survey'),
    path('survey/<int:survey_id>/thank-you/', views.private_survey_answered, name='private_survey_answered'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

