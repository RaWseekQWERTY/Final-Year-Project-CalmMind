from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def chatbot_view(request):
    if not request.user.is_authenticated:
        return redirect('home')
    return render(request, 'auth_app/chat.html')