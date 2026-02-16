"""
Formularios del módulo de activos.

Define los formularios para la gestión de activos, incluyendo:
- Catálogos: Categorías, Estados, Ubicaciones, Marcas, Talleres, Proveniencias
- Gestión de Activos y Movimientos
"""
from __future__ import annotations

from typing import Any

from django import forms
from django.contrib.auth.models import User

from .models import (
    Activo, CategoriaActivo, EstadoActivo, Ubicacion,
    Proveniencia, Marca, Taller, TipoMovimientoActivo, MovimientoActivo
)


class CategoriaActivoForm(forms.ModelForm):
    """Formulario para crear y editar categorías de activos"""

    class Meta:
        model = CategoriaActivo
        fields = ['codigo', 'nombre', 'sigla', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: COMP'}
            ),
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Computadoras'}
            ),
            'sigla': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: NTB, LCD, ESC',
                    'maxlength': '3',
                    'style': 'text-transform: uppercase;'
                }
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la categoría...'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
        labels = {
            'sigla': 'Sigla (3 caracteres)',
            'activo': 'Activo',
        }
        help_texts = {
            'sigla': 'Sigla de 3 caracteres para generación automática de códigos (ej: NTB para Notebook, LCD para Monitor)',
        }


class EstadoActivoForm(forms.ModelForm):
    """
    Formulario para crear y editar estados de activos.
    
    Incluye validación de código único y color en formato hexadecimal.
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Inicializa el formulario.
        
        Guarda el pk original de la instancia para la validación de unicidad.
        """
        super().__init__(*args, **kwargs)
        # Guardar el pk original si existe (para validación de unicidad)
        self._original_pk = self.instance.pk if self.instance and self.instance.pk else None

    class Meta:
        model = EstadoActivo
        fields = ['codigo', 'nombre', 'descripcion', 'color', 'es_inicial', 'permite_movimiento', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: ACTIVO',
                    'maxlength': '20'
                }
            ),
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: Activo',
                    'maxlength': '100'
                }
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'color': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'type': 'color',
                    'value': '#6c757d'
                }
            ),
            'es_inicial': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'permite_movimiento': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }

    def clean_codigo(self) -> str:
        """
        Validar que el código sea único (en mayúsculas).
        
        Al editar, excluye la instancia actual de la validación de unicidad.
        """
        from django.core.exceptions import ValidationError
        
        codigo = self.cleaned_data.get('codigo', '').strip().upper()

        if not codigo:
            raise ValidationError('El código es obligatorio.')

        # Construir queryset para validar unicidad
        # Solo considerar estados no eliminados
        queryset = EstadoActivo.objects.filter(
            codigo=codigo,
            eliminado=False
        )
        
        # Si estamos editando (tenemos un pk original), excluir la instancia actual
        # Verificar tanto _original_pk como instance.pk por si acaso
        pk_a_excluir = self._original_pk
        
        # Si _original_pk no está disponible, intentar obtenerlo de instance
        if pk_a_excluir is None and self.instance and hasattr(self.instance, 'pk'):
            pk_a_excluir = self.instance.pk
        
        if pk_a_excluir is not None:
            queryset = queryset.exclude(pk=pk_a_excluir)

        if queryset.exists():
            raise ValidationError(
                f'Ya existe un estado con el código "{codigo}".'
            )

        return codigo

    def clean_color(self) -> str:
        """Validar formato hexadecimal del color."""
        from django.core.exceptions import ValidationError
        
        color = self.cleaned_data.get('color', '').strip()

        if not color:
            # Si no se proporciona, usar el valor por defecto
            return '#6c757d'

        # Validar formato hexadecimal
        if not color.startswith('#') or len(color) != 7:
            raise ValidationError('El color debe estar en formato hexadecimal (#RRGGBB).')

        # Validar que sean caracteres hexadecimales válidos
        try:
            int(color[1:], 16)
        except ValueError:
            raise ValidationError('El color contiene caracteres hexadecimales inválidos.')

        return color

    def clean_nombre(self) -> str:
        """Limpiar y validar el nombre."""
        from django.core.exceptions import ValidationError
        
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        return nombre


