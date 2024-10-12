from .views import get_user_role_flags

def role_flags_processor(request):
    if request.user.is_authenticated:
        return get_user_role_flags(request.user)
    return {}
