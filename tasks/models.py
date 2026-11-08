from django.db import models
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from decimal import Decimal

# Create your models here.
class Acciones(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name 

class Padecimiento(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name 
    
class Estado(models.Model):
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name 


# class UsuarioManager(BaseUserManager):
#     def create_user(self,email,username,primer_nombre,segundo_nombre,apellido_paterno,apellido_materno,password=None):
#         if not email:
#             raise ValueError('El Usuario debe de tener un correo electrónico!')
        
#         usuario = self.model(
#             username=username,
#             email = self.normalize_email(email),
#             primer_nombre=primer_nombre,
#             segundo_nombre=segundo_nombre,            
#             apellido_paterno = apellido_paterno,
#             apellido_materno=apellido_materno
#             )
        
#         usuario.set_password(password)
#         usuario.save()
#         return usuario
    
#     def create_superuser(self,email,username,primer_nombre,segundo_nombre,apellido_paterno,apellido_materno,password):
#         usuario = self.create_user(
#             email,
#             username=username,            
#             primer_nombre=primer_nombre,
#             segundo_nombre=segundo_nombre,            
#             apellido_paterno = apellido_paterno,
#             apellido_materno=apellido_materno
#         )
        
#         usuario.usuario_administrador=True
#         usuario.save()
#         return usuario
        
        
    
# class Usuario(AbstractBaseUser):
#     primer_nombre = models.CharField(max_length=200)
#     segundo_nombre = models.CharField(max_length=200, blank=True)
#     apellido_paterno = models.CharField(max_length=200)
#     apellido_materno = models.CharField(max_length=200)
#     codigo_empl = models.CharField(max_length=10)
#     usuario_administrador = models.BooleanField(default=False)
#     estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
#     username = models.CharField(max_length=20, unique=True, null=False)
#     email = models.CharField(max_length=200)
#     telefono = models.CharField(max_length=9, validators=[MinLengthValidator(9)])
#     dni = models.CharField(max_length=8, validators=[MinLengthValidator(8)])
#     foto = models.ImageField('Imagen de perfil',upload_to='perfil/', null=True, blank=True,max_length=255)
#     fecha_creacion = models.DateTimeField(auto_now_add=True)
#     objects = UsuarioManager()
    
#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = ['email', 'primer_nombre','segundo_nombre','apellido_paterno','apellido_materno']
        
#     def __str__(self):
#         return f'Usuario {self.username},{self.apellido_paterno},{self.apellido_materno}'
    
#     def has_perm(self,perm,obj = None):
#         return True
    
#     def has_module_perms(self,app_label):
#         return True
    
#     @property
#     def is_staff(self):
#         return self.usuario_administrador


class UsuarioManager(BaseUserManager):
    def create_user(self, email, username, primer_nombre, segundo_nombre, apellido_paterno, apellido_materno, password=None):
        if not email:
            raise ValueError('El Usuario debe de tener un correo electrónico!')
        
        usuario = self.model(
            username=username,
            email=self.normalize_email(email),
            primer_nombre=primer_nombre,
            segundo_nombre=segundo_nombre,            
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno
        )
        
        usuario.set_password(password)
        usuario.save()
        return usuario
    
    def create_superuser(self, email, username, primer_nombre, segundo_nombre, apellido_paterno, apellido_materno, password):
        usuario = self.create_user(
            email,
            username=username,            
            primer_nombre=primer_nombre,
            segundo_nombre=segundo_nombre,            
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            password=password
        )
        
        usuario.usuario_administrador = True  # Corregido
        usuario.save()
        return usuario


class Usuario(AbstractBaseUser):
    primer_nombre = models.CharField(max_length=200)
    segundo_nombre = models.CharField(max_length=200, blank=True)
    apellido_paterno = models.CharField(max_length=200)
    apellido_materno = models.CharField(max_length=200)
    codigo_empl = models.CharField(max_length=10)
    usuario_administrador = models.BooleanField(default=False)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE,null=True)
    username = models.CharField(max_length=20, unique=True, null=False)
    email = models.EmailField(max_length=200,unique=True)  # Cambiado a EmailField
    telefono = models.CharField(max_length=9, validators=[MinLengthValidator(9)], null=True, blank=True)
    dni = models.CharField(max_length=8, validators=[MinLengthValidator(8)], null=True, blank=True)
    foto = models.ImageField('Imagen de perfil', upload_to='usuarios1/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    es_demo = models.BooleanField(default=False, db_index=True)
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'primer_nombre', 'segundo_nombre', 'apellido_paterno', 'apellido_materno']
        
    def __str__(self):
        return f'Usuario {self.username}, {self.apellido_paterno}, {self.apellido_materno}'
    
    def has_perm(self, perm, obj = None):
        # Personaliza la lógica de permisos aquí
        return True
    
    def has_module_perms(self, app_label):
        # Personaliza la lógica de permisos aquí
        return True

    @property
    def is_active(self):
        return self.estado_id is not None and self.estado.name == "Activo"

    @property
    def is_staff(self):
        return self.usuario_administrador



class Paciente (models.Model):
    primer_nombre = models.CharField(max_length=200)
    segundo_nombre = models.CharField(max_length=200, blank=True)
    apellido_paterno = models.CharField(max_length=200)
    apellido_materno = models.CharField(max_length=200)
    correo = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=9, validators=[MinLengthValidator(9)], blank=True)
    dni = models.CharField(max_length=8, validators=[MinLengthValidator(8)],unique=True)
    foto = models.ImageField('Imagen de perfil', upload_to='perfil/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    es_demo = models.BooleanField(default=False, db_index=True)
    
    def __str__(self):
        return self.dni 

class Historial_paciente (models.Model):
    empleado = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    padecimiento = models.ForeignKey(Padecimiento, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    
    precision_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    es_demo = models.BooleanField(default=False, db_index=True)
    
    def __str__(self):
        return self.padecimiento.name 
    
class Datos (models.Model):
    historial_paciente = models.ForeignKey(Historial_paciente, on_delete=models.CASCADE)
    pelvic_incidence = models.FloatField()
    pelvic_tilt = models.FloatField()
    lumbar_lordosis_angle = models.FloatField()
    sacral_slope = models.FloatField()
    pelvic_radius = models.FloatField()
    degree_spondylolisthesis = models.FloatField()
    
    # def __str__(self):
    #     return self.historial_paciente 
    def __str__(self):
        return f"Historial de {self.historial_paciente.paciente}"
    
class Crud_empleado(models.Model):
    editor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='acciones_editadas')
    afectado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='acciones_afectadas')
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=50)
    es_demo = models.BooleanField(default=False, db_index=True)
    
    def __str__(self):
        return self.editor.codigo_empl

    
class Crud_paciente (models.Model):
    editor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    afectado = models.ForeignKey(Paciente,on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=50)
    es_demo = models.BooleanField(default=False, db_index=True)
    
    def __str__(self):
        return self.fecha
    