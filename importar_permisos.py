import os
import json
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

with open('/home/tba/permisos_inteligentes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    try:
        group = Group.objects.get(name=item['name'])
        group.permissions.clear()
        asignados = 0
        for p_data in item['permissions']:
            try:
                ct = ContentType.objects.get(app_label=p_data['app_label'], model=p_data['model'])
                perm = Permission.objects.get(content_type=ct, codename=p_data['codename'])
                group.permissions.add(perm)
                asignados += 1
            except Exception as e:
                pass
        print(f"Rol '{group.name}': {asignados} permisos asignados correctamente.")
    except Group.DoesNotExist:
        print(f"Rol '{item['name']}' no existe en Producción.")
