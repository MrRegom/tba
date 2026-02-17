from allauth.account.adapter import DefaultAccountAdapter
from core.utils import get_client_ip

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Adaptador personalizado para manejar la resolución de IP de forma segura
    en entornos detrás de proxies (como Cloudflare/Nginx + Gunicorn).
    """

    def get_client_ip(self, request):
        """
        Sobrescribe el método original de allauth para evitar que lance
        PermissionDenied cuando no puede determinar la IP.
        """
        # Intentar usar nuestra utilidad centralizada
        ip = get_client_ip(request)
        
        if ip:
            return ip
            
        # Si falla, retornar una IP por defecto en lugar de romper el flujo
        # Esto es crítico para evitar errores 500/403 en producción
        return "127.0.0.1"
