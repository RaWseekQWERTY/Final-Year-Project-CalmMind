# Generated by Django 5.1.4 on 2025-02-12 09:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth_app', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_date', models.DateField()),
                ('appointment_time', models.TimeField()),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Cancelled', 'Cancelled')], default='Pending', max_length=10)),
                ('appointment_type', models.CharField(choices=[('Initial Consultation', 'Initial Consultation'), ('Follow-Up', 'Follow-Up'), ('Therapy Session', 'Therapy Session')], default='Initial Consultation', max_length=20)),
                ('notes', models.TextField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='auth_app.doctor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='auth_app.patient')),
            ],
        ),
        migrations.CreateModel(
            name='DoctorAvailability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visiting_hours_start', models.TimeField(blank=True, null=True)),
                ('visiting_hours_end', models.TimeField(blank=True, null=True)),
                ('consultation_fee', models.IntegerField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('doctor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='information', to='auth_app.doctor')),
            ],
        ),
    ]
