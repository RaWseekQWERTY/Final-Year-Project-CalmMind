from django.shortcuts import render, redirect, get_object_or_404
from auth_app.models import Doctor
from .models import Appointment
from django.contrib.auth.decorators import login_required

# List of all available doctors
def doctor_list(request):
    doctors = Doctor.objects.all()
    context = {
        'doctors': doctors,
        'no_doctors': not doctors.exists(), 
    }
    return render(request, 'appointments/doctor_list.html', context)

# Appointment booking view

@login_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)

    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        location = request.POST.get('location')
        notes = request.POST.get('notes')

        if appointment_date and appointment_time:
            Appointment.objects.create(
                patient=request.user.patient_profile,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                location=location,
                notes=notes,
            )
            return redirect('doctor_list')  # Redirect to doctor list or another page
        else:
            error_message = "Please provide both date and time for the appointment."
            return render(request, 'appointments/book_appointment.html', {
                'doctor': doctor,
                'error_message': error_message
            })

    return render(request, 'appointment/book_appointment.html', {'doctor': doctor})