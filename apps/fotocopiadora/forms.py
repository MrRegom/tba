from __future__ import annotations

from decimal import Decimal

from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils import timezone

from apps.solicitudes.models import Area, Departamento
from core.utils import validar_rut, format_rut
from .models import (
    FotocopiadoraEquipo,
    PrintCostCenter,
    PrintMembershipRole,
    PrintRequest,
    PrintRequestAttachment,
    PrintRequestItem,
    PrintRoleMembership,
    TrabajoFotocopia,
)


class FotocopiadoraEquipoForm(forms.ModelForm):
    class Meta:
        model = FotocopiadoraEquipo
        fields = ["nombre", "ubicacion", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "ubicacion": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TrabajoFotocopiaForm(forms.ModelForm):
    class Meta:
        model = TrabajoFotocopia
        fields = [
            "fecha_hora",
            "tipo_uso",
            "equipo",
            "solicitante_usuario",
            "solicitante_nombre",
            "rut_solicitante",
            "departamento",
            "area",
            "cantidad_copias",
            "precio_unitario",
            "observaciones",
            "activo",
        ]
        widgets = {
            "fecha_hora": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "tipo_uso": forms.Select(
                attrs={"class": "form-select", "id": "id_tipo_uso"}
            ),
            "equipo": forms.Select(attrs={"class": "form-select"}),
            "solicitante_usuario": forms.Select(attrs={"class": "form-select"}),
            "solicitante_nombre": forms.TextInput(attrs={"class": "form-control"}),
            "rut_solicitante": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "12.345.678-9"}
            ),
            "departamento": forms.Select(attrs={"class": "form-select"}),
            "area": forms.Select(attrs={"class": "form-select"}),
            "cantidad_copias": forms.NumberInput(
                attrs={"class": "form-control", "min": "1"}
            ),
            "precio_unitario": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["equipo"].queryset = FotocopiadoraEquipo.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo")
        self.fields["departamento"].queryset = Departamento.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo")
        self.fields["area"].queryset = Area.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo")
        self.fields["solicitante_usuario"].required = False
        self.fields["rut_solicitante"].required = False
        self.fields["departamento"].required = False
        self.fields["area"].required = False
        self.fields["precio_unitario"].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_uso = cleaned_data.get("tipo_uso")
        cantidad = cleaned_data.get("cantidad_copias") or 0
        precio = cleaned_data.get("precio_unitario")
        rut = cleaned_data.get("rut_solicitante")
        departamento = cleaned_data.get("departamento")
        area = cleaned_data.get("area")

        if cantidad <= 0:
            self.add_error(
                "cantidad_copias", "Debe ingresar una cantidad mayor a cero."
            )

        if tipo_uso == TrabajoFotocopia.TipoUso.INTERNO:
            if not departamento and not area:
                self.add_error(
                    "departamento", "Para uso interno debe indicar departamento o area."
                )
            cleaned_data["rut_solicitante"] = None
            cleaned_data["precio_unitario"] = Decimal("0")

        if tipo_uso in [
            TrabajoFotocopia.TipoUso.PERSONAL,
            TrabajoFotocopia.TipoUso.EXTERNO,
        ]:
            if not rut:
                self.add_error(
                    "rut_solicitante", "RUT obligatorio para uso personal o externo."
                )
            elif not validar_rut(rut):
                self.add_error("rut_solicitante", "RUT invalido.")
            else:
                cleaned_data["rut_solicitante"] = format_rut(rut)

            if precio is None:
                self.add_error(
                    "precio_unitario",
                    "Precio unitario obligatorio para uso personal o externo.",
                )

        return cleaned_data


class FiltroTrabajoFotocopiaForm(forms.Form):
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    equipo = forms.ModelChoiceField(
        required=False,
        queryset=FotocopiadoraEquipo.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    tipo_uso = forms.ChoiceField(
        required=False,
        choices=[("", "Todos")] + list(TrabajoFotocopia.TipoUso.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    solicitante = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nombre solicitante"}
        ),
    )
    rut = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "RUT"}),
    )


