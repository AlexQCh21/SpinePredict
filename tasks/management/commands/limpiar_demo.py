from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from tasks.models import Crud_empleado, Crud_paciente, Datos, Historial_paciente, Paciente, Usuario


class Command(BaseCommand):
    help = 'Limpia datos externos del demo y restaura el estado canónico.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh-seed',
            action='store_true',
            default=True,
            help='Ejecuta seed_demo --refresh después de limpiar (por defecto: sí).',
        )
        parser.add_argument(
            '--no-refresh-seed',
            action='store_false',
            dest='refresh_seed',
            help='No ejecuta seed_demo --refresh.',
        )

    def handle(self, *args, **options):
        if not getattr(settings, 'DEMO_MODE', False):
            self.stdout.write(self.style.WARNING('DEMO_MODE desactivado: no se ejecuta limpieza demo.'))
            return

        with transaction.atomic():
            self._delete_non_demo_data()
            if options['refresh_seed']:
                call_command('seed_demo', refresh=True)

        self.stdout.write(self.style.SUCCESS('Limpieza demo completada.'))

    def _delete_file(self, field_file):
        if not field_file:
            return
        try:
            name = field_file.name
        except Exception:
            name = None
        if name:
            try:
                field_file.delete(save=False)
            except Exception:
                pass

    def _delete_non_demo_data(self):
        non_demo_pacientes = list(Paciente.objects.filter(es_demo=False))
        for paciente in non_demo_pacientes:
            self._delete_file(getattr(paciente, 'foto', None))
        Paciente.objects.filter(es_demo=False).delete()

        Historial_paciente.objects.filter(es_demo=False).delete()

        Crud_paciente.objects.filter(es_demo=False).delete()
        Crud_empleado.objects.filter(es_demo=False).delete()

        demo_users = Usuario.objects.filter(es_demo=True)
        Crud_paciente.objects.filter(editor__in=demo_users, afectado__es_demo=False).delete()
        Crud_empleado.objects.filter(editor__in=demo_users).delete()
        Historial_paciente.objects.filter(empleado__in=demo_users, es_demo=False).delete()
