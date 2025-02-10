from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from auth_app.models import User, Doctor, Patient

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'gender', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def save_model(self, request, obj, form, change):
        # Check if the role is being changed
        if change and 'role' in form.changed_data:
            if obj.role == 'doctor':
                # Ensure the user does not already have a Doctor profile
                if not hasattr(obj, 'doctor_profile'):
                    # Create a Doctor instance with a default license number and image
                    Doctor.objects.create(
                        user=obj,
                        license_number=f"DOC-{obj.id}",  # Generate a unique license number
                        specialization="General Practitioner",  # Default specialization
                        featured_image="images/doctors/doc-def.png"  # Default doctor image
                    )
                # Update the user's featured_image to the default doctor image
                obj.featured_image = "images/doctors/doc-def.png"
            elif obj.role == 'patient':
                # Ensure the user does not already have a Patient profile
                if not hasattr(obj, 'patient_profile'):
                    # Create a Patient instance with a default image
                    Patient.objects.create(
                        user=obj,
                        featured_image="images/patients/def-avatar.jpg"  # Default patient image
                    )
                # Update the user's featured_image to the default patient image
                obj.featured_image = "images/patients/def-avatar.jpg"

        super().save_model(request, obj, form, change)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Doctor)
admin.site.register(Patient)