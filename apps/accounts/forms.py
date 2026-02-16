from crispy_forms.helper import FormHelper
from allauth.account.forms import LoginForm, SignupForm, ChangePasswordForm, ResetPasswordForm, ResetPasswordKeyForm, SetPasswordForm
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import AuthEstado


class UserLoginForm(LoginForm):
    """Formulario de login personalizado con estilos Bootstrap."""
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['login'].widget = forms.TextInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su usuario',
            'id': 'username'
        })
        self.fields['password'].widget = forms.PasswordInput(attrs={
            'class': 'form-control mb-2 position-relative',
            'placeholder': 'Ingrese su contraseña',
            'id': 'password'
        })
        self.fields['remember'].widget = forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })


class UserRegistrationForm(SignupForm):
    """Formulario de registro personalizado con estilos Bootstrap."""
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['email'].widget = forms.EmailInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su email',
            'id': 'email'
        })
        self.fields['email'].label = "Email"
        self.fields['username'].widget = forms.TextInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su usuario',
            'id': 'username1'
        })
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su contraseña',
            'id': 'password1'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su contraseña nuevamente',
            'id': 'password2'
        })
        self.fields['password2'].label = "Confirmar contraseña"


class PasswordChangeForm(ChangePasswordForm):
    """Formulario de cambio de contraseña personalizado."""
    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.fields['oldpassword'].widget = forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su contraseña actual',
            'id': 'password3'
        })
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su nueva contraseña',
            'id': 'password4'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su nueva contraseña nuevamente',
            'id': 'password5'
        })
        self.fields['oldpassword'].label = "Contraseña actual"
        self.fields['password2'].label = "Confirmar contraseña"


class PasswordResetForm(ResetPasswordForm):
    """Formulario de reseteo de contraseña personalizado."""
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.fields['email'].widget = forms.EmailInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su email',
            'id': 'email1'
        })
        self.fields['email'].label = "Email"


class PasswordResetKeyForm(ResetPasswordKeyForm):
    """Formulario de reseteo de contraseña con clave personalizado."""
    def __init__(self, *args, **kwargs):
        super(PasswordResetKeyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su nueva contraseña',
            'id': 'password6'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su nueva contraseña nuevamente',
            'id': 'password7'
        })
        self.fields['password2'].label = "Confirmar contraseña"


class PasswordSetForm(SetPasswordForm):
    """Formulario de establecimiento de contraseña personalizado."""
    def __init__(self, *args, **kwargs):
        super(PasswordSetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Ingrese su nueva contraseña',
            'id': 'password8'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nueva contraseña nuevamente',
            'id': 'password9'
        })
        self.fields['password2'].label = "Confirmar contraseña"


# ========== FORMULARIOS DE GESTIÓN DE USUARIOS ==========

