from django.urls import re_path
from chatbot.consumers import ChatbotConsumer  # Fine-tuned chatbot consumer
from appointment_chatbot.consumers import AppointmentChatbotConsumer  # Appointment chatbot consumer

websocket_urlpatterns = [
    re_path(r'ws/chatbot/$', ChatbotConsumer.as_asgi()),  # Fine-tuned chatbot
    re_path(r'ws/appointment_chatbot/$', AppointmentChatbotConsumer.as_asgi()),  # Appointment chatbot
]