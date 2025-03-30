from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def chatbot_view(request):
    return render(request, 'chatbot/chat.html')