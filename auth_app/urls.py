from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('admin_dash/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_dash/update_role/<int:user_id>/', views.update_user_role_page, name='update_user_role_page'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('about/', views.about_view, name='about'),
    path('api/user-stats/', views.user_stats_api, name='user_stats_api'),
    path('api/depression-stats/', views.depression_stats_api, name='depression_stats_api'),
    path('api/appointment-stats/', views.appointment_stats_api, name='appointment_stats_api'),
    path('api/user-pdf/<int:user_id>/', views.generate_user_pdf, name='generate_user_pdf'),
    path('api/users/', views.users_api, name='users_api'),
]