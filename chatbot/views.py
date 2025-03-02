from django.shortcuts import render

def chat(request):
    return render(request, 'chatbot/chat.html')