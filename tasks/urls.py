from django.urls import path
from django.views.generic import RedirectView
from . import views as v

urlpatterns = [
    path('home/', RedirectView.as_view(pattern_name='dashboard'), name="home"),
    path('',v.dashboard,name='dashboard'),
    path('healthz/', v.healthz, name='healthz'),
    path('demo/login/<str:role>/', v.demo_login, name='demo_login'),
    # URL de paciente
    path('listado_pacientes/',v.ListadoPaciente.as_view(),name='paciente'),
    path('registrar_pacientes/',v.RegistrarPaciente.as_view(),name='registro_p'),
    path('pacientes/<int:pk>/', v.DetallePaciente.as_view(), name='paciente_detalle'),
    path('pacientes/<int:pk>/editar/', v.EditarPaciente.as_view(), name='paciente_editar'),
    path('desactivar_paciente/<int:pk>/', v.DesactivarPaciente.as_view(), name='desactivar_paciente'),
    # URL de empleado doctor
    path('registrar_especialista/',v.RegistrarUsuario.as_view(),name='registro_e'),
    path('listado_empleado/',v.ListadoDoctor.as_view(),name='especialista'),
    path('desactivar_usuario/<int:pk>/', v.DesactivarUsuario.as_view(), name='desactivar_usuario'),
    path('reactivar_usuario/<int:pk>/', v.ReactivarUsuario.as_view(), name='reactivar_usuario'),
    # URL de empleado admin
    path('registrar_admin/',v.RegistrarUsuarioAdmin.as_view(),name='registro_a'),
    path('listado_administradores/',v.ListadoAdmin.as_view(),name='administrador'),
    path('desactivar_admin/<int:pk>/', v.DesactivarUsuarioAdmin.as_view(), name='desactivar_admin'),
    path('reactivar_admin/<int:pk>/', v.ReactivarUsuarioAdmin.as_view(), name='reactivar_admin'),
    # Ficha y edicion de usuarios
    path('usuarios/<int:pk>/', v.DetalleUsuario.as_view(), name='usuario_detalle'),
    path('usuarios/<int:pk>/editar/', v.EditarUsuario.as_view(), name='usuario_editar'),
    # Auditoria de cambios
    path('auditoria/', v.ListadoAuditoria.as_view(), name='auditoria'),
    # Perfil propio
    path('perfil/', v.MiPerfil.as_view(), name='perfil'),
    path('perfil/editar/', v.EditarPerfil.as_view(), name='perfil_editar'),
    path('perfil/contrasena/', v.CambiarContrasena.as_view(), name='password_change'),
    # Historial de diagnostico
    path('historial/',v.moduloHistorialD,name='historial_d'),
    path('historial/<int:pk>/',v.DetalleDiagnostico.as_view(),name='diagnostico_detalle'),
    path('historial/<int:pk>/pdf/',v.informe_diagnostico_pdf,name='diagnostico_pdf'),
    path('historial_personal/',v.moduloHistorialInteracciones,name='historial_m'),
    ################################
    path('diagnostico/etapa1',v.moduloDiagnosticoEtp1,name='diagnostico'),
    path('diagnostico/etapa2/<int:id>',v.moduloDiagnosticoEtp2,name='diagnostico2'),
    path('diagnostico/etapa3/<int:id>',v.moduloDiagnosticoEtp3,name='diagnostico3'),
    path('diagnostico/resultado/<int:paciente_id>/', v.realizar_prediccion, name='diagnosticof'),
    path('diagnostico/resultado/informe/<int:paciente_id>/', v.moduloInformeDiagnostico, name='informeDiagnostico'),
]