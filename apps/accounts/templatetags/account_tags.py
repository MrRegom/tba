"""
Template tags para la app accounts.
"""
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def get_user_photo(user):
    """
    Obtiene la foto de perfil del usuario.
    Retorna la URL de la foto si existe, o una imagen por defecto.
    """
    if not user or not user.is_authenticated:
        return f"{settings.STATIC_URL}images/users/avatar-1.jpg"
    
    try:
        from apps.accounts.models import Persona
        persona = Persona.objects.filter(user=user, eliminado=False).first()
        if persona and persona.foto_perfil:
            return persona.foto_perfil.url
    except Exception:
        pass
    
    return f"{settings.STATIC_URL}images/users/avatar-1.jpg"

