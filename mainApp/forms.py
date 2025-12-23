from django import forms
from .models import Cliente, Estado
import re
from itertools import cycle
import phonenumbers 
from phonenumbers.phonenumberutil import NumberParseException 

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'rut', 'telefono', 'correo']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control mb-2', 'placeholder': 'Nombre'})
        self.fields['rut'].widget.attrs.update({'class': 'form-control mb-2', 'placeholder': 'Rut (Ej: 12345678-9)'})
        self.fields['telefono'].widget.attrs.update({
            'class': 'form-control mb-2', 
            'placeholder': 'Ej: 912345678 o +14155552671'
        })
        self.fields['correo'].widget.attrs.update({'class': 'form-control mb-2', 'placeholder': 'Correo'})

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        
        rut = rut.upper().replace(".", "").replace("-", "")
        
        if len(rut) < 3:
             raise forms.ValidationError("RUT no válido.")

        cuerpo = rut[:-1]
        dv = rut[-1]


        if not cuerpo.isdigit() or dv not in "0123456789K":
            raise forms.ValidationError("Formato de RUT no válido. Use solo números y K.")

  
        suma = sum(int(c) * m for c, m in zip(reversed(cuerpo), cycle([2, 3, 4, 5, 6, 7])))
        dv_calculado = f"{11 - (suma % 11)}"

        if dv_calculado == "11":
            dv_calculado = "0"
        if dv_calculado == "10":
            dv_calculado = "K"

        if dv != dv_calculado:
            raise forms.ValidationError("RUT inválido (dígito verificador no coincide).")

        return f"{cuerpo}-{dv}"

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono']
        
        try:

            parsed_number = phonenumbers.parse(telefono, "CL")

            if not phonenumbers.is_valid_number(parsed_number):
                raise forms.ValidationError("Número de teléfono no válido o incompleto.")


            formatted_number = phonenumbers.format_number(
                parsed_number,
                phonenumbers.PhoneNumberFormat.E164
            )
            return formatted_number

        except NumberParseException:
            raise forms.ValidationError("Formato de teléfono no reconocido.")
        
        
class EstadoForm(forms.ModelForm):
    class Meta:
        model = Estado
        fields = ['tipo_estado']