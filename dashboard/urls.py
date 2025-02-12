from django.urls import path
from . import views

urlpatterns = [
    path('doctor_dashboard', views.doctor_dashboard, name='dashboard-doctor'),
]
