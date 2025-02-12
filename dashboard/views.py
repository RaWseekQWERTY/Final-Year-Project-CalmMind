# dashboard/views.py
from django.shortcuts import render
from appointment.models import Appointment, DoctorAvailability
from auth_app.models import Doctor, Patient
from django.contrib.auth.decorators import login_required
from datetime import date

@login_required
def doctor_dashboard(request):
    total_doctors = Doctor.objects.count()
    total_patients = Patient.objects.count()
    total_appointments = Appointment.objects.count()
    today_appointments = Appointment.objects.filter(appointment_date=date.today()).count()
    pending_appointments = Appointment.objects.filter(status='Pending').count()

    # Recent appointments (limit to 5)
    recent_appointments = Appointment.objects.order_by('-created_at')[:5]

    context = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'dashboard/doctor/doctor_dash.html', context)
