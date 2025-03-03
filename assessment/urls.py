from django.urls import path
from . import views

urlpatterns = [
    path('assessment/', views.assessment, name='assessment'),
    path('result/', views.result, name='result'),  # For latest assessment
    path('result/<int:assessment_id>/', views.result, name='result'),  # For specific assessment
]