class ActivoForm(forms.ModelForm):
    """
    Formulario para crear y editar activos.

    Los activos son bienes individuales que NO manejan stock.
    Cada activo es único y se rastrea individualmente.
    El código se genera automáticamente en formato CCCNNNNN-NNN.
    """

    codigo = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Se generará automáticamente (ej: NTB01437-001)',
                'readonly': 'readonly'
            }
        ),
        help_text='Se genera automáticamente según categoría y RBD del establecimiento'
    )

    class Meta:
        model = Activo
        fields = [
            'codigo', 'nombre', 'descripcion',
            'categoria', 'estado', 'marca',
            'lote', 'numero_serie', 'codigo_barras',
            'precio_unitario', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Nombre del activo'}
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción detallada...'}
            ),
            'categoria': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'estado': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'marca': forms.Select(
                attrs={'class': 'form-select', 'id': 'id_marca'}
            ),
            'lote': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Lote (opcional)'}
            ),
            'numero_serie': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Número de serie'}
            ),
            'codigo_barras': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Dejar vacío para auto-generar desde código'}
            ),
            'precio_unitario': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Inicializa el formulario y configura querysets filtrados."""
        super().__init__(*args, **kwargs)
        # Filtrar solo registros activos para los selectores
        self.fields['categoria'].queryset = CategoriaActivo.objects.filter(
            activo=True, eliminado=False
        )
        self.fields['estado'].queryset = EstadoActivo.objects.filter(activo=True)
        self.fields['marca'].queryset = Marca.objects.filter(activo=True, eliminado=False)

        # Marca es opcional
        self.fields['marca'].required = False


class UbicacionForm(forms.ModelForm):
    """Formulario para crear y editar ubicaciones físicas."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Inicializa el formulario.
        
        Guarda el pk original de la instancia para la validación de unicidad.
        """
        super().__init__(*args, **kwargs)
        # Guardar el pk original si existe (para validación de unicidad)
        self._original_pk = self.instance.pk if self.instance and self.instance.pk else None

    class Meta:
        model = Ubicacion
        fields = ['codigo', 'nombre', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: UB001'}
            ),
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Oficina Principal'}
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la ubicación...'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
    
    def clean_codigo(self) -> str:
        """
        Validar que el código sea único (en mayúsculas).
        
        Al editar, excluye la instancia actual de la validación de unicidad.
        """
        from django.core.exceptions import ValidationError
        
        codigo = self.cleaned_data.get('codigo', '').strip().upper()

        if not codigo:
            raise ValidationError('El código es obligatorio.')

        # Construir queryset para validar unicidad
        # Solo considerar ubicaciones no eliminadas
        queryset = Ubicacion.objects.filter(
            codigo=codigo,
            eliminado=False
        )
        
        # Si estamos editando (tenemos un pk original), excluir la instancia actual
        pk_a_excluir = self._original_pk
        
        # Si _original_pk no está disponible, intentar obtenerlo de instance
        if pk_a_excluir is None and self.instance and hasattr(self.instance, 'pk'):
            pk_a_excluir = self.instance.pk
        
        if pk_a_excluir is not None:
            queryset = queryset.exclude(pk=pk_a_excluir)

        if queryset.exists():
            raise ValidationError(
                f'Ya existe una ubicación con el código "{codigo}".'
            )

        return codigo
    
    def clean_nombre(self) -> str:
        """Validar que el nombre no esté vacío."""
        from django.core.exceptions import ValidationError
        
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        return nombre


class TipoMovimientoActivoForm(forms.ModelForm):
    """Formulario para crear y editar tipos de movimiento."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Inicializa el formulario.
        
        Guarda el pk original de la instancia para la validación de unicidad.
        """
        super().__init__(*args, **kwargs)
        # Guardar el pk original si existe (para validación de unicidad)
        self._original_pk = self.instance.pk if self.instance and self.instance.pk else None

    class Meta:
        model = TipoMovimientoActivo
        fields = ['codigo', 'nombre', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: ASIG'}
            ),
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Asignación'}
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
    
    def clean_codigo(self) -> str:
        """
        Validar que el código sea único (en mayúsculas).
        
        Al editar, excluye la instancia actual de la validación de unicidad.
        """
        from django.core.exceptions import ValidationError
        
        codigo = self.cleaned_data.get('codigo', '').strip().upper()

        if not codigo:
            raise ValidationError('El código es obligatorio.')

        # Construir queryset para validar unicidad
        # Solo considerar tipos de movimiento no eliminados
        queryset = TipoMovimientoActivo.objects.filter(
            codigo=codigo,
            eliminado=False
        )
        
        # Si estamos editando (tenemos un pk original), excluir la instancia actual
        pk_a_excluir = self._original_pk
        
        # Si _original_pk no está disponible, intentar obtenerlo de instance
        if pk_a_excluir is None and self.instance and hasattr(self.instance, 'pk'):
            pk_a_excluir = self.instance.pk
        
        if pk_a_excluir is not None:
            queryset = queryset.exclude(pk=pk_a_excluir)

        if queryset.exists():
            raise ValidationError(
                f'Ya existe un tipo de movimiento con el código "{codigo}".'
            )

        return codigo
    
    def clean_nombre(self) -> str:
        """Validar que el nombre no esté vacío."""
        from django.core.exceptions import ValidationError
        
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        return nombre


class MovimientoActivoForm(forms.ModelForm):
    """
    Formulario para registrar movimientos de activos individuales.

    Cada movimiento registra la trazabilidad del activo:
    ubicación, responsable, taller asociado, proveniencia, etc.
    """

    class Meta:
        model = MovimientoActivo
        fields = [
            'activo', 'estado_nuevo', 'ubicacion_destino', 'taller',
            'responsable', 'proveniencia', 'observaciones'
        ]
        widgets = {
            'activo': forms.Select(
                attrs={'class': 'form-select', 'id': 'id_activo'}
            ),
            'estado_nuevo': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'ubicacion_destino': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'taller': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'responsable': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'proveniencia': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'observaciones': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones adicionales...'}
            ),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Inicializa el formulario configurando querysets filtrados."""
        super().__init__(*args, **kwargs)

        # Filtrar solo registros activos
        self.fields['activo'].queryset = Activo.objects.filter(
            activo=True, eliminado=False
        ).select_related('categoria', 'estado', 'marca')
        self.fields['estado_nuevo'].queryset = EstadoActivo.objects.filter(
            activo=True, eliminado=False
        )
        self.fields['ubicacion_destino'].queryset = Ubicacion.objects.filter(
            activo=True, eliminado=False
        )
        self.fields['taller'].queryset = Taller.objects.filter(
            activo=True, eliminado=False
        )
        self.fields['responsable'].queryset = User.objects.filter(
            is_active=True
        ).order_by('username')
        self.fields['proveniencia'].queryset = Proveniencia.objects.filter(
            activo=True, eliminado=False
        )

        # Campos opcionales
        # El campo 'activo' es opcional cuando se usan múltiples activos (viene en activos_seleccionados)
        self.fields['activo'].required = False
        self.fields['ubicacion_destino'].required = False
        self.fields['taller'].required = False
        self.fields['responsable'].required = False
        self.fields['proveniencia'].required = False
        
        # Agregar JavaScript para validación condicional de responsable
        # Si el estado es "Baja", el responsable no es requerido
        self.fields['estado_nuevo'].widget.attrs.update({
            'onchange': 'validarResponsableBaja(this)'
        })
        self.fields['responsable'].widget.attrs.update({
            'id': 'id_responsable_movimiento'
        })
    
    def clean(self) -> dict[str, Any]:
        """
        Validación personalizada del formulario.
        
        Si el estado es "Baja", el responsable no es requerido.
        Para otros estados, el responsable es opcional pero recomendado.
        El campo 'activo' es opcional cuando se usan múltiples activos.
        """
        cleaned_data = super().clean()
        estado_nuevo = cleaned_data.get('estado_nuevo')
        responsable = cleaned_data.get('responsable')
        activo = cleaned_data.get('activo')
        
        # Validar que haya al menos un activo (ya sea en el campo activo o en activos_seleccionados)
        # Esta validación se hace en la vista porque activos_seleccionados no es parte del formulario
        
        # Validar que estado_nuevo sea requerido
        if not estado_nuevo:
            from django.core.exceptions import ValidationError
            raise ValidationError({
                'estado_nuevo': 'El nuevo estado es obligatorio para registrar un movimiento.'
            })
        
        # Si el estado es "Baja", no requerir responsable
        if estado_nuevo and estado_nuevo.codigo.upper() == 'BAJA':
            # El responsable es opcional para bajas
            pass
        # Para otros estados, el responsable sigue siendo opcional
        # pero se puede agregar validación adicional si se requiere
        
        return cleaned_data


