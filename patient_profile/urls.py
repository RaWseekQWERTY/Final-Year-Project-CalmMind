from django.urls import path
from . import views


urlpatterns = [
    path('', views.patient_profile, name='patient_profile'),
    path('update/', views.update_profile, name='update_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('appointments/', views.patient_appointments, name='patient_appointments'),
    path('appointment-pdf/<int:appointment_id>/', views.appointment_pdf, name='appointment_pdf'),
]