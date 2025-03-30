from django.shortcuts import render, redirect, get_object_or_404
from auth_app.models import Doctor
from .models import Appointment, DoctorAvailability
from dashboard.models import Notification
from django.contrib.auth.decorators import login_required
from datetime import datetime,time,timedelta
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

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
        'role': getattr(request.user, 'role', None),
    }
    return render(request, 'appointment/doctor_list.html', context)


@login_required
def book_appointment(request, doctor_id=None):
    # Check if doctor_id is None or empty
    if not doctor_id:
        messages.warning(request, "Please select a doctor from the list to book an appointment.")
        return redirect('doctor_list')
    doctor = get_object_or_404(Doctor, id=doctor_id)
    availability = get_object_or_404(DoctorAvailability, doctor=doctor)
    
    # Prepare context for rendering
    context = {
        'doctor': doctor,
        'availability': availability,
        'role': getattr(request.user, 'role', None),  # Pass user role
        'error_message': None,  # Initialize error message
    }

    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        location = request.POST.get('location')
        notes = request.POST.get('notes')

        # Convert strings to datetime objects
        appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        appointment_time_obj = datetime.strptime(appointment_time, "%H:%M").time()

        # Combine date and time into a single datetime object
        appointment_datetime_naive = datetime.combine(appointment_date_obj, appointment_time_obj)

        # Make the combined datetime timezone-aware
        appointment_datetime = timezone.make_aware(appointment_datetime_naive)

        # Get the current datetime (timezone-aware)
        current_datetime = timezone.now()

        # Check if the appointment date/time is in the past
        if appointment_datetime < current_datetime:
            context['error_message'] = "Appointments cannot be booked for past dates or times."
            return render(request, 'appointment/book_appointment.html', context)

        # Check if the appointment date is a weekend
        if appointment_date_obj.weekday() in [5, 6]:  # Saturday or Sunday
            context['error_message'] = "Appointments cannot be booked on weekends (Saturday or Sunday)."
            return render(request, 'appointment/book_appointment.html', context)

        # Check if the appointment time is within visiting hours
        if not (availability.visiting_hours_start <= appointment_time_obj <= availability.visiting_hours_end):
            context['error_message'] = "The selected time is outside the doctor's visiting hours."
            return render(request, 'appointment/book_appointment.html', context)

        # Check if the doctor is already booked for the selected date and time
        existing_appointment = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date_obj,
            appointment_time=appointment_time_obj
        ).exists()
        if existing_appointment:
            context['error_message'] = "The doctor is already booked for the selected date and time."
            return render(request, 'appointment/book_appointment.html', context)

        # Create the appointment if all checks pass
        appointment = Appointment.objects.create(
            patient=request.user.patient_profile,
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            location=location,
            notes=notes,
        )
        
        # Notify doctor about new appointment
        Notification.objects.create(
            user=doctor.user,
            message=f"New appointment request from {request.user.get_full_name()} for {appointment_date} at {appointment_time}."
        )
        
        messages.success(
            request,
            f"Your appointment with Dr. {doctor.user.get_full_name()} has been booked for {appointment_date} at {appointment_time}."
        )
        return redirect('doctor_list')  # Redirect to doctor list or another page

    return render(request, 'appointment/book_appointment.html', context)

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
        
        Notification.objects.create(
            user=request.user,
            message="Your availability settings have been updated successfully."
        )
        
        return redirect('doctor_dashboard')

    return render(request, 'dashboard/doctor/doctor_availability_form.html', {'doctor': doctor})