from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def employee_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.profile.is_employee:
            messages.error(request, 'This action requires employee privileges.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def regular_user_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.profile.is_employee:
            messages.error(request, 'This action is only available to regular users.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
