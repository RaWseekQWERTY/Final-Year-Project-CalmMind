from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('chat/', views.chat, name='chat'),
     path('chatbot-test/', TemplateView.as_view(template_name='chatbot/chatbot_test.html'), name='chatbot_test'),
]