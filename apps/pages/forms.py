"""
Formularios para la gestión de perfil de usuario.
"""
from django import forms
from django.contrib.auth.models import User
from apps.accounts.models import UserSecure, Persona


class ProfileForm(forms.ModelForm):
    """Formulario para editar información del perfil del usuario y Persona."""
    
    # Campos de Persona editables
    nombres = forms.CharField(
        label='Nombres',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese los nombres'
        })
    )
    apellido1 = forms.CharField(
        label='Apellido 1',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Primer apellido'
        })
    )
    apellido2 = forms.CharField(
        label='Apellido 2',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Segundo apellido (opcional)'
        })
    )
    sexo = forms.ChoiceField(
        label='Sexo',
        choices=[('', 'Seleccione...'), ('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    fecha_nacimiento = forms.DateField(
        label='Fecha de Nacimiento',
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    talla = forms.CharField(
        label='Talla',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XS, S, M, L, XL, XXL (opcional)'
        }),
        help_text='Talla de ropa (opcional)'
    )
    numero_zapato = forms.CharField(
        label='Número de Zapato',
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de zapato (opcional)'
        }),
        help_text='Para EPP (opcional)'
    )
    foto_perfil = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Foto de Perfil',
        help_text='Subir una nueva foto de perfil (JPG, PNG, etc.)'
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su apellido'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su email'
            }),
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa el formulario con los datos actuales de User y Persona."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                persona = Persona.objects.get(user=self.instance, eliminado=False)
                # Prellenar campos de Persona
                self.fields['nombres'].initial = persona.nombres
                self.fields['apellido1'].initial = persona.apellido1
                self.fields['apellido2'].initial = persona.apellido2 or ''
                self.fields['sexo'].initial = persona.sexo
                self.fields['fecha_nacimiento'].initial = persona.fecha_nacimiento
                self.fields['talla'].initial = persona.talla or ''
                self.fields['numero_zapato'].initial = persona.numero_zapato or ''
                if persona.foto_perfil:
                    self.fields['foto_perfil'].initial = persona.foto_perfil
            except Persona.DoesNotExist:
                # Si no existe Persona, inicializar con datos del User
                self.fields['nombres'].initial = self.instance.first_name or ''
                self.fields['apellido1'].initial = self.instance.last_name or ''


class UserPINForm(forms.Form):
    """Formulario para crear o cambiar el PIN del usuario."""
    
    pin = forms.CharField(
        label='PIN',
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese PIN de 4 dígitos',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        }),
        help_text='El PIN debe tener exactamente 4 dígitos numéricos.'
    )
    
    pin_confirmacion = forms.CharField(
        label='Confirmar PIN',
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme el PIN',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        }),
        help_text='Ingrese nuevamente el PIN para confirmar.'
    )
    
    def clean_pin(self):
        """Validar que el PIN tenga exactamente 4 dígitos numéricos."""
        pin = self.cleaned_data.get('pin', '').strip()
        
        if not pin:
            raise forms.ValidationError('El PIN es obligatorio.')
        
        if not pin.isdigit():
            raise forms.ValidationError('El PIN debe contener solo números.')
        
        if len(pin) != 4:
            raise forms.ValidationError('El PIN debe tener exactamente 4 dígitos.')
        
        return pin
    
    def clean_pin_confirmacion(self):
        """Validar que la confirmación del PIN coincida."""
        pin = self.cleaned_data.get('pin', '').strip()
        pin_confirmacion = self.cleaned_data.get('pin_confirmacion', '').strip()
        
        if not pin_confirmacion:
            raise forms.ValidationError('Debe confirmar el PIN.')
        
        if pin and pin_confirmacion and pin != pin_confirmacion:
            raise forms.ValidationError('Los PINs no coinciden.')
        
        return pin_confirmacion
    
    def clean(self):
        """Validación adicional del formulario."""
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        pin_confirmacion = cleaned_data.get('pin_confirmacion')
        
        if pin and pin_confirmacion and pin != pin_confirmacion:
            raise forms.ValidationError('Los PINs no coinciden.')
        
        return cleaned_data