class FiltroActivosForm(forms.Form):
    """Formulario para filtrar activos en la lista"""

    categoria = forms.ModelChoiceField(
        queryset=CategoriaActivo.objects.filter(activo=True, eliminado=False),
        required=False,
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    estado = forms.ModelChoiceField(
        queryset=EstadoActivo.objects.filter(activo=True),
        required=False,
        empty_label='Todos los estados',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    buscar = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Buscar por código, nombre, marca...'
            }
        )
    )




class TallerForm(forms.ModelForm):
    """Formulario para crear y editar talleres de servicio."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Inicializa el formulario.
        
        Guarda el pk original de la instancia para la validación de unicidad.
        Configura querysets filtrados.
        """
        super().__init__(*args, **kwargs)
        # Guardar el pk original si existe (para validación de unicidad)
        self._original_pk = self.instance.pk if self.instance and self.instance.pk else None
        
        # Configurar querysets filtrados
        self.fields['responsable'].queryset = User.objects.filter(
            is_active=True
        ).order_by('username')
        self.fields['responsable'].required = False

    class Meta:
        model = Taller
        fields = ['codigo', 'nombre', 'descripcion', 'ubicacion', 'responsable', 'observaciones', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: TALL01'}
            ),
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Taller de Mantenimiento'}
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del taller...'}
            ),
            'ubicacion': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ubicación física del taller'}
            ),
            'responsable': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'observaciones': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones...'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
    
    def clean_codigo(self) -> str:
        """
        Validar que el código sea único (en mayúsculas).
        
        Al editar, excluye la instancia actual de la validación de unicidad.
        """
        from django.core.exceptions import ValidationError
        
        codigo = self.cleaned_data.get('codigo', '').strip().upper()

        if not codigo:
            raise ValidationError('El código es obligatorio.')

        # Construir queryset para validar unicidad
        # Solo considerar talleres no eliminados
        queryset = Taller.objects.filter(
            codigo=codigo,
            eliminado=False
        )
        
        # Si estamos editando (tenemos un pk original), excluir la instancia actual
        pk_a_excluir = self._original_pk
        
        # Si _original_pk no está disponible, intentar obtenerlo de instance
        if pk_a_excluir is None and self.instance and hasattr(self.instance, 'pk'):
            pk_a_excluir = self.instance.pk
        
        if pk_a_excluir is not None:
            queryset = queryset.exclude(pk=pk_a_excluir)

        if queryset.exists():
            raise ValidationError(
                f'Ya existe un taller con el código "{codigo}".'
            )

        return codigo
    
    def clean_nombre(self) -> str:
        """Validar que el nombre no esté vacío."""
        from django.core.exceptions import ValidationError
        
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        return nombre


