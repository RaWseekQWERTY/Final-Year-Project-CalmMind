from django.shortcuts import render, redirect, get_object_or_404
from auth_app.models import Doctor
from .models import Appointment, DoctorAvailability
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

# List of all available doctors
@login_required
def doctor_list(request):
    doctors = Doctor.objects.all()
    context = {
        'doctors': doctors,
        'no_doctors': not doctors.exists(), 
    }
    return render(request, 'appointment/doctor_list.html', context)

# Appointment booking view

@login_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    availability = get_object_or_404(DoctorAvailability, doctor=doctor)

    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        location = request.POST.get('location')
        notes = request.POST.get('notes')

        # Convert strings to datetime objects
        appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        appointment_time_obj = datetime.strptime(appointment_time, "%H:%M").time()

        # Check if the appointment date is a weekend
        if appointment_date_obj.weekday() in [5, 6]:  # Saturday or Sunday
            error_message = "Appointments cannot be booked on weekends (Saturday or Sunday)."
            return render(request, 'appointment/book_appointment.html', {'doctor': doctor, 'error_message': error_message})

        # Check if the appointment time is within visiting hours
        if not (availability.visiting_hours_start <= appointment_time_obj <= availability.visiting_hours_end):
            error_message = "The selected time is outside the doctor's visiting hours."
            return render(request, 'appointment/book_appointment.html', {'doctor': doctor, 'error_message': error_message})

        # Check if the doctor is already booked for the selected date and time
        existing_appointment = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date_obj,
            appointment_time=appointment_time_obj
        ).exists()

        if existing_appointment:
            error_message = "The doctor is already booked for the selected date and time."
            return render(request, 'appointment/book_appointment.html', {'doctor': doctor, 'error_message': error_message})

        #Create the appointment if all checks pass
        Appointment.objects.create(
            patient=request.user.patient_profile,
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            location=location,
            notes=notes,
        )
        return redirect('doctor_list')  # Redirect to doctor list or another page

    return render(request, 'appointment/book_appointment.html', {'doctor': doctor})

@login_required
def doctor_availability_register(request, doctor_id):
    try:
        doctor = get_object_or_404(Doctor, id=doctor_id)
    except Doctor.DoesNotExist:
        return redirect('doctor_dashboard')  # Redirect if the doctor profile doesn't exist

    if request.user != doctor.user:
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        visiting_hours_start = request.POST.get('visiting_hours_start')
        visiting_hours_end = request.POST.get('visiting_hours_end')
        consultation_fee = request.POST.get('consultation_fee')
        location = request.POST.get('location')

        DoctorAvailability.objects.update_or_create(
            doctor=doctor,
            defaults={
                'visiting_hours_start': visiting_hours_start,
                'visiting_hours_end': visiting_hours_end,
                'consultation_fee': consultation_fee,
                'location': location,
            }
        )
        return redirect('doctor_dashboard')

    return render(request, 'dashboard/doctor/doctor_availability_form.html', {'doctor': doctor})