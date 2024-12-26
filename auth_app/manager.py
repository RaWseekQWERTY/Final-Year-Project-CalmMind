from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username,password=None, **kwargs):
        if not username:
            raise ValueError("Users must have a username")
        kwargs['email'] = self.normalize_email('email')
        kwargs['role'] = 'patient'
        user = self.model(username=username, **kwargs)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, username, password, **kwargs):
        kwargs['is_staff'] = True
        kwargs['is_superuser'] = True
        kwargs['role'] = 'admin'
        return self.create_user(username, password, **kwargs)