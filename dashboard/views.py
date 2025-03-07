# dashboard/views.py
from django.shortcuts import render, redirect
from appointment.models import Appointment, DoctorAvailability
from auth_app.models import Doctor, Patient
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.utils.timezone import now
from django.contrib import messages
from django.http import JsonResponse
from .models import Notification
from django.db import models
import plotly.express as px
import plotly.graph_objects as go
from django.db.models import Q
from datetime import datetime

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
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    data = {
        'notifications': [{
            'message': notification.message,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': notification.is_read
        } for notification in notifications],
        'unread_count': unread_count
    }
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

            elif new_status == 'Cancelled' and appointment.status != 'Cancelled':
                appointment.status = 'Cancelled'
                appointment.save()
                
                # Notify patient about the cancellation
                Notification.objects.create(
                    user=appointment.patient.user,
                    message=f"Your appointment on {appointment.appointment_date} has been cancelled."
                )
                messages.success(request, 'Appointment cancelled successfully.')

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

@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def doctor_analytics(request):
    doctor_appointments = Appointment.objects.filter(doctor=request.user.doctor_profile)

    # Status counts (Donut Chart)
    status_counts = doctor_appointments.values('status').annotate(count=models.Count('id'))
    status_fig = px.pie(
        data_frame=list(status_counts),
        names='status',
        values='count',
        hole=0.4
    )
    status_chart = status_fig.to_html(full_html=False)

    # Daily Appointments (Last 10 days - Bar Chart)
    daily_appointments = doctor_appointments.values('appointment_date').annotate(
        count=models.Count('id')
    ).order_by('-appointment_date')[:10]
    daily_fig = px.bar(
        data_frame=list(daily_appointments),
        x='appointment_date',
        y='count'
    )
    daily_chart = daily_fig.to_html(full_html=False)

    # Appointments by Time of Day (Line Chart)
    time_slots = doctor_appointments.extra(
        select={'hour': "EXTRACT(hour FROM appointment_time)"}
    ).values('hour').annotate(count=models.Count('id')).order_by('hour')
    time_fig = px.line(
        data_frame=list(time_slots),
        x='hour',
        y='count'
    )
    time_chart = time_fig.to_html(full_html=False)

    # Monthly Appointment Trend
    one_year_ago = now() - timedelta(days=365)
    monthly_appointments = (
        doctor_appointments.filter(appointment_date__gte=one_year_ago)
        .annotate(month=models.functions.TruncMonth('appointment_date'))
        .values('month')
        .annotate(count=models.Count('id'))
        .order_by('month')
    )
    monthly_fig = px.line(
        data_frame=list(monthly_appointments),
        x='month',
        y='count',
        title="Monthly Appointment Trend (Last 12 Months)"
    )
    monthly_chart = monthly_fig.to_html(full_html=False)

    context = {
        'status_chart': status_chart,
        'daily_chart': daily_chart,
        'time_chart': time_chart,
        'monthly_chart': monthly_chart,
        'total_appointments': doctor_appointments.count(),
        'confirmed_count': doctor_appointments.filter(status='Confirmed').count(),
        'pending_count': doctor_appointments.filter(status='Pending').count(),
        'cancelled_count': doctor_appointments.filter(status='Cancelled').count(),
    }

    return render(request, 'dashboard/doctor/analytics.html', context)

@login_required
def doctor_appointments_data(request):
    # Get the parameters from DataTables
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    status_filter = request.GET.get('status', '')

    # Base queryset
    queryset = Appointment.objects.filter(doctor=request.user.doctor_profile)

    # Apply status filter if provided
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Apply search
    if search_value:
        queryset = queryset.filter(
            Q(patient__user__first_name__icontains=search_value) |
            Q(patient__user__last_name__icontains=search_value) |
            Q(location__icontains=search_value) |
            Q(status__icontains=search_value)
        )

    # Total records before filtering
    total_records = queryset.count()

    # Order
    order_column = int(request.GET.get('order[0][column]', 0))
    order_dir = request.GET.get('order[0][dir]', 'asc')
    
    # Define orderable columns
    orderable_columns = ['patient__user__first_name', 'appointment_date', 'appointment_time', 'status', 'location']
    if order_column < len(orderable_columns):
        order_field = orderable_columns[order_column]
        if order_dir == 'desc':
            order_field = f'-{order_field}'
        queryset = queryset.order_by(order_field)

    # Pagination
    queryset = queryset[start:start + length]

    # Prepare data for response
    data = []
    for appointment in queryset:
        data.append({
            'id': appointment.id,
            'patient': appointment.patient.user.get_full_name(),
            'patient_image': appointment.patient.featured_image.url,
            'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d'),
            'appointment_time': appointment.appointment_time.strftime('%H:%M'),
            'status': appointment.status,
            'location': appointment.location,
            'notes': appointment.notes or ''
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })
