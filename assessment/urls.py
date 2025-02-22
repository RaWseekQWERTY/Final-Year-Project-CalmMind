from django.urls import path
from . import views

urlpatterns = [
    path('assessment/', views.assessment, name='assessment'),
]
