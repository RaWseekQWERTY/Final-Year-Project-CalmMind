from django.db import models
from django.utils.timezone import now
from auth_app.models import Patient 

class ChatLog(models.Model):
    chatID = models.AutoField(primary_key=True)  
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='patient_chat_logs')  
    message = models.TextField()  # User's input message
    response = models.TextField()  # Chatbot's response
    intent = models.CharField(max_length=255)  
    timestamp = models.DateTimeField(default=now) 
    
    def __str__(self):
        return f"ChatLog {self.chatID} - Patient: {self.patient.user.username}, Intent: {self.intent}"
