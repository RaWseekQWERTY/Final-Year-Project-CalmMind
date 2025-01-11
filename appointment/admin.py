from django.contrib import admin
from .models import Appointment, DoctorAvailability

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'appointment_time', 'status')

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'visiting_hours_start', 'visiting_hours_end', 'consultation_fee', 'location')