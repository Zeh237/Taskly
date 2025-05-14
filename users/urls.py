from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('verify/', views.verify_email_view, name='verify_email'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_request_view, name='forgot_password_request'),
    path('forgot-password/verify/', views.forgot_password_verify_view, name='forgot_password_verify'),
    path('forgot-password/reset/', views.forgot_password_reset_view, name='forgot_password_reset'),
]