from django.urls import path
from . import views

urlpatterns = [
    path('doctor_dashboard', views.doctor_dashboard, name='dashboard-doctor'),
    path('doctor_appointments', views.doctor_appointments, name='doctor-appointments'),
    path('doctor_appointments/data/', views.doctor_appointments_data, name='doctor-appointments-data'),
    path('get-notifications/', views.get_notifications, name='get-notifications'),
    path('mark-notifications-read/', views.mark_notifications_read, name='mark-notifications-read'),
    path('doctor_analytics/', views.doctor_analytics, name='doctor-analytics'),
]
