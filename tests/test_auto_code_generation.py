"""
Tests para la generación automática de códigos (AutoCodeMixin + generar_codigo_unico).

Cubre:
1. Unit tests de `generar_codigo_unico`
2. Unit tests de `AutoCodeMixin`
3. Tests de formularios (codigo excluido)
4. Tests de integración end-to-end
"""

import re
import pytest
from unittest.mock import patch, MagicMock
from django.db import IntegrityError

from core.utils.business import generar_codigo_unico
from core.models import AutoCodeMixin

# Modelos reales usados como sujetos de prueba
from apps.activos.models import (
    Ubicacion,
    Proveniencia,
    Marca as MarcaActivos,
    CategoriaActivo,
    Taller,
)
from apps.bodega.models import (
    Categoria as CategoriaBodega,
    UnidadMedida,
    Marca as MarcaBodega,
)
from apps.activos.forms import (
    UbicacionForm,
    CategoriaActivoForm,
    MarcaForm as MarcaActivosForm,
)
from apps.bodega.forms import CategoriaForm, MarcaForm as MarcaBodegaForm, ArticuloForm


pytestmark = pytest.mark.django_db


# ============================================================
# HELPERS
# ============================================================

FORMAT_RE = re.compile(r"^[A-Z]{2,4}-\d{6}$")


def assert_codigo_format(codigo: str, prefix: str):
    """Verifica que el código tiene formato PREFIX-NNNNNN."""
    assert codigo.startswith(f"{prefix}-"), (
        f"Código '{codigo}' no empieza con '{prefix}-'"
    )
    sufijo = codigo[len(prefix) + 1 :]
    assert sufijo.isdigit() and len(sufijo) == 6, (
        f"Sufijo '{sufijo}' no tiene exactamente 6 dígitos"
    )


# ============================================================
# 1. UNIT TESTS — generar_codigo_unico
# ============================================================


class TestGenerarCodigoUnico:
    """Pruebas unitarias de la función generar_codigo_unico."""

    @pytest.mark.unit
    def test_primer_codigo_sin_existentes(self):
        """Sin registros previos genera PREFIX-000001."""
        # No hay Ubicacion con prefijo TST aún
        # Usamos Ubicacion pero con un prefijo ficticio via mock de queryset
        # Para evitar colisión con datos reales, usamos CategoriaBodega con prefix inexistente
        codigo = generar_codigo_unico("ZZZ", Ubicacion, "codigo", 6)
        assert codigo == "ZZZ-000001"

    @pytest.mark.unit
    def test_siguiente_codigo_despues_de_uno(self):
        """Con CAT-000001 ya existente, genera CAT-000002."""
        # Crear una Ubicacion real con código UBI-000001
        Ubicacion.objects.create(codigo="UBI-TEST-A1", nombre="Sala A1")
        codigo = generar_codigo_unico("UBI-TEST", Ubicacion, "codigo", 6)
        assert codigo == "UBI-TEST-000002"

    @pytest.mark.unit
    def test_maneja_huecos_en_la_secuencia(self):
        """Con UBI-000001 y UBI-000003, el siguiente es UBI-000004."""
        Ubicacion.objects.create(codigo="HCO-000001", nombre="Sala B1")
        Ubicacion.objects.create(codigo="HCO-000003", nombre="Sala B3")
        codigo = generar_codigo_unico("HCO", Ubicacion, "codigo", 6)
        assert codigo == "HCO-000004"

    @pytest.mark.unit
    def test_sufijos_no_numericos_no_rompen_la_funcion(self):
        """Códigos como PREFIX-LEGACY no deben romper la numeración."""
        Ubicacion.objects.create(codigo="LEG-LEGACY", nombre="Sala Legacy")
        Ubicacion.objects.create(codigo="LEG-000002", nombre="Sala 2")
        # LEG-LEGACY no tiene sufijo numérico → se ignora, el máximo es 2
        codigo = generar_codigo_unico("LEG", Ubicacion, "codigo", 6)
        assert codigo == "LEG-000003"

    @pytest.mark.unit
    def test_prefijos_independientes_entre_si(self):
        """Cada prefijo tiene su propio contador independiente."""
        Ubicacion.objects.create(codigo="AAA-000001", nombre="Sala AAA 1")
        Ubicacion.objects.create(codigo="AAA-000002", nombre="Sala AAA 2")
        # Prefijo BBB no tiene registros → empieza en 1
        codigo_bbb = generar_codigo_unico("BBB", Ubicacion, "codigo", 6)
        assert codigo_bbb == "BBB-000001"
        # Prefijo AAA tiene 2 → siguiente es 3
        codigo_aaa = generar_codigo_unico("AAA", Ubicacion, "codigo", 6)
        assert codigo_aaa == "AAA-000003"

    @pytest.mark.unit
    def test_longitud_personalizada(self):
        """Respeta el parámetro `longitud` para el zero-padding."""
        codigo = generar_codigo_unico("XYZ", Ubicacion, "codigo", longitud=4)
        assert codigo == "XYZ-0001"

    @pytest.mark.unit
    def test_funciona_con_campo_distinto_a_codigo(self):
        """Puede operar sobre un campo diferente a 'codigo'."""
        # Usamos el campo 'nombre' solo para verificar que acepta otro campo
        # (el modelo no tiene unique en nombre, pero generar_codigo_unico no lo valida)
        codigo = generar_codigo_unico("NOM", Ubicacion, "nombre", 6)
        assert codigo == "NOM-000001"