class UserCreateForm(forms.ModelForm):
    """Formulario para crear nuevos usuarios del sistema con datos de Persona."""
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    password2 = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme la contraseña'
        })
    )
    pin = forms.CharField(
        label='PIN (Opcional)',
        max_length=4,
        min_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '4 dígitos (opcional)',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        }),
        help_text='PIN de 4 dígitos para confirmar entregas (opcional, puede configurarse después)'
    )
    pin_confirmacion = forms.CharField(
        label='Confirmar PIN',
        max_length=4,
        min_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme el PIN',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        })
    )
    
    # Campos de Persona
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
        label='Foto de Perfil',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Foto de perfil del usuario (opcional)'
    )
    activo_persona = forms.BooleanField(
        label='Activo',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Estado activo/inactivo de la persona'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': 'Usuario Activo',
            'is_staff': 'Es Staff',
            'is_superuser': 'Es Superusuario',
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def clean_pin(self):
        """Validar que el PIN tenga exactamente 4 dígitos numéricos."""
        pin = self.cleaned_data.get('pin', '').strip()
        
        if pin:
            if not pin.isdigit():
                raise forms.ValidationError('El PIN debe contener solo números.')
            if len(pin) != 4:
                raise forms.ValidationError('El PIN debe tener exactamente 4 dígitos.')
        
        return pin

    def clean_pin_confirmacion(self):
        """Validar que la confirmación del PIN coincida."""
        pin = self.cleaned_data.get('pin', '').strip()
        pin_confirmacion = self.cleaned_data.get('pin_confirmacion', '').strip()
        
        if pin and pin_confirmacion and pin != pin_confirmacion:
            raise forms.ValidationError('Los PINs no coinciden.')
        
        if pin_confirmacion and not pin:
            raise forms.ValidationError('Debe ingresar el PIN primero.')
        
        return pin_confirmacion

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Formulario para actualizar usuarios del sistema."""
    pin = forms.CharField(
        label='PIN (Opcional)',
        max_length=4,
        min_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '4 dígitos (opcional)',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        }),
        help_text='Dejar vacío para mantener el PIN actual. Ingrese nuevo PIN para cambiarlo.'
    )
    pin_confirmacion = forms.CharField(
        label='Confirmar PIN',
        max_length=4,
        min_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme el PIN',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': 'Usuario Activo',
            'is_staff': 'Es Staff',
            'is_superuser': 'Es Superusuario',
        }

    def clean_pin(self):
        """Validar que el PIN tenga exactamente 4 dígitos numéricos."""
        pin = self.cleaned_data.get('pin', '').strip()
        
        if pin:
            if not pin.isdigit():
                raise forms.ValidationError('El PIN debe contener solo números.')
            if len(pin) != 4:
                raise forms.ValidationError('El PIN debe tener exactamente 4 dígitos.')
        
        return pin

    def clean_pin_confirmacion(self):
        """Validar que la confirmación del PIN coincida."""
        pin = self.cleaned_data.get('pin', '').strip()
        pin_confirmacion = self.cleaned_data.get('pin_confirmacion', '').strip()
        
        if pin and pin_confirmacion and pin != pin_confirmacion:
            raise forms.ValidationError('Los PINs no coinciden.')
        
        if pin_confirmacion and not pin:
            raise forms.ValidationError('Debe ingresar el PIN primero.')
        
        return pin_confirmacion


class UserPasswordChangeForm(forms.Form):
    """Formulario para cambiar contraseña de usuario (por admin)."""
    password1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        })
    )
    password2 = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme la contraseña'
        })
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2


# ========== FORMULARIOS DE GESTIÓN DE GRUPOS/ROLES ==========

from django.contrib.auth.models import Group, Permission

class GroupForm(forms.ModelForm):
    """Formulario para crear/editar grupos (roles)."""
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del rol'
            }),
        }
        labels = {
            'name': 'Nombre del Rol',
        }


class GroupPermissionsForm(forms.ModelForm):
    """Formulario para asignar permisos a un grupo."""
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Permisos'
    )

    class Meta:
        model = Group
        fields = ['permissions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organizar permisos por app/modelo
        self.fields['permissions'].queryset = Permission.objects.select_related(
            'content_type'
        ).order_by('content_type__app_label', 'content_type__model', 'codename')


class UserGroupsForm(forms.ModelForm):
    """Formulario para asignar grupos a un usuario."""
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Roles/Grupos'
    )

    class Meta:
        model = User
        fields = ['groups']


class UserPermissionsForm(forms.ModelForm):
    """Formulario para asignar permisos específicos a un usuario."""
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Permisos del Usuario'
    )

    class Meta:
        model = User
        fields = ['user_permissions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organizar permisos por app/modelo
        self.fields['user_permissions'].queryset = Permission.objects.select_related(
            'content_type'
        ).order_by('content_type__app_label', 'content_type__model', 'codename')


# ========== FORMULARIOS DE FILTROS ==========

class UserFilterForm(forms.Form):
    """Formulario para filtrar usuarios."""
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, email, usuario...'
        }),
        label='Buscar'
    )
    is_active = forms.TypedChoiceField(
        required=False,
        coerce=lambda x: x == 'True',
        choices=[
            ('', 'Todos los estados'),
            ('True', 'Activos'),
            ('False', 'Inactivos')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
    is_staff = forms.TypedChoiceField(
        required=False,
        coerce=lambda x: x == 'True',
        choices=[
            ('', 'Todos'),
            ('True', 'Staff'),
            ('False', 'No Staff')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Es Staff'
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        empty_label='Todos los roles',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Rol/Grupo'
    )


# ========== FORMULARIOS DE PERMISOS ==========

class PermissionForm(forms.ModelForm):
    """Formulario para crear/editar permisos personalizados."""

    class Meta:
        model = Permission
        fields = ['name', 'content_type', 'codename']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Puede aprobar solicitudes'
            }),
            'content_type': forms.Select(attrs={'class': 'form-select'}),
            'codename': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: aprobar_solicitud'
            }),
        }
        labels = {
            'name': 'Nombre del Permiso',
            'content_type': 'Modelo (Content Type)',
            'codename': 'Código del Permiso',
        }
        help_texts = {
            'name': 'Nombre descriptivo del permiso (ej: "Puede aprobar solicitudes")',
            'content_type': 'Seleccione el modelo al que aplica este permiso',
            'codename': 'Código único del permiso (sin espacios, usar guiones bajos)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar content types por app y modelo
        self.fields['content_type'].queryset = ContentType.objects.all().order_by('app_label', 'model')

    def clean_codename(self):
        """Validar que el codename no tenga espacios y sea lowercase."""
        codename = self.cleaned_data.get('codename', '')
        # Convertir a lowercase y reemplazar espacios por guiones bajos
        codename = codename.lower().replace(' ', '_')
        # Validar que solo contenga letras, números y guiones bajos
        if not codename.replace('_', '').isalnum():
            raise forms.ValidationError('El código del permiso solo puede contener letras, números y guiones bajos.')
        return codename


# ========== FORMULARIOS DE ORGANIZACIÓN ==========

# Imports de modelos de Organización
from apps.activos.models import Ubicacion, Taller
from apps.solicitudes.models import Area, Departamento


class UbicacionForm(forms.ModelForm):
    """Formulario para crear y editar ubicaciones físicas."""
    
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


class TallerForm(forms.ModelForm):
    """Formulario para crear y editar talleres de servicio."""
    
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].queryset = User.objects.filter(
            is_active=True
        ).order_by('username')
        self.fields['responsable'].required = False


class AreaForm(forms.ModelForm):
    """Formulario para crear y editar áreas."""
    
    class Meta:
        model = Area
        fields = ['codigo', 'nombre', 'descripcion', 'departamento', 'responsable', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: AREA001'}
            ),
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Área de Tecnología'}
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del área...'}
            ),
            'departamento': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'responsable': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.solicitudes.models import Departamento
        self.fields['departamento'].queryset = Departamento.objects.filter(
            eliminado=False
        ).order_by('codigo')
        self.fields['responsable'].queryset = User.objects.filter(
            is_active=True
        ).order_by('username')
        self.fields['responsable'].required = False


class DepartamentoForm(forms.ModelForm):
    """Formulario para crear y editar departamentos."""
    
    class Meta:
        model = Departamento
        fields = ['codigo', 'nombre', 'descripcion', 'responsable', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: DEP001'}
            ),
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Departamento de Tecnología'}
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del departamento...'}
            ),
            'responsable': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].queryset = User.objects.filter(
            is_active=True
        ).order_by('username')
        self.fields['responsable'].required = False


# ========== FORMULARIOS DE CARGOS ==========

class CargoForm(forms.ModelForm):
    """Formulario para crear y editar cargos."""
    
    class Meta:
        from .models import Cargo
        model = Cargo
        fields = ['codigo', 'nombre', 'activo']
        widgets = {
            'codigo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: PROF-MAT'}
            ),
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Profesor de Matemáticas'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
        labels = {
            'codigo': 'Código del Cargo',
            'nombre': 'Nombre del Cargo',
            'activo': 'Activo',
        }
        help_texts = {
            'codigo': 'Código único del cargo (ej: PROF-MAT, BOD-001)',
            'nombre': 'Nombre descriptivo del cargo',
        }

    def clean_codigo(self):
        """Validar que el código sea único y en mayúsculas."""
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        
        # Verificar unicidad (excluyendo el registro actual si es edición)
        from .models import Cargo
        queryset = Cargo.objects.filter(codigo=codigo)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('Ya existe un cargo con este código.')
        
        return codigo


# ========== FORMULARIOS PARA GESTIÓN DE PERSONA, PIN Y CARGOS ==========

class PersonaForm(forms.ModelForm):
    """Formulario para crear y editar datos de Persona/Funcionario."""
    
    class Meta:
        from .models import Persona
        model = Persona
        fields = [
            'documento_identidad', 'nombres', 'apellido1', 'apellido2',
            'sexo', 'fecha_nacimiento', 'talla', 'numero_zapato'
        ]
        widgets = {
            'documento_identidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12345678-9'
            }),
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres'
            }),
            'apellido1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primer Apellido'
            }),
            'apellido2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Segundo Apellido (opcional)'
            }),
            'sexo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'talla': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: M, L, XL'
            }),
            'numero_zapato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 42, 43'
            }),
        }
        labels = {
            'documento_identidad': 'Documento de Identidad',
            'nombres': 'Nombres',
            'apellido1': 'Primer Apellido',
            'apellido2': 'Segundo Apellido',
            'sexo': 'Sexo',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'talla': 'Talla',
            'numero_zapato': 'Número de Zapato',
        }

    def clean_documento_identidad(self):
        """Validar que el documento de identidad sea único."""
        documento = self.cleaned_data.get('documento_identidad', '').strip()
        if not documento:
            raise forms.ValidationError('El documento de identidad es obligatorio.')
        
        from .models import Persona
        queryset = Persona.objects.filter(documento_identidad=documento)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('Ya existe una persona con este documento de identidad.')
        
        return documento


class PINForm(forms.Form):
    """Formulario para crear o cambiar PIN de usuario."""
    
    pin = forms.CharField(
        label='PIN',
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese 4 dígitos',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        }),
        help_text='PIN de 4 dígitos numéricos'
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
        })
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
        pin = self.cleaned_data.get('pin')
        pin_confirmacion = self.cleaned_data.get('pin_confirmacion', '').strip()
        
        if pin and pin_confirmacion and pin != pin_confirmacion:
            raise forms.ValidationError('Los PINs no coinciden.')
        
        return pin_confirmacion


class UserCargoForm(forms.ModelForm):
    """Formulario para asignar cargos a usuarios."""
    
    class Meta:
        from .models import UserCargo
        model = UserCargo
        fields = ['cargo', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'cargo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'cargo': 'Cargo',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Cargo
        self.fields['cargo'].queryset = Cargo.objects.filter(activo=True, eliminado=False).order_by('nombre')
        self.fields['fecha_fin'].required = False

    def clean(self):
        """Validar que fecha_fin sea posterior a fecha_inicio."""
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise forms.ValidationError({
                'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        
        return cleaned_data

