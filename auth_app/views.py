from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import User,Patient,Doctor
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random
import string

User = get_user_model()

# Redirect logged-in users away from login/signup pages
def redirect_if_logged_in(user):
    return not user.is_authenticated


def home_view(request):
    context = {'role': getattr(request.user, 'role', None)}
    return render(request, 'auth_app/home.html', context)

def register_view(request):
    if request.user.is_authenticated:  # Check if the user is logged in
        return redirect('/')  # Redirect to the homepage or another page
    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name").capitalize() 
        last_name = request.POST.get("last_name").capitalize()
        email = request.POST.get("email")
        gender = "male"
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = "patient"

        # Validate required fields
        if not all([username, first_name, last_name, email, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return render(request, "auth_app/register.html")

        # Validate username length and characters
        if len(username) < 3:
            messages.error(request, "Username must be at least 3 characters long.")
            return render(request, "auth_app/register.html")
        if not username.isalnum():
            messages.error(request, "Username can only contain letters and numbers.")
            return render(request, "auth_app/register.html")

        # Validate email format
        if '@' not in email or '.' not in email:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "auth_app/register.html")

        # Validate password strength
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, "auth_app/register.html")
        if not any(char.isdigit() for char in password):
            messages.error(request, "Password must contain at least one number.")
            return render(request, "auth_app/register.html")
        if not any(char.isupper() for char in password):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return render(request, "auth_app/register.html")

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "auth_app/register.html")

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "auth_app/register.html")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "auth_app/register.html")

        # Validate name fields
        if not first_name.isalpha() or not last_name.isalpha():
            messages.error(request, "Names can only contain letters.")
            return render(request, "auth_app/register.html")

        try:
            # Create the user
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role="patient"
            )
            if role == "admin":
                user.is_staff = True

            user.set_password(password)  # Hash the password
            user.save()

            # Create associated Patient profile
            Patient.objects.create(user=user)

            messages.success(request, "Registration successful. Please log in.")
            return redirect("login")
            
        except Exception as e:
            messages.error(request, "An error occurred during registration. Please try again.")
            return render(request, "auth_app/register.html")

    return render(request, "auth_app/register.html")

def login_view(request):
    if request.user.is_authenticated:  # Check if the user is already logged in
        return redirect('/')  # Redirect to the homepage or another page

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            if user.is_active:  # Ensure the user is active
                login(request, user)
                # Redirect based on the 'next' parameter or user role
                next_url = request.POST.get('next', '/')
                if user.role == "patient":
                    return redirect(next_url) if next_url else redirect("dashboard-patient")
                elif user.role == "doctor":
                    return redirect(next_url) if next_url else redirect("dashboard-doctor")
                elif user.role == "admin":
                    return redirect(next_url) if next_url else redirect("admin_dashboard")
            else:
                messages.error(request, "Account is inactive.")
        else:
            messages.error(request, "Invalid username or password.")

    # Pass the 'next' parameter to the template for the hidden input field
    next_url = request.GET.get('next', '')
    return render(request, "auth_app/login.html", {'next': next_url})

@login_required
def patient_dashboard(request):
    if hasattr(request.user, 'doctor'):  # Check if the user is a doctor
        return redirect('doctor_dashboard')  # Redirect to the doctor dashboard
    
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return redirect('login')  # Redirect to login or another appropriate page if the patient does not exist

    return render(request, "auth_app/patient.html", {'patient': patient})

@login_required
def doctor_dashboard(request):
    if request.user.is_doctor():
        return render(request, "auth_app/doctor.html")
    return HttpResponseForbidden("You are not authorized to view this page.")


@login_required
def admin_dashboard(request):
    if not request.user.is_admin():
        return HttpResponseForbidden("You are not authorized to view this page.")
    users = User.objects.all()
    return render(request, "auth_app/admin_dash.html", {"users": users})


@login_required
def update_user_role_page(request, user_id):
    if not request.user.is_admin():
        return HttpResponseForbidden("You are not authorized to update user roles.")
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in [role[0] for role in User.ROLE_CHOICES]:
            user.role = new_role
            if new_role == 'patient':
                if hasattr(user, 'doctor_profile'):
                  user.doctor_profile.delete()
                Patient.objects.get_or_create(user=user)
            elif new_role == 'doctor':
               if hasattr(user, 'patient_profile'):
                  user.patient_profile.delete()
                  Doctor.objects.get_or_create(user=user)
            else:
                  if hasattr(user, 'doctor_profile'):
                      user.doctor_profile.delete()
                  if hasattr(user, 'patient_profile'):
                      user.patient_profile.delete()
            user.save()
            messages.success(request, f"User '{user.username}' role updated to {new_role}.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid role selected.')
    return render(request, "auth_app/update_role_page.html", {'user': user})



def logout_view(request):
    logout(request)
    return redirect("login")

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            otp = generate_otp()
            # Store OTP in session
            request.session['reset_otp'] = otp
            request.session['reset_email'] = email
            
            # Send email
            send_mail(
                'Password Reset OTP',
                f'Your OTP for password reset is: {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, "OTP has been sent to your email.")
            return redirect('verify_otp')
        except User.DoesNotExist:
            messages.error(request, "No user found with this email address.")
    
    return render(request, "auth_app/forgot_password.html")

def verify_otp(request):
    # Check if user has a reset email in session
    if 'reset_email' not in request.session:
        messages.error(request, "Please start the password reset process from the beginning.")
        return redirect('forgot_password')

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        stored_otp = request.session.get('reset_otp')
        
        if entered_otp == stored_otp:
            # Store a flag indicating OTP verification was successful
            request.session['otp_verified'] = True
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP")
    
    return render(request, "auth_app/verify_otp.html")

def reset_password(request):
    # Check if user has verified OTP
    if not request.session.get('otp_verified'):
        messages.error(request, "Please verify your OTP first.")
        return redirect('forgot_password')

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        email = request.session.get('reset_email')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "auth_app/reset_password.html")
        
        # Password validation
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long")
            return render(request, "auth_app/reset_password.html")
        if not any(char.isdigit() for char in password):
            messages.error(request, "Password must contain at least one number")
            return render(request, "auth_app/reset_password.html")
        if not any(char.isupper() for char in password):
            messages.error(request, "Password must contain at least one uppercase letter")
            return render(request, "auth_app/reset_password.html")
        
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            
            # Clear all session variables
            for key in ['reset_otp', 'reset_email', 'otp_verified']:
                if key in request.session:
                    del request.session[key]
            
            messages.success(request, "Password has been reset successfully")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "User not found")
    
    return render(request, "auth_app/reset_password.html")