# ============================================================
# 2. UNIT TESTS — AutoCodeMixin
# ============================================================


class TestAutoCodeMixin:
    """Pruebas unitarias del mixin usando modelos reales."""

    @pytest.mark.unit
    def test_codigo_autogenerado_al_crear_sin_codigo(self):
        """Al guardar sin código, se genera PREFIX-000001."""
        ub = Ubicacion(nombre="Sala Test Mixin")
        ub.save()
        assert_codigo_format(ub.codigo, "UBI")
        assert ub.pk is not None

    @pytest.mark.unit
    def test_codigo_preservado_si_ya_esta_establecido(self):
        """Si ya viene con un código, el mixin NO lo sobreescribe."""
        codigo_manual = "UBI-MANUAL"
        ub = Ubicacion(nombre="Sala Manual", codigo=codigo_manual)
        ub.save()
        assert ub.codigo == codigo_manual

    @pytest.mark.unit
    def test_codigo_no_cambia_al_editar(self):
        """Editar una instancia existente NO modifica su código."""
        ub = Ubicacion(nombre="Sala Original")
        ub.save()
        codigo_original = ub.codigo

        ub.nombre = "Sala Renombrada"
        ub.save()
        ub.refresh_from_db()

        assert ub.codigo == codigo_original

    @pytest.mark.unit
    def test_formato_codigo_es_correcto(self):
        """El código generado sigue el patrón PREFIX-NNNNNN."""
        ub = Ubicacion(nombre="Sala Formato")
        ub.save()
        assert_codigo_format(ub.codigo, "UBI")

    @pytest.mark.unit
    def test_numeracion_secuencial_tres_instancias(self):
        """Crear 3 instancias produce códigos correlativos."""
        u1 = Ubicacion(nombre="Sala Seq 1")
        u2 = Ubicacion(nombre="Sala Seq 2")
        u3 = Ubicacion(nombre="Sala Seq 3")
        u1.save()
        u2.save()
        u3.save()

        # Todos deben tener el prefijo UBI y ser distintos
        codigos = {u1.codigo, u2.codigo, u3.codigo}
        assert len(codigos) == 3, "Los códigos deben ser únicos"

        # Todos deben tener formato correcto
        for codigo in codigos:
            assert_codigo_format(codigo, "UBI")

        # Deben ser consecutivos (extraer números)
        numeros = sorted(int(c.split("-")[1]) for c in codigos)
        assert numeros == list(range(numeros[0], numeros[0] + 3))

    @pytest.mark.unit
    def test_prefijos_distintos_para_distintos_modelos(self):
        """Modelos diferentes usan prefijos distintos."""
        ub = Ubicacion(nombre="Sala Prov")
        pv = Proveniencia(nombre="Compra Directa")
        ub.save()
        pv.save()

        assert ub.codigo.startswith("UBI-")
        assert pv.codigo.startswith("PRV-")

    @pytest.mark.unit
    def test_retry_en_integrity_error(self):
        """Si super().save() lanza IntegrityError una vez, el mixin reintenta."""
        # Crear un registro previo con el código que el mock devuelve en 1er intento
        Ubicacion.objects.create(codigo="UBI-000001", nombre="Ya existe")

        call_count_gcr = {"n": 0}

        def fake_generar(prefijo, modelo, campo, longitud):
            call_count_gcr["n"] += 1
            if call_count_gcr["n"] == 1:
                return (
                    "UBI-000001"  # código que ya existe → provocará IntegrityError real
                )
            return "UBI-000999"  # 2do intento → código libre

        # La función es importada dentro de AutoCodeMixin.save() como:
        # from core.utils.business import generar_codigo_unico
        # Por eso parcheamos en el módulo donde se usa el nombre.
        with patch(
            "core.utils.business.generar_codigo_unico", side_effect=fake_generar
        ):
            ub = Ubicacion(nombre="Sala Retry")
            ub.save()

        # Se llamó 2 veces: 1ra provocó IntegrityError, 2da exitosa
        assert call_count_gcr["n"] == 2
        assert ub.codigo == "UBI-000999"

    @pytest.mark.unit
    def test_max_retries_agotados_lanza_integrity_error(self):
        """Después de MAX_RETRIES intentos fallidos, se propaga IntegrityError."""
        # Crear el registro bloqueador (siempre colisionará)
        Ubicacion.objects.create(codigo="UBI-000001", nombre="Bloqueador")

        def always_collide(prefijo, modelo, campo, longitud):
            return "UBI-000001"  # siempre devuelve código ocupado → IntegrityError en cada retry

        # Parchamos en core.utils.business porque AutoCodeMixin hace:
        # from core.utils.business import generar_codigo_unico (lazy, dentro del save)
        with patch(
            "core.utils.business.generar_codigo_unico", side_effect=always_collide
        ):
            ub = Ubicacion(nombre="Sala Agotada")
            with pytest.raises(IntegrityError):
                ub.save()


