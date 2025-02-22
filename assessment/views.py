from django.shortcuts import render

def assessment(request):
    return render(request, 'assessment/depression_test.html')