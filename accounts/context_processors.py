from .models import Profile


def profile_context(request):
    profile = None
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = None
    return {'user_profile': profile}
