from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from apps.fotocopiadora.models import FotocopiadoraEquipo


class FotocopiadoraViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='viewer', password='test123')
        perm = Permission.objects.get(codename='view_trabajofotocopia')
        self.user.user_permissions.add(perm)
        FotocopiadoraEquipo.objects.create(codigo='FC-01', nombre='Equipo 1', ubicacion='Sala 1')

    def test_menu_requires_permission(self):
        self.client.login(username='viewer', password='test123')
        response = self.client.get(reverse('fotocopiadora:menu_fotocopiadora'))
        self.assertEqual(response.status_code, 200)