class ProvenienciaForm(forms.ModelForm):
    """Formulario para crear y editar proveniencias de activos."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Inicializa el formulario.
        
        Guarda el pk original de la instancia para la validación de unicidad.
        """
        super().__init__(*args, **kwargs)
        # Guardar el pk original si existe (para validación de unicidad)
        self._original_pk = self.instance.pk if self.instance and self.instance.pk else None

    class Meta:
        model = Proveniencia
        fields = ['codigo', 'nombre', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: COMP'}
            ),
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Compra'}
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la proveniencia...'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
    
    def clean_codigo(self) -> str:
        """
        Validar que el código sea único (en mayúsculas).
        
        Al editar, excluye la instancia actual de la validación de unicidad.
        """
        from django.core.exceptions import ValidationError
        
        codigo = self.cleaned_data.get('codigo', '').strip().upper()

        if not codigo:
            raise ValidationError('El código es obligatorio.')

        # Construir queryset para validar unicidad
        # Solo considerar proveniencias no eliminadas
        queryset = Proveniencia.objects.filter(
            codigo=codigo,
            eliminado=False
        )
        
        # Si estamos editando (tenemos un pk original), excluir la instancia actual
        pk_a_excluir = self._original_pk
        
        # Si _original_pk no está disponible, intentar obtenerlo de instance
        if pk_a_excluir is None and self.instance and hasattr(self.instance, 'pk'):
            pk_a_excluir = self.instance.pk
        
        if pk_a_excluir is not None:
            queryset = queryset.exclude(pk=pk_a_excluir)

        if queryset.exists():
            raise ValidationError(
                f'Ya existe una proveniencia con el código "{codigo}".'
            )

        return codigo
    
    def clean_nombre(self) -> str:
        """Validar que el nombre no esté vacío."""
        from django.core.exceptions import ValidationError
        
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        return nombre


