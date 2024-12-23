from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds an admin user in the database'

    def handle(self, *args, **options):
        username = 'admin' 
        email = 'admin@gmail.com' 
        password = '123'
        try:
            user = User.objects.create_superuser(username=username, email=email, password=password)
            user.role = 'admin'
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {username}'))
        except IntegrityError:
            self.stdout.write(self.style.WARNING(f'Admin user with username "{username}" already exists.'))