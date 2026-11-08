from .models import Crud_empleado, Crud_paciente

ACCION_CREAR = "Crear"
ACCION_EDITAR = "Editar"
ACCION_DESACTIVAR = "Desactivar"
ACCION_REACTIVAR = "Reactivar"
ACCION_PERFIL = "Editar perfil"
ACCION_CONTRASENA = "Cambiar contraseña"


def registrar_accion_empleado(editor, afectado, accion):
    return Crud_empleado.objects.create(
        editor=editor,
        afectado=afectado,
        accion=accion,
    )


def registrar_accion_paciente(editor, afectado, accion):
    return Crud_paciente.objects.create(
        editor=editor,
        afectado=afectado,
        accion=accion,
    )