# ============================================================
# 3. TESTS DE FORMULARIOS — codigo excluido de fields
# ============================================================


class TestFormulariosSinCodigo:
    """Verifica que los formularios no exponen el campo 'codigo' al usuario."""

    @pytest.mark.unit
    def test_ubicacion_form_sin_codigo(self):
        """UbicacionForm (activos) NO tiene campo 'codigo'."""
        form = UbicacionForm()
        assert "codigo" not in form.fields, (
            "UbicacionForm no debe exponer 'codigo' — es auto-generado"
        )

    @pytest.mark.unit
    def test_categoria_activo_form_sin_codigo(self):
        """CategoriaActivoForm NO tiene campo 'codigo'."""
        form = CategoriaActivoForm()
        assert "codigo" not in form.fields

    @pytest.mark.unit
    def test_marca_activos_form_sin_codigo(self):
        """MarcaForm (activos) NO tiene campo 'codigo'."""
        form = MarcaActivosForm()
        assert "codigo" not in form.fields

    @pytest.mark.unit
    def test_categoria_bodega_form_sin_codigo(self):
        """CategoriaForm (bodega) NO tiene campo 'codigo'."""
        form = CategoriaForm()
        assert "codigo" not in form.fields

    @pytest.mark.unit
    def test_marca_bodega_form_sin_codigo(self):
        """MarcaForm (bodega) NO tiene campo 'codigo'."""
        form = MarcaBodegaForm()
        assert "codigo" not in form.fields

    @pytest.mark.unit
    def test_articulo_form_sin_codigo(self):
        """ArticuloForm (bodega) NO tiene campo 'codigo'."""
        form = ArticuloForm()
        assert "codigo" not in form.fields

    @pytest.mark.unit
    def test_ubicacion_form_valido_sin_codigo_genera_instancia(self):
        """UbicacionForm válido sin codigo → instancia guardada con código auto-generado."""
        form = UbicacionForm(
            data={
                "nombre": "Sala de Reuniones",
                "descripcion": "Sala principal",
                "activo": True,
            }
        )
        assert form.is_valid(), f"Errores de validación: {form.errors}"
        instancia = form.save()
        assert instancia.pk is not None
        assert_codigo_format(instancia.codigo, "UBI")

    @pytest.mark.unit
    def test_categoria_bodega_form_valido_sin_codigo_genera_instancia(self):
        """CategoriaForm válido sin codigo → instancia guardada con código auto-generado."""
        form = CategoriaForm(
            data={
                "nombre": "Papelería",
                "descripcion": "Artículos de papelería",
                "activo": True,
            }
        )
        assert form.is_valid(), f"Errores de validación: {form.errors}"
        instancia = form.save()
        assert instancia.pk is not None
        assert_codigo_format(instancia.codigo, "CAB")

    @pytest.mark.unit
    def test_marca_bodega_form_valido_sin_codigo_genera_instancia(self):
        """MarcaForm (bodega) válido sin codigo → instancia guardada con código auto-generado."""
        form = MarcaBodegaForm(
            data={
                "nombre": "Samsung",
                "descripcion": "Marca de electrónica",
                "activo": True,
            }
        )
        assert form.is_valid(), f"Errores de validación: {form.errors}"
        instancia = form.save()
        assert instancia.pk is not None
        assert_codigo_format(instancia.codigo, "MRB")


