from django.urls import path
from . import views as v
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('home/',v.home,name="home"),
    path('',v.dashboard,name='dashboard'),
    # path('especialista/',v.moduloEspecialista,name='especialista'),
    # URl de paciente
    path('listado_pacientes/',v.ListadoPaciente.as_view(),name='paciente'),
    path('registrar_pacientes/',v.RegistrarPaciente.as_view(),name='registro_p'),
    # path('admnistrador/',v.moduloAdministrador,name='administrador'),
    path('desactivar_paciente/<int:pk>/', v.DesactivarPaciente.as_view(), name='desactivar_paciente'),
    # URL de empleado doctor
    path('registrar_especialista/',v.RegistrarUsuario.as_view(),name='registro_e'),
    path('listado_empleado/',v.ListadoDoctor.as_view(),name='especialista'),
    path('desactivar_usuario/<int:pk>/', v.DesactivarUsuario.as_view(), name='desactivar_usuario'),
    # URL de empleado admin
    path('registrar_admin/',v.RegistrarUsuarioAdmin.as_view(),name='registro_a'),
    path('listado_administradores/',v.ListadoAdmin.as_view(),name='administrador'),
    path('desactivar_admin/<int:pk>/', v.DesactivarUsuarioAdmin.as_view(), name='desactivar_admin'),
    # path('registro_paciente',v.moduloRegistroPaciente,name='registro_p'),
    # Para el historial de diagnostico
    path('historial/',v.moduloHistorialD,name='historial_d'),
    path('historial_personal/',v.moduloHistorialInteracciones,name='historial_m'),
    ################################
    path('diagnostico/etapa1',v.moduloDiagnosticoEtp1,name='diagnostico'),
    path('diagnostico/etapa2/<int:id>',v.moduloDiagnosticoEtp2,name='diagnostico2'),
    path('diagnostico/etapa3/<int:id>',v.moduloDiagnosticoEtp3,name='diagnostico3'),
    path('diagnostico/resultado/<int:paciente_id>/', v.realizar_prediccion, name='diagnosticof'),
    path('diagnostico/resultado/informe/<int:paciente_id>/', v.moduloInformeDiagnostico, name='informeDiagnostico'),
]