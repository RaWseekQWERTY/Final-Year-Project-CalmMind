# Import necessary modules
from django.contrib import admin  # Django admin module
from django.urls import path       # URL routing
from auth_app.views import *  # Import views from the authentication app
from django.conf import settings   # Application settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns  # Static files serving

# Define URL patterns
app_name = "auth_app"
urlpatterns = [
    path('', home, name="home_page"),      # Home page
    path('login/', login_page, name='login_page'),    # Login page
    path('register/', register_page, name='register'),  # Registration page
]