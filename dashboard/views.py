# dashboard/views.py
from django.shortcuts import render, redirect
from appointment.models import Appointment, DoctorAvailability
from auth_app.models import Doctor, Patient
from django.contrib.auth.decorators import login_required
from datetime import date
from django.contrib import messages
from django.http import JsonResponse
from .models import Notification

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


@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    data = [{
        'message': notification.message,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for notification in notifications]
    return JsonResponse(data, safe=False)


@login_required
def doctor_appointments(request):
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        new_status = request.POST.get('status')

        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                doctor=request.user.doctor_profile
            )
            
            # Handle status change cases
            if new_status == 'Confirmed' and appointment.status == 'Pending':
                appointment.status = 'Confirmed'
                appointment.save()
                
                # Notify patient about the confirmation
                Notification.objects.create(
                    user=appointment.patient.user,
                    message=f"Your appointment on {appointment.appointment_date} has been confirmed."
                )
                messages.success(request, 'Appointment confirmed successfully.')

            elif new_status == 'Canceled' and appointment.status != 'Canceled':
                appointment.status = 'Canceled'
                appointment.save()
                
                # Notify patient about the cancellation
                Notification.objects.create(
                    user=appointment.patient.user,
                    message=f"Your appointment on {appointment.appointment_date} has been canceled."
                )
                messages.success(request, 'Appointment canceled successfully.')

            elif new_status == 'Pending' and appointment.status != 'Pending':
                appointment.status = 'Pending'
                appointment.save()
                
                # Notify patient about the status change to pending
                Notification.objects.create(
                    user=appointment.patient.user,
                    message=f"Your appointment on {appointment.appointment_date} is now pending."
                )
                messages.success(request, 'Appointment status set to pending.')

            else:
                messages.warning(request, 'No changes were made to the appointment status.')
        
        except Appointment.DoesNotExist:
            messages.error(request, 'Appointment not found.')
        
        return redirect('doctor-appointments')

    # Get appointments for the logged-in doctor
    appointments = Appointment.objects.filter(
        doctor=request.user.doctor_profile
    ).order_by('appointment_date', 'appointment_time')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        appointments = appointments.filter(status=status_filter)
    
    context = {
        'appointments': appointments,
        'current_status': status_filter if status_filter else 'all',
        'status_choices': Appointment.STATUS_CHOICES,
    }
    return render(request, 'dashboard/doctor/appointments.html', context)
