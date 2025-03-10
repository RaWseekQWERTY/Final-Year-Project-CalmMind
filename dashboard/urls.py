from django.urls import path
from . import views

urlpatterns = [
    path('doctor_dashboard', views.doctor_dashboard, name='dashboard-doctor'),
    path('doctor_appointments', views.doctor_appointments, name='doctor-appointments'),
    path('doctor_appointments/data/', views.doctor_appointments_data, name='doctor-appointments-data'),
    path('get-notifications/', views.get_notifications, name='get-notifications'),
    path('mark-notifications-read/', views.mark_notifications_read, name='mark-notifications-read'),
    path('doctor_analytics/', views.doctor_analytics, name='doctor-analytics'),
    path('doctor_patients/', views.patients_info, name='doctor-patients'),
    path('doctor_patients/data/', views.patients_info_data, name='doctor-patients-data'),
    path('patient_modal_data/<int:patient_id>/', views.patient_modal_data, name='patient-modal-data'),
    path('update_appointment_notes/<int:appointment_id>/', views.update_appointment_notes, name='update-appointment-notes'),
]
