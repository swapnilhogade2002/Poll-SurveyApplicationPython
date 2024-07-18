from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:question_id>/', views.detail, name='detail'),
    path('<int:question_id>/results/', views.results, name='results'),
    path('<int:question_id>/vote/', views.vote, name='vote'),
    path('resultsdata/<str:obj>/', views.resultsData, name='resultsdata'),
    path('home-survey-list/', views.home_survey_list, name='home_survey_list'),
    path('home-surveys/<int:survey_id>/answer/', views.home_answer_survey, name='home_answer_survey'),

  
]