# ==================== FORMULARIOS DE MANTENEDORES ====================


class MarcaForm(forms.ModelForm):
    """Formulario para crear y editar marcas de activos y artículos."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Inicializa el formulario.
        
        Guarda el pk original de la instancia para la validación de unicidad.
        """
        super().__init__(*args, **kwargs)
        # Guardar el pk original si existe (para validación de unicidad)
        self._original_pk = self.instance.pk if self.instance and self.instance.pk else None

    class Meta:
        model = Marca
        fields = ['codigo', 'nombre', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: DELL',
                    'maxlength': '20'
                }
            ),
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: Dell Technologies',
                    'maxlength': '100'
                }
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Descripción detallada de la marca (opcional)...'
                }
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
        help_texts = {
            'codigo': 'Código único identificador de la marca',
            'activo': 'Solo las marcas activas estarán disponibles en el sistema'
        }

    def clean_codigo(self) -> str:
        """
        Validar que el código sea único (en mayúsculas).
        
        Al editar, excluye la instancia actual de la validación de unicidad.
        Excluye también registros eliminados (soft delete).
        """
        from django.core.exceptions import ValidationError
        
        codigo = self.cleaned_data.get('codigo', '').strip().upper()

        if not codigo:
            raise ValidationError('El código es obligatorio.')

        # Construir queryset para validar unicidad
        # Solo considerar marcas no eliminadas
        queryset = Marca.objects.filter(
            codigo=codigo,
            eliminado=False
        )
        
        # Si estamos editando (tenemos un pk original), excluir la instancia actual
        pk_a_excluir = self._original_pk
        
        # Si _original_pk no está disponible, intentar obtenerlo de instance
        if pk_a_excluir is None and self.instance and hasattr(self.instance, 'pk'):
            pk_a_excluir = self.instance.pk
        
        if pk_a_excluir is not None:
            queryset = queryset.exclude(pk=pk_a_excluir)

        if queryset.exists():
            raise ValidationError(
                f'Ya existe una marca con el código "{codigo}".'
            )

        return codigo

    def clean_nombre(self) -> str:
        """Limpiar y validar el nombre."""
        from django.core.exceptions import ValidationError
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        return nombre
