from django.urls import path
from users import views as user_views
from django.contrib.auth import views as auth_views
from users import views as user_views

urlpatterns = [
    path('register/', user_views.register, name='register'),
    path('change_password/', user_views.change_password, name='change-pass'),
    path('login/', auth_views.LoginView.as_view(template_name='admin_login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('profile/', user_views.profile, name='profile'),
]