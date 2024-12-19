from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password


def home_view(request):
    return render(request, 'auth_app/home.html')

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        gender = request.POST.get("gender")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role="patient"

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "auth_app/register.html")

        # Create user
        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            gender=gender,
            role=role
        )
        if role == 'admin':
            user.is_staff = True
        user.set_password(password)  # Hash the password
        user.save()

        messages.success(request, "Registration successful. Please log in.")
        return redirect("login")

    return render(request, "auth_app/register.html")

def login_view(request):
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

        # Debugging output
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"User object: {user}")
        print(f"Is user active: {user.is_active if user else 'N/A'}")

    return render(request, "auth_app/login.html")

from django.http import JsonResponse
from django.contrib.auth import authenticate

# def test_auth_view(request):
#     username = "re"
#     password = "your_password"
#     user = authenticate(request, username=username, password=password)
#     return JsonResponse({
#         "user_authenticated": user is not None,
#         "is_active": user.is_active if user else None,
#     })


@login_required
def patient_dashboard(request):
    if request.user.is_patient():
        return render(request, "auth_app/patient.html")
    return HttpResponseForbidden("You are not authorized to view this page.")

@login_required
def doctor_dashboard(request):
    if request.user.is_doctor():
        return render(request, "auth_app/doctor.html")
    return HttpResponseForbidden("You are not authorized to view this page.")

@login_required
def admin_dashboard(request):
    if request.user.is_admin():
        return render(request, "auth_app/admin_dash.html")
    return HttpResponseForbidden("You are not authorized to view this page.")

def logout_view(request):
    logout(request)
    return redirect("login")