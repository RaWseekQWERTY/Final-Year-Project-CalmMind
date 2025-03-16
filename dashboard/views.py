# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from appointment.models import Appointment, DoctorAvailability
from auth_app.models import Doctor, Patient
from assessment.models import PHQ9Assessment
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta, datetime, time
from django.utils.timezone import now
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Notification
from django.db import models
import plotly.express as px
import plotly.graph_objects as go
from django.db.models import Q, Count, Max
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
from django.views.decorators.http import require_POST


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

    # Add notification for report generation
    Notification.objects.create(
        user=request.user,
        message="Analytics report has been generated successfully."
    )

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
    
    
@login_required
def patients_info(request):
    """Render the patients' information page for doctors."""
    return render(request, 'dashboard/doctor/patients_info.html')

@login_required
def patients_info_data(request):
    """Ajax endpoint for patients DataTable."""
    doctor = Doctor.objects.get(user=request.user)
    
    # Get the parameters from DataTables
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # Base queryset
    queryset = Patient.objects.filter(appointments__doctor=doctor).distinct()

    # Total records before filtering
    total_records = queryset.count()

    # Apply search
    if search_value:
        queryset = queryset.filter(
            Q(user__first_name__icontains=search_value) |
            Q(user__last_name__icontains=search_value) |
            Q(contact_number__icontains=search_value)
        )

    # Total records after filtering
    filtered_records = queryset.count()

    # Ordering
    order_column = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')
    
    # Define column ordering
    columns = ['user__first_name', 'contact_number', 'appointments__appointment_date', 'id', 'id']
    
    if order_column and int(order_column) < len(columns):
        order_field = columns[int(order_column)]
        if order_dir == 'desc':
            order_field = f'-{order_field}'
        queryset = queryset.order_by(order_field)

    # Pagination
    queryset = queryset[start:start + length]

    data = []
    for patient in queryset:
        appointments = Appointment.objects.filter(patient=patient, doctor=doctor)
        latest_assessment = PHQ9Assessment.objects.filter(patient=patient).order_by('-assessment_date').first()
        
        # Get severity and create appropriate badge
        severity = latest_assessment.get_depression_level_display() if latest_assessment else "Not Assessed"
        severity_badge = ''
        
        if severity == 'Mild':
            severity_badge = '<span class="bg-blue-100 text-blue-800 rounded-full px-3 py-1 text-sm">Mild</span>'
        elif severity == 'Moderate':
            severity_badge = '<span class="bg-yellow-100 text-yellow-800 rounded-full px-3 py-1 text-sm">Moderate</span>'
        elif severity == 'Severe':
            severity_badge = '<span class="bg-red-100 text-red-800 rounded-full px-3 py-1 text-sm">Severe</span>'
        else:
            severity_badge = '<span class="bg-gray-100 text-gray-800 rounded-full px-3 py-1 text-sm">Not Assessed</span>'
        
        data.append({
            'full_name': patient.user.get_full_name(),
            'contact_number': patient.contact_number or '',
            'last_appointment': appointments.latest('appointment_date').appointment_date.strftime('%Y-%m-%d') if appointments.exists() else "N/A",
            'total_appointments': appointments.count(),
            'phq9_severity': severity_badge,  # Use the HTML badge instead of plain text
            'actions': f'<button onclick="openPatientModal({patient.id})" class="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded">View</button>'
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })

@login_required
def patient_modal_data(request, patient_id):
    """Endpoint to get patient data for the modal."""
    doctor = Doctor.objects.get(user=request.user)
    patient = Patient.objects.get(id=patient_id)
    
    # Patient Information
    patient_info = {
        'full_name': patient.user.get_full_name(),
        'email': patient.user.email,
        'contact_number': patient.contact_number or '',
        'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else '',
        'gender': patient.user.gender,
        'address': patient.address or '',
    }
    
    # Appointments History
    appointments = Appointment.objects.filter(
        patient=patient,
        doctor=doctor
    ).order_by('-appointment_date')
    
    appointments_data = []
    for apt in appointments:
        appointments_data.append({
            'id': apt.id,
            'date': apt.appointment_date.strftime('%Y-%m-%d'),
            'time': apt.appointment_time.strftime('%H:%M'),
            'status': apt.status,
            'location': apt.location,
            'notes': apt.notes or '',
        })
    
    # PHQ-9 Assessments History
    assessments = PHQ9Assessment.objects.filter(
        patient=patient
    ).order_by('-assessment_date')
    
    assessments_data = []
    for assessment in assessments:
        assessments_data.append({
            'date': assessment.assessment_date.strftime('%Y-%m-%d'),
            'score': assessment.predicted_score,
            'severity': assessment.get_depression_level_display()
        })
    
    data = {
        'patient_info': patient_info,
        'appointments': appointments_data,
        'assessments': assessments_data,
    }
    
    return JsonResponse(data)

