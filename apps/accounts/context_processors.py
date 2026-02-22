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


def sidebar_nav(request):
    """
    Context processor que indica en qué sección del sidebar estamos.

    Detecta las páginas de Gestores para que el sidebar expanda el grupo
    correcto (Gestores) en lugar del grupo del módulo correspondiente.

    Variables inyectadas:
        nav_gs_sol  — Gestores › Solicitudes  (/solicitudes/ exacto)
        nav_gs_bod  — Gestores › Bodega       (/bodega/ exacto)
        nav_gs_comp — Gestores › Compras      (/compras/gestores/…)
        nav_gs_inv  — Gestores › Inventario   (/activos/gestores/…)
        nav_gs_org  — Gestores › Organización (/administracion/organizacion/…)
        nav_gs_usr  — Gestores › Usuarios     (/administracion/personal/…)
        nav_en_gestores — True cuando cualquiera de las anteriores es True
    """
    path = request.path

    gs_sol  = (path == '/solicitudes/')
    gs_bod  = (path == '/bodega/')
    gs_comp = path.startswith('/compras/gestores/')
    gs_inv  = path.startswith('/activos/gestores/')
    gs_org  = path.startswith('/administracion/organizacion/')
    gs_usr  = path.startswith('/administracion/personal/')

    return {
        'nav_gs_sol':      gs_sol,
        'nav_gs_bod':      gs_bod,
        'nav_gs_comp':     gs_comp,
        'nav_gs_inv':      gs_inv,
        'nav_gs_org':      gs_org,
        'nav_gs_usr':      gs_usr,
        'nav_en_gestores': gs_sol or gs_bod or gs_comp or gs_inv or gs_org or gs_usr,
    }

