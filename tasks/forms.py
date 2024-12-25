from django import forms
from .models import Paciente, Usuario,Estado

class ValidarEmpleado(forms.Form):
    username = forms.CharField(max_length=200)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'inp_pass'}), max_length=200)
    
    def __init__(self, *args, **kwargs):
        super(ValidarEmpleado, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'inp_user'})
        self.fields['password'].widget.attrs.update({'class': 'inp_pass'})
        
class ValidarPrediccion(forms.Form):
    pelvic_incidence = forms.CharField(max_length=200)
    pelvic_tilt = forms.CharField(max_length=200)
    lumbar_lordosis_angle = forms.CharField(max_length=200)
    sacral_slope = forms.CharField(max_length=200)
    pelvic_radius = forms.CharField(max_length=200)
    degree_spondylolisthesis = forms.CharField(max_length=200)

    def __init__(self, *args, **kwargs):
        super(ValidarPrediccion, self).__init__(*args, **kwargs)
        # Actualiza las clases CSS de los campos correctamente
        self.fields['pelvic_incidence'].widget.attrs.update({'class': 'contenido'})
        self.fields['pelvic_tilt'].widget.attrs.update({'class': 'contenido'})
        self.fields['lumbar_lordosis_angle'].widget.attrs.update({'class': 'contenido'})
        self.fields['sacral_slope'].widget.attrs.update({'class': 'contenido'})
        self.fields['pelvic_radius'].widget.attrs.update({'class': 'contenido'})
        self.fields['degree_spondylolisthesis'].widget.attrs.update({'class': 'contenido'})
        
        
class CrearPaciente(forms.ModelForm):
        class Meta:
            model = Paciente
            fields = ['primer_nombre', 'segundo_nombre', 'apellido_paterno', 'apellido_materno', 'correo', 'telefono', 'dni', 'foto']
        
        # Campos personalizados
        primer_nombre = forms.CharField(
            max_length=200,
            widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Primer Nombre"})
        )
        segundo_nombre = forms.CharField(
            max_length=200,
            required=False,
            widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Segundo Nombre"})
        )
        apellido_paterno = forms.CharField(
            max_length=200,
            widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Apellido Paterno"})
        )
        apellido_materno = forms.CharField(
            max_length=200,
            widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Apellido Materno"})
        )
        correo = forms.EmailField(
            max_length=200,
            widget=forms.EmailInput(attrs={"class": "custom-input", "placeholder": "Correo Electrónico"})
        )
        telefono = forms.CharField(
            max_length=9,
            min_length=9,
            widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Teléfono"})
        )
        dni = forms.CharField(
            max_length=8,
            min_length=8,
            widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "DNI"})
        )
        # fecha_creacion = forms.DateField(
        #     widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
        # )
        foto = forms.ImageField(
            widget=forms.FileInput(attrs={"class": "custom-file-input", "accept": "image/*"}),
            required=False
        )
        

class CrearUsuario(forms.ModelForm):
    # Campos de la clase Meta
    class Meta:
        model = Usuario
        fields = ['primer_nombre', 'segundo_nombre', 'apellido_paterno', 'apellido_materno', 
                  'codigo_empl', 'estado', 'username', 'email', 'telefono', 'dni', 'foto','usuario_administrador']
    
    # Campos personalizados
    primer_nombre = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Primer Nombre"})
    )
    segundo_nombre = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Segundo Nombre"})
    )
    apellido_paterno = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Apellido Paterno"})
    )
    apellido_materno = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Apellido Materno"})
    )
    codigo_empl = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Código de Empleado"})
    )
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.all(),
        widget=forms.Select(attrs={"class": "custom-input"})
    )
    username = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Nombre de Usuario"})
    )
    email = forms.EmailField(
        max_length=200,
        widget=forms.EmailInput(attrs={"class": "custom-input", "placeholder": "Correo Electrónico"})
    )
    telefono = forms.CharField(
        max_length=9,
        min_length=9,
        widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "Teléfono"})
    )
    dni = forms.CharField(
        max_length=8,
        min_length=8,
        widget=forms.TextInput(attrs={"class": "custom-input", "placeholder": "DNI"})
    )
    foto = forms.ImageField(
        widget=forms.FileInput(attrs={"class": "custom-file-input", "accept": "image/*"}),
        required=False
    )
    
    usuario_administrador = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "custom-checkbox"})
    )
    
    # Campos de contraseña
    contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "custom-input", "placeholder": "Contraseña"})
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "custom-input", "placeholder": "Confirmar Contraseña"})
    )
    
   
    
    def clean(self):
        cleaned_data = super().clean()
        contrasena = cleaned_data.get("contrasena")
        confirmar_contrasena = cleaned_data.get("confirmar_contrasena")
        
        if contrasena and confirmar_contrasena:
            if contrasena != confirmar_contrasena:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        
        # Se debe devolver el cleaned_data completo
        return cleaned_data

    
    def save(self,commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['contrasena'])
        if commit:
            user.save()
        return user