class PrintRequestForm(forms.ModelForm):
    class Meta:
        model = PrintRequest
        fields = [
            "title",
            "description",
            "use_type",
            "request_type",
            "priority",
            "required_at",
            "departamento",
            "area",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Prueba de Historia 7B",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Detalle breve del material a preparar",
                }
            ),
            "use_type": forms.Select(attrs={"class": "form-select"}),
            "request_type": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "required_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "departamento": forms.Select(attrs={"class": "form-select", "id": "id_departamento"}),
            "area": forms.Select(attrs={"class": "form-select", "id": "id_area"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["departamento"].queryset = Departamento.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo")
        self.fields["area"].queryset = Area.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo")
        self.fields["departamento"].required = False
        self.fields["area"].required = False

    def clean_required_at(self):
        value = self.cleaned_data["required_at"]
        if value <= timezone.now():
            raise forms.ValidationError("La fecha requerida debe ser futura.")
        return value


class PrintRequestItemForm(forms.ModelForm):
    class Meta:
        model = PrintRequestItem
        fields = [
            "document_title",
            "page_size",
            "print_side",
            "color_mode",
            "copy_count_requested",
            "stapled",
            "collated",
            "ring_bound",
            "notes",
        ]
        widgets = {
            "document_title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Documento o guia"}
            ),
            "page_size": forms.Select(attrs={"class": "form-select"}),
            "print_side": forms.Select(attrs={"class": "form-select"}),
            "color_mode": forms.Select(attrs={"class": "form-select"}),
            "copy_count_requested": forms.NumberInput(
                attrs={"class": "form-control", "min": "1"}
            ),
            "stapled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "collated": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ring_bound": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class BasePrintRequestItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if not active_forms:
            raise forms.ValidationError(
                "Debe ingresar al menos un detalle de impresión."
            )


PrintRequestItemFormSet = inlineformset_factory(
    PrintRequest,
    PrintRequestItem,
    form=PrintRequestItemForm,
    formset=BasePrintRequestItemFormSet,
    extra=1,
    can_delete=True,
)


class PrintRequestApprovalForm(forms.Form):
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Observaciones de aprobacion o rechazo",
            }
        ),
        label="Observacion",
    )

    def __init__(self, *args, request_obj: PrintRequest, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_obj = request_obj
        for item in request_obj.items.all():
            self.fields[f"item_{item.pk}_approved"] = forms.IntegerField(
                required=False,
                min_value=1,
                initial=item.copy_count_approved or item.copy_count_requested,
                label=f"Cantidad aprobada para {item.document_title}",
                widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            )

    def clean(self):
        cleaned = super().clean()
        for item in self.request_obj.items.all():
            field_name = f"item_{item.pk}_approved"
            approved_qty = cleaned.get(field_name)
            if approved_qty is None:
                continue
            if approved_qty > item.copy_count_requested:
                self.add_error(
                    field_name, "La cantidad aprobada no puede superar la solicitada."
                )
        return cleaned

    def apply(self):
        partial = False
        for item in self.request_obj.items.all():
            field_name = f"item_{item.pk}_approved"
            approved_qty = self.cleaned_data.get(field_name)
            if approved_qty is None:
                approved_qty = item.copy_count_requested
            item.copy_count_approved = approved_qty
            if approved_qty < item.copy_count_requested:
                partial = True
            item.save(update_fields=["copy_count_approved", "fecha_actualizacion"])
        self.request_obj.is_partial_approval = partial
        self.request_obj.save(
            update_fields=["is_partial_approval", "fecha_actualizacion"]
        )
        return partial


class PrintRequestTransitionCommentForm(forms.Form):
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Comentario opcional",
            }
        ),
        label="Comentario",
    )


class PrintRequestAttachmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = False

    class Meta:
        model = PrintRequestAttachment
        fields = ["file"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            return file
        allowed_extensions = {
            ".pdf",
            ".docx",
            ".xlsx",
            ".pptx",
            ".jpg",
            ".jpeg",
            ".png",
        }
        extension = ""
        if hasattr(file, "name") and "." in file.name:
            extension = file.name[file.name.rfind(".") :].lower()
        if extension not in allowed_extensions:
            raise forms.ValidationError("Tipo de archivo no permitido.")
        if hasattr(file, "size") and file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                "El archivo excede el tamano maximo permitido de 10 MB."
            )
        return file


class PrintRoleMembershipForm(forms.ModelForm):
    class Meta:
        model = PrintRoleMembership
        fields = [
            "user",
            "role",
            "departamento",
            "area",
            "equipo",
            "cost_center",
            "is_primary",
            "valid_from",
            "valid_to",
            "activo",
        ]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "departamento": forms.Select(attrs={"class": "form-select"}),
            "area": forms.Select(attrs={"class": "form-select"}),
            "equipo": forms.Select(attrs={"class": "form-select"}),
            "cost_center": forms.Select(attrs={"class": "form-select"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "valid_from": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "valid_to": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["departamento"].queryset = Departamento.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo")
        self.fields["area"].queryset = Area.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo")
        self.fields["equipo"].queryset = FotocopiadoraEquipo.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo")
        self.fields["cost_center"].queryset = PrintCostCenter.objects.filter(
            activo=True, eliminado=False
        ).order_by("codigo")
        self.fields["departamento"].required = False
        self.fields["area"].required = False
        self.fields["equipo"].required = False
        self.fields["cost_center"].required = False
        self.fields["valid_from"].required = False
        self.fields["valid_to"].required = False

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")

        if role == PrintMembershipRole.APPROVER and not (
            cleaned.get("departamento") or cleaned.get("area")
        ):
            self.add_error(
                "departamento",
                "La jefatura debe quedar asociada a un departamento o area.",
            )

        if role in {
            PrintMembershipRole.ADMIN,
            PrintMembershipRole.AUDITOR,
            PrintMembershipRole.SUPERADMIN,
        }:
            for field_name in ("departamento", "area", "equipo", "cost_center"):
                if cleaned.get(field_name):
                    self.add_error(
                        field_name,
                        "Este perfil principal debe permanecer global dentro del modulo.",
                    )

        return cleaned
