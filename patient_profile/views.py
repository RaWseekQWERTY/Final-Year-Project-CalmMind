from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.http import JsonResponse, HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from auth_app.models import Patient, Doctor
from assessment.models import PHQ9Assessment
from appointment.models import Appointment
from datetime import datetime
from io import BytesIO
from appointment.models import DoctorAvailability

User = get_user_model()

@login_required
def patient_profile(request):
    patient = get_object_or_404(Patient, user=request.user)
    
    # Get next appointment
    next_appointment = Appointment.objects.filter(
        patient=patient,
        appointment_date__gte=datetime.now().date(),
        status='Confirmed'
    ).order_by('appointment_date', 'appointment_time').first()
    
    # Get PHQ-9 assessments
    assessments = PHQ9Assessment.objects.filter(patient=patient).order_by('-assessment_date')
    latest_score = None
    improvement = None
    improvement_abs = None
    
    if assessments.exists():
        latest_score = assessments[0].score
        if len(assessments) > 1:
            improvement = latest_score - assessments[1].score
            improvement_abs = abs(improvement)
    
    total_assessments = assessments.count()
    
    context = {
        'patient': patient,
        'next_appointment': next_appointment,
        'latest_score': latest_score,
        'improvement': improvement,
        'improvement_abs': improvement_abs,
        'total_assessments': total_assessments,
    }
    
    return render(request, 'profile/patient_profile.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        patient = get_object_or_404(Patient, user=request.user)
        user = request.user
        
        # Update user info
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.gender = request.POST.get('gender')
        user.save()
        
        # Update patient info
        patient.contact_number = request.POST.get('phone')
        patient.address = request.POST.get('address')
        
        # Handle emergency contact
        patient.emergency_contact = request.POST.get('emergency_contact')
        
        # Handle profile image if provided
        if 'profile_image' in request.FILES:
            image = request.FILES['profile_image']
            # Check file extension
            if image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                patient.featured_image = image
            else:
                messages.error(request, 'Invalid image format. Only PNG, JPG and JPEG are allowed.')
                return redirect('patient_profile')
        
        patient.save()
        messages.success(request, 'Profile updated successfully!')
        
        return redirect('patient_profile')
    
    return redirect('patient_profile')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('patient_profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    return redirect('patient_profile')

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # Verify password
        if request.user.check_password(password):
            # Delete user account
            request.user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('login')
        else:
            messages.error(request, 'Incorrect password. Account not deleted.')
    
    return redirect('patient_profile')

@login_required
def patient_appointments(request):
    patient = get_object_or_404(Patient, user=request.user)
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date', '-appointment_time')
    
    data = [{
        'id': apt.id,
        'appointment_date': apt.appointment_date.isoformat(),
        'appointment_time': apt.appointment_time.strftime('%H:%M'),
        'doctor_name': apt.doctor.user.get_full_name(),
        'status': apt.status,
        'location': apt.location or 'Not specified'
    } for apt in appointments]
    
    return JsonResponse(data, safe=False)

@login_required
def appointment_pdf(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient__user=request.user)
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add content to PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, "Appointment Details")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, 700, f"Date: {appointment.appointment_date.strftime('%B %d, %Y')}")
    p.drawString(50, 680, f"Time: {appointment.appointment_time.strftime('%I:%M %p')}")
    p.drawString(50, 660, f"Status: {appointment.status}")
    
    p.drawString(50, 620, "Patient Information")
    p.drawString(70, 600, f"Name: {appointment.patient.user.get_full_name()}")
    p.drawString(70, 580, f"Email: {appointment.patient.user.email}")
    p.drawString(70, 560, f"Phone: {appointment.patient.contact_number}")
    
    p.drawString(50, 520, "Doctor Information")
    p.drawString(70, 500, f"Name: Dr. {appointment.doctor.user.get_full_name()}")
    p.drawString(70, 480, f"Specialization: {appointment.doctor.specialization}")
    p.drawString(70, 460, f"License: {appointment.doctor.license_number}")
    
    if appointment.notes:
        p.drawString(50, 420, "Notes:")
        p.drawString(70, 400, appointment.notes)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="appointment_{appointment_id}.pdf"'
    
    return response


@login_required
def doctor_settings(request):
    if not request.user.is_doctor():
        return redirect('home')
    return render(request, 'dashboard/doctor/settings.html')

@login_required
def doctor_availability_register(request, doctor_id):
    if not request.user.is_doctor():
        return redirect('home')
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.user != doctor.user:
        return redirect('doctor-settings')

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
        
        messages.success(request, 'Availability settings updated successfully!')
        return redirect('doctor-settings')

    return redirect('doctor-settings')