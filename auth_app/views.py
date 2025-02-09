from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import User,Patient,Doctor
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

# Redirect logged-in users away from login/signup pages
def redirect_if_logged_in(user):
    return not user.is_authenticated


def home_view(request):
    if request.user.is_authenticated:
        context = {'role': request.user.role}
        return render(request, 'auth_app/home.html', context)
    else:
        return render(request, 'auth_app/home.html')
def register_view(request):
    if request.user.is_authenticated:  # Check if the user is logged in
        return redirect('/')  # Redirect to the homepage or another page
    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        gender = "male"
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = "patient"

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

        # Create the user
        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        if role == "admin":
            user.is_staff = True

        user.set_password(password)  # Hash the password
        user.save()

        # Create associated Patient profile
        Patient.objects.create(user=user)

        messages.success(request, "Registration successful. Please log in.")
        return redirect("login")

    return render(request, "auth_app/register.html")

def login_view(request):
    if request.user.is_authenticated:  # Check if the user is logged in
        return redirect('/')  # Redirect to the homepage or another page
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            if user.is_active:  # Ensure the user is active
                login(request, user)
                if user.role == "patient":
                    return redirect("patient_dashboard")
                elif user.role == "doctor":
                    return redirect("doctor_dashboard")
                elif user.role == "admin":
                    return redirect("admin_dashboard")
            else:
                messages.error(request, "Account is inactive.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "auth_app/login.html")

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