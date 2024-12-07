from django.db import models
from django.contrib.auth.models import User

class test_db(models.Model):
    username = models.CharField(max_length=60)