@login_required
def update_appointment_notes(request, appointment_id):
    """Endpoint to update appointment notes."""
    if request.method == 'POST':
        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                doctor=request.user.doctor_profile
            )
            notes = request.POST.get('notes', '')
            appointment.notes = notes
            appointment.save()
            return JsonResponse({'status': 'success', 'notes': notes})
        except Appointment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Appointment not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def export_patient_pdf(request, patient_id):
    # Get the patient and related data
    try:
        doctor = request.user.doctor_profile
        patient = Patient.objects.get(id=patient_id)
        
        # Get recent appointments
        recent_appointments = Appointment.objects.filter(
            patient=patient,
            doctor=doctor
        ).order_by('-appointment_date')[:5]
        
        # Get recent assessments
        recent_assessments = PHQ9Assessment.objects.filter(
            patient=patient
        ).order_by('-assessment_date')[:5]
        
        # Create the PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        elements.append(Paragraph(f"Patient Report - {patient.user.get_full_name()}", title_style))
        
        # Patient Information
        elements.append(Paragraph("Patient Information", styles['Heading2']))
        patient_info = [
            ["Full Name:", patient.user.get_full_name()],
            ["Email:", patient.user.email],
            ["Contact Number:", patient.contact_number or "N/A"],
            ["Date of Birth:", patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else "N/A"],
            ["Gender:", patient.user.gender],
            ["Address:", patient.address or "N/A"]
        ]
        
        info_table = Table(patient_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Recent Appointments
        elements.append(Paragraph("Recent Appointments", styles['Heading2']))
        if recent_appointments:
            appointments_data = [["Date", "Time", "Status", "Notes"]]
            for apt in recent_appointments:
                appointments_data.append([
                    apt.appointment_date.strftime('%Y-%m-%d'),
                    apt.appointment_time.strftime('%H:%M'),
                    apt.status,
                    apt.notes or "N/A"
                ])
            
            apt_table = Table(appointments_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 2.5*inch])
            apt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(apt_table)
        else:
            elements.append(Paragraph("No recent appointments found.", styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Recent Assessments
        elements.append(Paragraph("Recent PHQ-9 Assessments", styles['Heading2']))
        if recent_assessments:
            assessments_data = [["Date", "Score", "Severity"]]
            for assessment in recent_assessments:
                assessments_data.append([
                    assessment.assessment_date.strftime('%Y-%m-%d'),
                    str(assessment.predicted_score),
                    assessment.get_depression_level_display()
                ])
            
            assess_table = Table(assessments_data, colWidths=[2*inch, 2*inch, 3*inch])
            assess_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(assess_table)
        else:
            elements.append(Paragraph("No recent assessments found.", styles['Normal']))
        
        # Generate PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and write it to the response
        pdf = buffer.getvalue()
        buffer.close()
        
        # Generate the response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="patient_report_{patient_id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        response.write(pdf)
        
        # Add notification for PDF generation
        Notification.objects.create(
            user=request.user,
            message=f"Patient report for {patient.user.get_full_name()} has been generated."
        )
        
        return response
        
    except Patient.DoesNotExist:
        return HttpResponse('Patient not found', status=404)
    except Exception as e:
        return HttpResponse(f'Error generating PDF: {str(e)}', status=500)

@login_required
def patient_dashboard(request):
    # Get patient's PHQ-9 assessments ordered by date
    assessments = PHQ9Assessment.objects.filter(
        patient=request.user.patient_profile
    ).order_by('assessment_date')
    
    # Initialize context
    context = {}
    
    if assessments.exists():
        # Create plotly figure for assessment history
        dates = [assessment.assessment_date.strftime('%Y-%m-%d') for assessment in assessments]
        scores = [assessment.score for assessment in assessments]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            name='PHQ-9 Score',
            line=dict(color='#10B981'),  # Green color to match the theme
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='PHQ-9 Score History',
            xaxis_title='Assessment Date',
            yaxis_title='Score',
            hovermode='x unified',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis=dict(gridcolor='rgba(0,0,0,0.1)', range=[0, max(scores) + 5]),
            xaxis=dict(gridcolor='rgba(0,0,0,0.1)')
        )
        
        # Get latest assessment
        latest_assessment = assessments.latest('assessment_date')
        
        context = {
            'has_assessments': True,
            'graph': fig.to_html(full_html=False),
            'latest_assessment': latest_assessment,
            'latest_date': latest_assessment.assessment_date.strftime('%B %d, %Y'),
            'latest_score': latest_assessment.score,
            'latest_level': latest_assessment.get_depression_level_display(),
        }
    else:
        context['has_assessments'] = False
    
    # Get next confirmed appointment
    next_appointment = Appointment.objects.filter(
        patient=request.user.patient_profile,
        status='Confirmed',
        appointment_date__gte=now().date()
    ).order_by('appointment_date', 'appointment_time').first()

    context.update({
        'next_appointment': next_appointment,
        'today': date.today(),
    })
    
    return render(request, 'dashboard/patient/patient_dash.html', context)

@login_required
def reschedule_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, 
                                  id=appointment_id, 
                                  patient=request.user.patient_profile)
    
    if request.method == 'POST':
        try:
            # Parse the date and time from the form
            new_date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
            new_time = datetime.strptime(request.POST.get('time'), '%H:%M').time()
            
            # Check if the date is in the past
            if new_date < date.today():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot schedule appointments in the past'
                }, status=400)
            
            # Check if the date is a weekend
            if new_date.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
                return JsonResponse({
                    'status': 'error',
                    'message': 'Doctor is not available on weekends'
                }, status=400)
            
            # If it's today, check if the time has already passed
            if new_date == date.today() and new_time < datetime.now().time():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot schedule appointments in the past'
                }, status=400)
            
            # Get doctor's availability
            doctor_availability = DoctorAvailability.objects.get(doctor=appointment.doctor)
            
            # Check if the selected time is within doctor's visiting hours
            if new_time < doctor_availability.visiting_hours_start or new_time > doctor_availability.visiting_hours_end:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Doctor is only available between {doctor_availability.visiting_hours_start.strftime("%I:%M %p")} '
                              f'and {doctor_availability.visiting_hours_end.strftime("%I:%M %p")}'
                }, status=400)
            
            # Check if doctor has any other appointments at the same time
            conflicting_appointment = Appointment.objects.filter(
                ~Q(id=appointment_id),  # Exclude current appointment
                doctor=appointment.doctor,
                appointment_date=new_date,
                appointment_time=new_time,
                status='Confirmed'
            ).exists()
            
            if conflicting_appointment:
                return JsonResponse({
                    'status': 'error',
                    'message': 'This time slot is already booked. Please choose another time.'
                }, status=400)
            
            # Store old date/time for notification
            old_date = appointment.appointment_date
            old_time = appointment.appointment_time
            
            # Update appointment details
            appointment.appointment_date = new_date
            appointment.appointment_time = new_time
            appointment.notes = request.POST.get('notes', '')
            appointment.location = request.POST.get('location', '')
            appointment.save()
            
            # Create notification for doctor
            Notification.objects.create(
                user=appointment.doctor.user,
                message=f"Appointment with {request.user.get_full_name()} rescheduled from "
                        f"{old_date.strftime('%B %d, %Y')} at {old_time.strftime('%I:%M %p')} to "
                        f"{new_date.strftime('%B %d, %Y')} at {new_time.strftime('%I:%M %p')}"
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Appointment rescheduled successfully',
                'new_date': new_date.strftime('%B %d, %Y'),
                'new_time': new_time.strftime('%I:%M %p')
            })
        except DoctorAvailability.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': "Doctor's availability information not found"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    # For GET request, return doctor's availability along with appointment details
    try:
        doctor_availability = DoctorAvailability.objects.get(doctor=appointment.doctor)
        return JsonResponse({
            'appointment': {
                'id': appointment.id,
                'date': appointment.appointment_date.strftime('%Y-%m-%d'),
                'time': appointment.appointment_time.strftime('%H:%M'),
                'notes': appointment.notes or '',
                'location': appointment.location or '',
                'doctor_name': appointment.doctor.user.get_full_name(),
                'doctor_availability': {
                    'start_time': doctor_availability.visiting_hours_start.strftime('%H:%M'),
                    'end_time': doctor_availability.visiting_hours_end.strftime('%H:%M')
                }
            }
        })
    except DoctorAvailability.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': "Doctor's availability information not found"
        }, status=400)

@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, 
                                  id=appointment_id, 
                                  patient=request.user.patient_profile)
    
    try:
        appointment.status = 'Cancelled'
        appointment.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Appointment cancelled successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)