# ============================================================
# 4. INTEGRATION TESTS — end-to-end
# ============================================================


class TestIntegracionGeneracionCodigos:
    """Tests de integración que cubren el flujo completo de creación y edición."""

    @pytest.mark.integration
    def test_crear_ubicacion_via_form_save(self):
        """
        E2E: Crear Ubicacion via form.save() → código auto-generado con formato correcto.
        """
        form = UbicacionForm(
            data={
                "nombre": "Sala de Informática",
                "descripcion": "Sala principal",
                "activo": True,
            }
        )
        assert form.is_valid(), f"Errores: {form.errors}"
        ub = form.save()

        assert ub.pk is not None
        assert_codigo_format(ub.codigo, "UBI")
        ub_db = Ubicacion.objects.get(pk=ub.pk)
        assert ub_db.codigo == ub.codigo

    @pytest.mark.integration
    def test_codigos_secuenciales_en_creacion_multiple(self):
        """
        E2E: Crear dos Ubicaciones via form → códigos son secuenciales.
        """
        form1 = UbicacionForm(data={"nombre": "Sala 1", "activo": True})
        form2 = UbicacionForm(data={"nombre": "Sala 2", "activo": True})

        assert form1.is_valid(), f"Errores form1: {form1.errors}"
        assert form2.is_valid(), f"Errores form2: {form2.errors}"

        ub1 = form1.save()
        ub2 = form2.save()

        num1 = int(ub1.codigo.split("-")[1])
        num2 = int(ub2.codigo.split("-")[1])
        assert num2 == num1 + 1, (
            f"Los códigos deben ser consecutivos: {ub1.codigo} → {ub2.codigo}"
        )

    @pytest.mark.integration
    def test_editar_ubicacion_no_cambia_codigo(self):
        """
        E2E: Editar Ubicacion existente via form → código se preserva sin cambios.
        """
        # Crear instancia inicial
        form_crear = UbicacionForm(data={"nombre": "Sala Original", "activo": True})
        assert form_crear.is_valid()
        ub = form_crear.save()
        codigo_original = ub.codigo

        # Editar via form (nombre cambia, codigo no debe cambiar)
        form_editar = UbicacionForm(
            data={
                "nombre": "Sala Renombrada",
                "descripcion": "Nueva descripción",
                "activo": True,
            },
            instance=ub,
        )
        assert form_editar.is_valid(), f"Errores edición: {form_editar.errors}"
        ub_editado = form_editar.save()

        assert ub_editado.codigo == codigo_original
        ub_editado.refresh_from_db()
        assert ub_editado.codigo == codigo_original
        assert ub_editado.nombre == "Sala Renombrada"

    @pytest.mark.integration
    def test_instancias_de_distintos_modelos_tienen_prefijos_correctos(self):
        """
        E2E: Cada modelo usa su prefijo propio y ambos generan correctamente.
        """
        ub = Ubicacion(nombre="Sala Multi")
        pv = Proveniencia(nombre="Donación")
        ub.save()
        pv.save()

        assert ub.codigo.startswith("UBI-")
        assert pv.codigo.startswith("PRV-")
        assert_codigo_format(ub.codigo, "UBI")
        assert_codigo_format(pv.codigo, "PRV")

    @pytest.mark.integration
    def test_codigo_con_datos_preexistentes_en_db(self):
        """
        E2E: Con registros existentes en la DB, el nuevo código es el siguiente correcto.
        """
        # Crear registros manuales con códigos específicos
        CategoriaBodega.objects.create(codigo="CAB-000005", nombre="Electrónica")
        CategoriaBodega.objects.create(codigo="CAB-000003", nombre="Muebles")

        # Al crear una nueva Categoria sin código, debe ser CAB-000006
        cat_nueva = CategoriaBodega(nombre="Ropa")
        cat_nueva.save()

        assert cat_nueva.codigo == "CAB-000006"

    @pytest.mark.integration
    def test_codigo_existente_manual_no_sobreescrito(self):
        """
        E2E: Un registro con código manual pre-existente mantiene su código.
        El guard `if not self.codigo` garantiza que el mixin no sobreescribe.
        """
        codigo_legado = "SALA-LEGACY"
        # Crear con código explícito (simulando datos previos a la migración)
        ub = Ubicacion(nombre="Sala Legacy", codigo=codigo_legado)
        ub.save()

        ub.refresh_from_db()
        # El código manual se respeta — el mixin no interviene
        assert ub.codigo == codigo_legado

    @pytest.mark.integration
    def test_articulo_codigo_uuid_legado_no_sobreescrito(self):
        """
        E2E: Articulo.codigo (varchar 50) con UUID legado se preserva al editar.
        Simula el escenario real de artículos creados antes de la migración.
        """
        from apps.bodega.models import Articulo, Categoria, UnidadMedida
        from apps.bodega.models import Bodega
        from django.contrib.auth.models import User

        # Setup mínimo requerido para Articulo
        u = User.objects.create_user("test_art_user", password="pass!")
        bodega = Bodega.objects.create(
            codigo="BOD-UUID-TEST", nombre="Bodega Test", responsable=u
        )
        cat = Categoria.objects.create(codigo="CAB-UUID-TEST", nombre="Cat UUID")

        uuid_code = "550e8400-e29b-41d4-a716-446655440000"
        art = Articulo(
            nombre="Artículo Legacy",
            codigo=uuid_code,
            categoria=cat,
            ubicacion_fisica=bodega,
        )
        art.save()

        art.refresh_from_db()
        # El código UUID se preserva — el mixin ve que codigo ya está establecido
        assert art.codigo == uuid_code
