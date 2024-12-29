from django.urls import path
from . import views

urlpatterns = [
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('book-appointment/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
]
