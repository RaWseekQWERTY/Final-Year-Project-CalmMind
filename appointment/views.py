from django.shortcuts import render, redirect, get_object_or_404
from auth_app.models import Doctor
from .models import Appointment, DoctorAvailability
from django.contrib.auth.decorators import login_required
from datetime import datetime,time,timedelta
from django.db.models import Q

# List of all available doctors
@login_required
def doctor_list(request):
    # Get filter parameters from the request
    specialty = request.GET.get('specialty', '')
    gender = request.GET.get('gender', '')
    available_today = request.GET.get('available_today', False)
    available_this_week = request.GET.get('available_this_week', False)

    # Start with all doctors
    doctors = Doctor.objects.all()

    # Apply filters
    if specialty:
        doctors = doctors.filter(specialization__icontains=specialty)
    if gender:
        doctors = doctors.filter(user__gender=gender)  # Filter by gender in the User model

    # Filter by availability
    if available_today or available_this_week:
        today = datetime.today().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        availability_filters = Q()
        if available_today:
            availability_filters |= Q(information__visiting_hours_start__lte=time(23, 59, 59), information__visiting_hours_end__gte=time(0, 0, 0))
        if available_this_week:
            availability_filters |= Q(information__visiting_hours_start__lte=time(23, 59, 59), information__visiting_hours_end__gte=time(0, 0, 0))

        doctors = doctors.filter(availability_filters)

    # Check if no doctors are available
    no_doctors = not doctors.exists()

    # Fetch availability information for each doctor
    doctor_data = []
    for doctor in doctors:
        availability = DoctorAvailability.objects.filter(doctor=doctor).first()
        doctor_data.append({
            'doctor': doctor,
            'availability': availability
        })

    # Get unique specializations for the filter dropdown
    specializations = Doctor.objects.values_list('specialization', flat=True).distinct()

    context = {
        'doctor_data': doctor_data,
        'no_doctors': no_doctors,
        'specializations': specializations,
        'selected_specialty': specialty,
        'selected_gender': gender,
        'available_today': available_today,
        'available_this_week': available_this_week,
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