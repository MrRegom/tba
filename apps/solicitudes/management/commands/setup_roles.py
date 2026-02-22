"""
Comando para crear y configurar roles (Groups) del módulo de solicitudes.

Define todos los roles del sistema con sus permisos correspondientes.
Idempotente: se puede ejecutar múltiples veces sin duplicar datos.

Roles definidos:
    - Solicitante          → Solo puede crear y ver sus propias solicitudes
                             (Solicitud Artículos, Solicitud Bienes, Mis Solicitudes)
    - Gestor de Solicitudes → Administración completa del módulo
    - Aprobador            → Puede aprobar y rechazar solicitudes
    - Despachador          → Puede despachar solicitudes aprobadas

Uso:
    python manage.py setup_roles
    python manage.py setup_roles --verbose
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Crea y configura roles (Groups) del módulo de solicitudes con sus permisos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra detalle de cada permiso asignado',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Limpia los permisos existentes antes de reasignar (no elimina el grupo)',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.reset = options['reset']

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n========================================================'
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '   CONFIGURACIÓN DE ROLES - MÓDULO SOLICITUDES'
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '========================================================\n'
        ))

        # Definición de roles y sus permisos
        # Formato: { nombre_grupo: { descripcion, permisos: [codename, ...] } }
        roles = self._definir_roles()

        total_creados = 0
        total_actualizados = 0

        for nombre_rol, config in roles.items():
            creado, actualizado = self._procesar_rol(nombre_rol, config)
            if creado:
                total_creados += 1
            if actualizado:
                total_actualizados += 1

        # Resumen final
        self.stdout.write('\n' + '=' * 56)
        self.stdout.write(self.style.SUCCESS(f'Roles creados:      {total_creados}'))
        self.stdout.write(self.style.SUCCESS(f'Roles actualizados: {total_actualizados}'))
        self.stdout.write(self.style.SUCCESS(
            '\n[OK] Configuración de roles completada exitosamente!'
        ))
        self.stdout.write('=' * 56 + '\n')

    # ------------------------------------------------------------------ #
    #  Definición de roles                                                 #
    # ------------------------------------------------------------------ #

    def _definir_roles(self) -> dict:
        """
        Retorna el diccionario con la definición de todos los roles.

        Permisos de Django estándar para Solicitud:
            add_solicitud, change_solicitud, delete_solicitud, view_solicitud

        Permisos personalizados (definidos en Solicitud.Meta.permissions):
            Gestión:
                gestionar_solicitudes, aprobar_solicitudes, rechazar_solicitudes,
                despachar_solicitudes, ver_todas_solicitudes,
                editar_cualquier_solicitud, eliminar_cualquier_solicitud
            Solicitud Artículos:
                crear_solicitud_articulos, ver_solicitudes_articulos
            Solicitud Bienes:
                crear_solicitud_bienes, ver_solicitudes_bienes
            Mis Solicitudes:
                ver_mis_solicitudes, editar_mis_solicitudes, eliminar_mis_solicitudes
        """
        return {
            # ----------------------------------------------------------
            # ROL: Solicitante
            # Puede crear solicitudes de artículos y bienes, y gestionar
            # únicamente sus propias solicitudes. Sin acceso a gestión.
            # ----------------------------------------------------------
            'Solicitante': {
                'descripcion': (
                    'Usuario que puede crear solicitudes de artículos y bienes, '
                    'y gestionar solo sus propias solicitudes.'
                ),
                'permisos': [
                    # Acceso básico al módulo
                    'solicitudes.view_solicitud',
                    'solicitudes.add_solicitud',

                    # Módulo: Solicitud de Artículos
                    'solicitudes.ver_solicitudes_articulos',
                    'solicitudes.crear_solicitud_articulos',

                    # Módulo: Solicitud de Bienes
                    'solicitudes.ver_solicitudes_bienes',
                    'solicitudes.crear_solicitud_bienes',

                    # Módulo: Mis Solicitudes
                    'solicitudes.ver_mis_solicitudes',
                    'solicitudes.editar_mis_solicitudes',
                    'solicitudes.eliminar_mis_solicitudes',

                    # Vistas auxiliares necesarias (catálogos de solo lectura)
                    'solicitudes.view_estadosolicitud',
                    'solicitudes.view_tiposolicitud',
                    'solicitudes.add_historialsolicitud',
                    'solicitudes.view_historialsolicitud',
                ],
            },

            # ----------------------------------------------------------
            # ROL: Aprobador
            # Puede ver todas las solicitudes y aprobar/rechazar.
            # ----------------------------------------------------------
            'Aprobador de Solicitudes': {
                'descripcion': (
                    'Puede revisar todas las solicitudes y aprobarlas o rechazarlas.'
                ),
                'permisos': [
                    'solicitudes.view_solicitud',
                    'solicitudes.ver_todas_solicitudes',
                    'solicitudes.aprobar_solicitudes',
                    'solicitudes.rechazar_solicitudes',
                    'solicitudes.view_estadosolicitud',
                    'solicitudes.view_tiposolicitud',
                    'solicitudes.add_historialsolicitud',
                    'solicitudes.view_historialsolicitud',
                ],
            },

            # ----------------------------------------------------------
            # ROL: Despachador
            # Puede despachar solicitudes aprobadas.
            # ----------------------------------------------------------
            'Despachador de Solicitudes': {
                'descripcion': (
                    'Puede ver solicitudes aprobadas y registrar el despacho de materiales.'
                ),
                'permisos': [
                    'solicitudes.view_solicitud',
                    'solicitudes.ver_todas_solicitudes',
                    'solicitudes.despachar_solicitudes',
                    'solicitudes.view_estadosolicitud',
                    'solicitudes.view_tiposolicitud',
                    'solicitudes.add_historialsolicitud',
                    'solicitudes.view_historialsolicitud',
                ],
            },

            # ----------------------------------------------------------
            # ROL: Gestor de Solicitudes
            # Administración completa del módulo.
            # ----------------------------------------------------------
            'Gestor de Solicitudes': {
                'descripcion': (
                    'Administración completa: puede ver, editar, aprobar, rechazar '
                    'y despachar cualquier solicitud, además de gestionar mantenedores.'
                ),
                'permisos': [
                    # Acceso y gestión completa
                    'solicitudes.view_solicitud',
                    'solicitudes.add_solicitud',
                    'solicitudes.change_solicitud',
                    'solicitudes.delete_solicitud',

                    # Permisos de gestión
                    'solicitudes.gestionar_solicitudes',
                    'solicitudes.ver_todas_solicitudes',
                    'solicitudes.aprobar_solicitudes',
                    'solicitudes.rechazar_solicitudes',
                    'solicitudes.despachar_solicitudes',
                    'solicitudes.editar_cualquier_solicitud',
                    'solicitudes.eliminar_cualquier_solicitud',

                    # Módulos específicos
                    'solicitudes.ver_solicitudes_articulos',
                    'solicitudes.crear_solicitud_articulos',
                    'solicitudes.ver_solicitudes_bienes',
                    'solicitudes.crear_solicitud_bienes',
                    'solicitudes.ver_mis_solicitudes',
                    'solicitudes.editar_mis_solicitudes',
                    'solicitudes.eliminar_mis_solicitudes',

                    # Mantenedores
                    'solicitudes.view_estadosolicitud',
                    'solicitudes.add_estadosolicitud',
                    'solicitudes.change_estadosolicitud',
                    'solicitudes.delete_estadosolicitud',
                    'solicitudes.view_tiposolicitud',
                    'solicitudes.add_tiposolicitud',
                    'solicitudes.change_tiposolicitud',
                    'solicitudes.delete_tiposolicitud',

                    # Historial
                    'solicitudes.view_historialsolicitud',
                    'solicitudes.add_historialsolicitud',
                    'solicitudes.change_historialsolicitud',
                    'solicitudes.delete_historialsolicitud',
                ],
            },
        }

    # ------------------------------------------------------------------ #
    #  Lógica de procesamiento                                             #
    # ------------------------------------------------------------------ #

    def _procesar_rol(self, nombre: str, config: dict) -> tuple[bool, bool]:
        """
        Crea o actualiza un grupo y asigna sus permisos.

        Returns:
            (creado: bool, actualizado: bool)
        """
        grupo, creado = Group.objects.get_or_create(name=nombre)

        if creado:
            self.stdout.write(self.style.SUCCESS(f'\n[+] ROL CREADO: {nombre}'))
        else:
            self.stdout.write(self.style.WARNING(f'\n[*] ROL EXISTENTE: {nombre}'))

        if self.reset and not creado:
            grupo.permissions.clear()
            self.stdout.write('    >> Permisos anteriores limpiados (--reset)')

        # Resolver y asignar permisos
        permisos_asignados = 0
        permisos_no_encontrados = []

        for perm_str in config['permisos']:
            permiso = self._resolver_permiso(perm_str)
            if permiso:
                grupo.permissions.add(permiso)
                permisos_asignados += 1
                if self.verbose:
                    self.stdout.write(f'    [OK] {perm_str}')
            else:
                permisos_no_encontrados.append(perm_str)
                self.stdout.write(
                    self.style.ERROR(f'    [!] Permiso no encontrado: {perm_str}')
                )

        extra = f', {len(permisos_no_encontrados)} no encontrados' if permisos_no_encontrados else ''
        self.stdout.write(f'    >> {permisos_asignados} permisos asignados{extra}')

        return creado, not creado

    def _resolver_permiso(self, perm_str: str):
        """
        Resuelve 'app_label.codename' al objeto Permission de Django.

        Args:
            perm_str: Formato 'app_label.codename' (ej: 'solicitudes.ver_mis_solicitudes')

        Returns:
            Permission instance o None si no existe.
        """
        try:
            app_label, codename = perm_str.split('.', 1)
            return Permission.objects.get(
                codename=codename,
                content_type__app_label=app_label,
            )
        except Permission.DoesNotExist:
            return None
        except (ValueError, Permission.MultipleObjectsReturned) as e:
            self.stdout.write(
                self.style.ERROR(f'    [ERROR] Al resolver "{perm_str}": {e}')
            )
            return None
