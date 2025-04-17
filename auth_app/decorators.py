from django.core.exceptions import PermissionDenied

from django.core.exceptions import PermissionDenied

def doctor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'doctor':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper

def patient_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'patient':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper
