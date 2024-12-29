from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import User, Patient, Doctor

@receiver(pre_save, sender=User)
def handle_role_change(sender, instance, **kwargs):
    if instance.pk:  # Ensure it's an update, not a creation
        # Get the existing user instance from the database
        old_instance = sender.objects.get(pk=instance.pk)

        # Check if the role has changed
        if old_instance.role != instance.role:
            # Delete the old profile
            if old_instance.role == 'patient' and hasattr(old_instance, 'patient_profile'):
                old_instance.patient_profile.delete()
            elif old_instance.role == 'doctor' and hasattr(old_instance, 'doctor_profile'):
                old_instance.doctor_profile.delete()

            # Create a new profile based on the updated role
            if instance.role == 'patient':
                Patient.objects.get_or_create(user=instance)
            elif instance.role == 'doctor':
                Doctor.objects.get_or_create(user=instance)
