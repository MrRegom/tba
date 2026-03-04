from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.fotocopiadora.models import FotocopiadoraEquipo, TrabajoFotocopia
from apps.solicitudes.models import Area, Departamento


class TrabajoFotocopiaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='operador', password='test123')
        self.equipo = FotocopiadoraEquipo.objects.create(
            codigo='FC-01',
            nombre='Fotocopiadora Central',
            ubicacion='Biblioteca',
        )
        self.departamento = Departamento.objects.create(codigo='DEP-T', nombre='Docencia')
        self.area = Area.objects.create(codigo='AR-T', nombre='Matematica', departamento=self.departamento)

    def test_trabajo_interno_calcula_monto_cero(self):
        trabajo = TrabajoFotocopia(
            tipo_uso=TrabajoFotocopia.TipoUso.INTERNO,
            equipo=self.equipo,
            solicitante_usuario=self.user,
            solicitante_nombre='Profesor Prueba',
            departamento=self.departamento,
            cantidad_copias=50,
            precio_unitario=Decimal('25.00'),
        )
        trabajo.full_clean()
        trabajo.save()

        self.assertEqual(trabajo.monto_total, Decimal('0'))
        self.assertEqual(trabajo.precio_unitario, Decimal('0'))

    def test_trabajo_personal_exige_rut(self):
        trabajo = TrabajoFotocopia(
            tipo_uso=TrabajoFotocopia.TipoUso.PERSONAL,
            equipo=self.equipo,
            solicitante_usuario=self.user,
            solicitante_nombre='Alumno Prueba',
            cantidad_copias=10,
            precio_unitario=Decimal('30.00'),
        )

        with self.assertRaises(ValidationError):
            trabajo.full_clean()
