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
]