from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import User

@receiver(pre_save, sender=User)
def handle_role_change(sender, instance, **kwargs):
    if instance.pk:  # Only check for updates, not creation
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.role != instance.role:
            if old_instance.role == 'patient' and hasattr(instance, 'patient_profile'):
                instance.patient_profile.delete()
            elif old_instance.role == 'doctor' and hasattr(instance, 'doctor_profile'):
                instance.doctor_profile.delete()
