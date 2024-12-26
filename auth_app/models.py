from django.db import models
from django.contrib.auth.models import User,AbstractUser, BaseUserManager,PermissionsMixin

from django.contrib.auth import get_user_model

ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
# Extend Django's default User model
class User(AbstractUser):

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    avatar = models.ImageField(max_length=100, blank=True, null=True,upload_to='images/user')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',  # Avoids conflict
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups"
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # Avoids conflict
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions"
    )

    def is_patient(self):
        return self.role == 'patient'

    def is_doctor(self):
        return self.role == 'doctor'

    def is_admin(self):
        return self.role == 'admin'

# Model for Patients
class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    featured_image = models.ImageField(upload_to='images/patients', default='patients/user-default.png', null=True, blank=True)
    # Chat
    #login_status = models.CharField(max_length=200, null=True, blank=True, default="offline")

    
    def __str__(self):
        return self.user.get_full_name()

# Model for Doctors
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    visiting_hour = models.TimeField(max_length=200, null=True, blank=True)
    consultation_fee = models.IntegerField(null=True, blank=True)
    featured_image = models.ImageField(upload_to='images/doctor', default='patients/user-default.png', null=True, blank=True)


    # Education
    institute = models.CharField(max_length=200, null=True, blank=True)
    degree = models.CharField(max_length=200, null=True, blank=True)
    completion_year = models.CharField(max_length=200, null=True, blank=True)

    # work experience
    work_place = models.CharField(max_length=200, null=True, blank=True)
    designation = models.CharField(max_length=200, null=True, blank=True)
    start_year = models.CharField(max_length=200, null=True, blank=True)
    end_year = models.CharField(max_length=200, null=True, blank=True)


    def __str__(self):
        return self.user.get_full_name()


