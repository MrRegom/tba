"""
Context processors para la app accounts.
Proporciona datos del usuario a todos los templates.
"""
from django.conf import settings


def user_photo(request):
    """
    Context processor que proporciona la foto de perfil del usuario.
    Disponible en todos los templates como 'user_photo_url'.
    """
    user_photo_url = f"{settings.STATIC_URL}images/users/avatar-1.jpg"
    
    if request.user and request.user.is_authenticated:
        try:
            from apps.accounts.models import Persona
            persona = Persona.objects.filter(
                user=request.user, 
                eliminado=False
            ).first()
            if persona and persona.foto_perfil:
                user_photo_url = persona.foto_perfil.url
        except Exception:
            pass
    
    return {
        'user_photo_url': user_photo_url
    }

