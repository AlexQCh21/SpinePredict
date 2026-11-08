from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from tasks.models import Crud_empleado, Crud_paciente, Datos, Estado, Historial_paciente, Paciente, Padecimiento, Usuario


DEMO_STATE_KEY = '_DEMO_SEED_AT'
DEMO_DATA_VERSION = '2026-11-07'


class Command(BaseCommand):
    help = 'Crea o restaura las cuentas y datos demo compartidos.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh',
            action='store_true',
            help='Restaura datos demo a su estado canónico sin eliminar datos externos.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        refresh = options['refresh']
        estado_activo = self._get_or_create_estado('Activo')
        self._get_or_create_estado('Inactivo')
        hernia, espondilo, normal = self._ensure_padecimientos()

        admin = self._ensure_usuario(
            username=getattr(settings, 'DEMO_ADMIN_USERNAME', 'demo_admin'),
            password=getattr(settings, 'DEMO_ADMIN_PASSWORD', 'Admin12345'),
            defaults=dict(
                primer_nombre='Demo',
                segundo_nombre='',
                apellido_paterno='Administrador',
                apellido_materno='Hospital',
                codigo_empl='DEMOADM',
                usuario_administrador=True,
                estado=estado_activo,
                email='demo_admin@hospital.local',
                telefono='900000001',
                dni='70000001',
                foto=None,
                es_demo=True,
            ),
        )
        especialista = self._ensure_usuario(
            username=getattr(settings, 'DEMO_SPECIALIST_USERNAME', 'demo_especialista'),
            password=getattr(settings, 'DEMO_SPECIALIST_PASSWORD', 'Especialista12345'),
            defaults=dict(
                primer_nombre='Demo',
                segundo_nombre='',
                apellido_paterno='Especialista',
                apellido_materno='Hospital',
                codigo_empl='DEMOESP',
                usuario_administrador=False,
                estado=estado_activo,
                email='demo_especialista@hospital.local',
                telefono='900000002',
                dni='70000002',
                foto=None,
                es_demo=True,
            ),
        )

        if refresh:
            self._purge_demo_generated(admin, especialista)

        paciente_normal = self._ensure_paciente(
            dni='70000011',
            defaults=dict(
                primer_nombre='Ana',
                segundo_nombre='',
                apellido_paterno='Paciente',
                apellido_materno='Demo',
                correo='ana.demo@hospital.local',
                telefono='900000011',
                foto=None,
                activo=True,
                es_demo=True,
            ),
        )
        paciente_hernia = self._ensure_paciente(
            dni='70000012',
            defaults=dict(
                primer_nombre='Luis',
                segundo_nombre='',
                apellido_paterno='Paciente',
                apellido_materno='Demo',
                correo='luis.demo@hospital.local',
                telefono='900000012',
                foto=None,
                activo=True,
                es_demo=True,
            ),
        )
        paciente_espondilo = self._ensure_paciente(
            dni='70000013',
            defaults=dict(
                primer_nombre='Maria',
                segundo_nombre='',
                apellido_paterno='Paciente',
                apellido_materno='Demo',
                correo='maria.demo@hospital.local',
                telefono='900000013',
                foto=None,
                activo=True,
                es_demo=True,
            ),
        )

        self._ensure_historial(
            empleado=especialista,
            paciente=paciente_normal,
            padecimiento=normal,
            precision=Decimal('95.00'),
            datos=dict(
                pelvic_incidence=48.0,
                pelvic_tilt=16.0,
                lumbar_lordosis_angle=52.0,
                sacral_slope=32.0,
                pelvic_radius=120.0,
                degree_spondylolisthesis=1.5,
            ),
        )
        self._ensure_historial(
            empleado=especialista,
            paciente=paciente_hernia,
            padecimiento=hernia,
            precision=Decimal('92.00'),
            datos=dict(
                pelvic_incidence=63.0,
                pelvic_tilt=22.0,
                lumbar_lordosis_angle=39.0,
                sacral_slope=41.0,
                pelvic_radius=98.0,
                degree_spondylolisthesis=5.0,
            ),
        )
        self._ensure_historial(
            empleado=especialista,
            paciente=paciente_espondilo,
            padecimiento=espondilo,
            precision=Decimal('93.00'),
            datos=dict(
                pelvic_incidence=75.0,
                pelvic_tilt=31.0,
                lumbar_lordosis_angle=62.0,
                sacral_slope=44.0,
                pelvic_radius=110.0,
                degree_spondylolisthesis=45.0,
            ),
        )

        self.stdout.write(self.style.SUCCESS(
            f'Seed demo completado (version={DEMO_DATA_VERSION}, refresh={refresh}).'
        ))

    def _get_or_create_estado(self, name):
        estado, _ = Estado.objects.get_or_create(name=name)
        return estado

    def _ensure_padecimientos(self):
        names = ['Hernia de Disco', 'Espondilolistesis', 'Normal']
        by_name = {}
        for name in names:
            by_name[name], _ = Padecimiento.objects.get_or_create(name=name)
        return by_name['Hernia de Disco'], by_name['Espondilolistesis'], by_name['Normal']

    def _ensure_usuario(self, username, password, defaults):
        user, created = Usuario.objects.get_or_create(username=username, defaults=defaults)
        for field, value in defaults.items():
            setattr(user, field, value)
        user.es_demo = True
        user.set_password(password)
        user.save()
        return user

    def _ensure_paciente(self, dni, defaults):
        paciente, _ = Paciente.objects.get_or_create(dni=dni, defaults=defaults)
        for field, value in defaults.items():
            setattr(paciente, field, value)
        paciente.es_demo = True
        paciente.save()
        return paciente

    def _ensure_historial(self, empleado, paciente, padecimiento, precision, datos):
        qs = Historial_paciente.objects.filter(empleado=empleado, paciente=paciente, padecimiento=padecimiento, es_demo=True)
        historial = qs.order_by('id').first()
        if historial is None:
            historial = Historial_paciente.objects.create(
                empleado=empleado,
                paciente=paciente,
                padecimiento=padecimiento,
                precision_value=precision,
                es_demo=True,
            )
        else:
            historial.precision_value = precision
            historial.es_demo = True
            historial.save(update_fields=['precision_value', 'es_demo'])
        Datos.objects.filter(historial_paciente=historial).delete()
        Datos.objects.create(historial_paciente=historial, **datos)
        return historial

    def _purge_demo_generated(self, admin, especialista):
        demo_users = Usuario.objects.filter(es_demo=True)
        demo_pacientes = Paciente.objects.filter(es_demo=True)
        Crud_paciente.objects.filter(es_demo=True).delete()
        Crud_empleado.objects.filter(es_demo=True).delete()
        Crud_paciente.objects.filter(editor__in=demo_users).delete()
        Crud_paciente.objects.filter(afectado__in=demo_pacientes).delete()
        Crud_empleado.objects.filter(editor__in=demo_users).delete()
        Crud_empleado.objects.filter(afectado__in=demo_users).delete()
        Datos.objects.filter(historial_paciente__empleado__in=demo_users).delete()
        Historial_paciente.objects.filter(empleado__in=demo_users).delete()
        Datos.objects.filter(historial_paciente__paciente__in=demo_pacientes).delete()
        Historial_paciente.objects.filter(paciente__in=demo_pacientes).delete()
