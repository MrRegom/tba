from __future__ import annotations

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from apps.solicitudes.models import Area, Departamento
from core.utils import validar_rut, format_rut
from .models import FotocopiadoraEquipo, TrabajoFotocopia


class FotocopiadoraEquipoForm(forms.ModelForm):
    class Meta:
        model = FotocopiadoraEquipo
        fields = ['codigo', 'nombre', 'ubicacion', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: FC-01'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TrabajoFotocopiaForm(forms.ModelForm):
    class Meta:
        model = TrabajoFotocopia
        fields = [
            'fecha_hora',
            'tipo_uso',
            'equipo',
            'solicitante_usuario',
            'solicitante_nombre',
            'rut_solicitante',
            'departamento',
            'area',
            'cantidad_copias',
            'precio_unitario',
            'observaciones',
            'activo',
        ]
        widgets = {
            'fecha_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tipo_uso': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_uso'}),
            'equipo': forms.Select(attrs={'class': 'form-select'}),
            'solicitante_usuario': forms.Select(attrs={'class': 'form-select'}),
            'solicitante_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rut_solicitante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
            'area': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_copias': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['equipo'].queryset = FotocopiadoraEquipo.objects.filter(activo=True, eliminado=False).order_by('codigo')
        self.fields['departamento'].queryset = Departamento.objects.filter(activo=True, eliminado=False).order_by('codigo')
        self.fields['area'].queryset = Area.objects.filter(activo=True, eliminado=False).order_by('codigo')
        self.fields['solicitante_usuario'].required = False
        self.fields['rut_solicitante'].required = False
        self.fields['departamento'].required = False
        self.fields['area'].required = False
        self.fields['precio_unitario'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_uso = cleaned_data.get('tipo_uso')
        cantidad = cleaned_data.get('cantidad_copias') or 0
        precio = cleaned_data.get('precio_unitario')
        rut = cleaned_data.get('rut_solicitante')
        departamento = cleaned_data.get('departamento')
        area = cleaned_data.get('area')

        if cantidad <= 0:
            self.add_error('cantidad_copias', 'Debe ingresar una cantidad mayor a cero.')

        if tipo_uso == TrabajoFotocopia.TipoUso.INTERNO:
            if not departamento and not area:
                self.add_error('departamento', 'Para uso interno debe indicar departamento o area.')
            cleaned_data['rut_solicitante'] = None
            cleaned_data['precio_unitario'] = Decimal('0')

        if tipo_uso in [TrabajoFotocopia.TipoUso.PERSONAL, TrabajoFotocopia.TipoUso.EXTERNO]:
            if not rut:
                self.add_error('rut_solicitante', 'RUT obligatorio para uso personal o externo.')
            elif not validar_rut(rut):
                self.add_error('rut_solicitante', 'RUT invalido.')
            else:
                cleaned_data['rut_solicitante'] = format_rut(rut)

            if precio is None:
                self.add_error('precio_unitario', 'Precio unitario obligatorio para uso personal o externo.')

        return cleaned_data


class FiltroTrabajoFotocopiaForm(forms.Form):
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    equipo = forms.ModelChoiceField(
        required=False,
        queryset=FotocopiadoraEquipo.objects.filter(activo=True, eliminado=False).order_by('codigo'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    tipo_uso = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(TrabajoFotocopia.TipoUso.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    solicitante = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre solicitante'}),
    )
    rut = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT'}),
    )
