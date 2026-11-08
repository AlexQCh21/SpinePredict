from unittest.mock import patch

from django.db import IntegrityError
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from tasks.forms import CrearUsuario, EditarUsuarioForm
from tasks.models import (
    Crud_empleado,
    Crud_paciente,
    Datos,
    Estado,
    Historial_paciente,
    Paciente,
    Padecimiento,
    Usuario,
)


class RolePermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado_activo = Estado.objects.create(name="Activo")
        cls.estado_inactivo = Estado.objects.create(name="Inactivo")

        cls.admin = Usuario.objects.create_user(
            email="admin.roles@test.local",
            username="admin_roles",
            primer_nombre="Admin",
            segundo_nombre="",
            apellido_paterno="Pruebas",
            apellido_materno="Uno",
            password="Admin12345",
        )
        cls.admin.usuario_administrador = True
        cls.admin.estado = cls.estado_activo
        cls.admin.save()

        cls.specialist = Usuario.objects.create_user(
            email="especialista.roles@test.local",
            username="especialista_roles",
            primer_nombre="Especialista",
            segundo_nombre="",
            apellido_paterno="Pruebas",
            apellido_materno="Uno",
            password="Especialista12345",
        )
        cls.specialist.usuario_administrador = False
        cls.specialist.estado = cls.estado_activo
        cls.specialist.save()

        cls.paciente = Paciente.objects.create(
            primer_nombre="Paciente",
            segundo_nombre="",
            apellido_paterno="Pruebas",
            apellido_materno="Uno",
            correo="paciente.roles@test.local",
            telefono="999999999",
            dni="12345678",
        )
        cls.padecimiento = Padecimiento.objects.create(name="Normal")
        cls.historial = Historial_paciente.objects.create(
            empleado=cls.specialist,
            paciente=cls.paciente,
            padecimiento=cls.padecimiento,
            precision_value="90.00",
        )
        Datos.objects.create(
            historial_paciente=cls.historial,
            pelvic_incidence=44.3,
            pelvic_tilt=12.5,
            lumbar_lordosis_angle=36.1,
            sacral_slope=31.8,
            pelvic_radius=124.1,
            degree_spondylolisthesis=5.4,
        )

    def login(self, user):
        self.client.force_login(user)

    def assertAllowed(self, user, name, *args, expected=200):
        self.login(user)
        response = self.client.get(reverse(name, args=args))
        self.assertEqual(
            response.status_code,
            expected,
            msg=f"{name} debía responder {expected} para {user.username} y respondió {response.status_code}",
        )

    def assertBlocked(self, user, name, *args):
        self.login(user)
        response = self.client.get(reverse(name, args=args))
        self.assertEqual(
            response.status_code,
            403,
            msg=f"{name} debía responder 403 para {user.username} y respondió {response.status_code}",
        )

    def test_admin_allowed_pages(self):
        for name in ("dashboard", "paciente", "historial_d", "especialista",
                     "administrador", "registro_e", "registro_a"):
            self.assertAllowed(self.admin, name)

    def test_admin_can_generate_report(self):
        self.assertAllowed(self.admin, "informeDiagnostico", self.paciente.id)

    def test_admin_blocked_clinical_pages(self):
        self.assertBlocked(self.admin, "diagnostico")
        self.assertBlocked(self.admin, "diagnostico2", self.paciente.id)
        self.assertBlocked(self.admin, "diagnostico3", self.paciente.id)
        self.assertBlocked(self.admin, "diagnosticof", self.paciente.id)
        self.assertBlocked(self.admin, "historial_m")
        self.assertBlocked(self.admin, "registro_p")

    def test_specialist_allowed_pages(self):
        for name in ("dashboard", "paciente", "registro_p", "diagnostico",
                     "historial_d", "historial_m"):
            self.assertAllowed(self.specialist, name)
        self.assertAllowed(self.specialist, "diagnostico2", self.paciente.id)
        self.assertAllowed(self.specialist, "diagnostico3", self.paciente.id)
        self.assertAllowed(self.specialist, "informeDiagnostico", self.paciente.id)

    def test_specialist_blocked_admin_pages(self):
        for name in ("especialista", "administrador", "registro_e", "registro_a"):
            self.assertBlocked(self.specialist, name)

    def test_unauthenticated_users_redirected_to_login(self):
        self.client.logout()
        for name in ("dashboard", "paciente", "registro_p", "diagnostico",
                     "historial_d", "historial_m", "especialista",
                     "administrador", "registro_e", "registro_a"):
            response = self.client.get(reverse(name))
            self.assertEqual(
                response.status_code,
                302,
                msg=f"{name} debía redirigir a login y respondió {response.status_code}",
            )
            self.assertTrue(response["Location"].startswith("/accounts/login/"))

    def test_specialist_cannot_create_users(self):
        before = Usuario.objects.count()
        self.login(self.specialist)
        response = self.client.post(reverse("registro_e"), {})
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse("registro_a"), {})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Usuario.objects.count(), before)

    def test_specialist_cannot_deactivate_users(self):
        self.login(self.specialist)
        response = self.client.post(
            reverse("desactivar_usuario", args=[self.specialist.id])
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            reverse("desactivar_admin", args=[self.admin.id])
        )
        self.assertEqual(response.status_code, 403)
        self.admin.refresh_from_db()
        self.specialist.refresh_from_db()
        self.assertEqual(self.admin.estado_id, self.estado_activo.id)
        self.assertEqual(self.specialist.estado_id, self.estado_activo.id)

    def test_specialist_can_create_and_deactivate_patient(self):
        self.login(self.specialist)
        response = self.client.post(
            reverse("registro_p"),
            {
                "primer_nombre": "Nuevo",
                "segundo_nombre": "",
                "apellido_paterno": "Paciente",
                "apellido_materno": "Prueba",
                "correo": "nuevo.paciente@test.local",
                "telefono": "988888888",
                "dni": "87654321",
            },
        )
        self.assertEqual(response.status_code, 302)
        nuevo = Paciente.objects.get(dni="87654321")

        response = self.client.post(
            reverse("desactivar_paciente", args=[nuevo.id])
        )
        self.assertEqual(response.status_code, 302)
        nuevo.refresh_from_db()
        self.assertFalse(nuevo.activo)

    def test_admin_cannot_create_or_deactivate_patients(self):
        self.login(self.admin)
        before = Paciente.objects.count()
        response = self.client.post(
            reverse("registro_p"),
            {
                "primer_nombre": "Bloqueado",
                "segundo_nombre": "",
                "apellido_paterno": "Paciente",
                "apellido_materno": "Prueba",
                "correo": "bloqueado@test.local",
                "telefono": "977777777",
                "dni": "11223344",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Paciente.objects.count(), before)

        response = self.client.post(
            reverse("desactivar_paciente", args=[self.paciente.id])
        )
        self.assertEqual(response.status_code, 403)
        self.paciente.refresh_from_db()
        self.assertTrue(self.paciente.activo)

    def test_specialist_registration_ignores_admin_flag(self):
        self.login(self.admin)
        response = self.client.post(
            reverse("registro_e"),
            {
                "primer_nombre": "Nuevo",
                "segundo_nombre": "",
                "apellido_paterno": "Especialista",
                "apellido_materno": "Prueba",
                "codigo_empl": "ESP9999",
                "estado": self.estado_activo.id,
                "username": "nuevo_especialista",
                "email": "nuevo.especialista@test.local",
                "telefono": "966666666",
                "dni": "55667788",
                "contrasena": "Especialista12345",
                "confirmar_contrasena": "Especialista12345",
                "usuario_administrador": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        creado = Usuario.objects.get(username="nuevo_especialista")
        self.assertFalse(creado.usuario_administrador)

    def test_admin_registration_creates_admin(self):
        self.login(self.admin)
        response = self.client.post(
            reverse("registro_a"),
            {
                "primer_nombre": "Nuevo",
                "segundo_nombre": "",
                "apellido_paterno": "Administrador",
                "apellido_materno": "Prueba",
                "codigo_empl": "ADM9999",
                "estado": self.estado_activo.id,
                "username": "nuevo_admin",
                "email": "nuevo.admin@test.local",
                "telefono": "955555555",
                "dni": "44556677",
                "contrasena": "Admin12345",
                "confirmar_contrasena": "Admin12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        creado = Usuario.objects.get(username="nuevo_admin")
        self.assertTrue(creado.usuario_administrador)

    def test_admin_can_deactivate_specialist(self):
        objetivo = Usuario.objects.create_user(
            email="objetivo.especialista@test.local",
            username="objetivo_especialista",
            primer_nombre="Objetivo",
            segundo_nombre="",
            apellido_paterno="Pruebas",
            apellido_materno="Dos",
            password="Especialista12345",
        )
        objetivo.estado = self.estado_activo
        objetivo.save()

        self.login(self.admin)
        response = self.client.post(
            reverse("desactivar_usuario", args=[objetivo.id])
        )
        self.assertEqual(response.status_code, 302)
        objetivo.refresh_from_db()
        self.assertEqual(objetivo.estado_id, self.estado_inactivo.id)

    def test_admin_can_deactivate_admin(self):
        objetivo = Usuario.objects.create_user(
            email="objetivo.admin@test.local",
            username="objetivo_admin",
            primer_nombre="Objetivo",
            segundo_nombre="",
            apellido_paterno="Pruebas",
            apellido_materno="Dos",
            password="Admin12345",
        )
        objetivo.usuario_administrador = True
        objetivo.estado = self.estado_activo
        objetivo.save()

        self.login(self.admin)
        response = self.client.post(
            reverse("desactivar_admin", args=[objetivo.id])
        )
        self.assertEqual(response.status_code, 302)
        objetivo.refresh_from_db()
        self.assertEqual(objetivo.estado_id, self.estado_inactivo.id)

    def test_user_registration_form_has_no_role_field(self):
        self.assertNotIn("usuario_administrador", CrearUsuario().fields)


class UserStateTests(TestCase):
    PASSWORD = "ClaveSegura123"

    @classmethod
    def setUpTestData(cls):
        cls.activo = Estado.objects.create(name="Activo")
        cls.inactivo = Estado.objects.create(name="Inactivo")
        cls.admin = cls.crear_usuario("admin_estado", admin=True, estado=cls.activo)
        cls.specialist = cls.crear_usuario(
            "especialista_estado", admin=False, estado=cls.activo
        )

    @classmethod
    def crear_usuario(cls, username, admin, estado):
        usuario = Usuario.objects.create_user(
            email=f"{username}@test.local",
            username=username,
            primer_nombre="Usuario",
            segundo_nombre="",
            apellido_paterno=username.title(),
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        usuario.usuario_administrador = admin
        usuario.estado = estado
        usuario.save()
        return usuario

    def test_active_user_can_login(self):
        self.assertTrue(
            self.client.login(
                username=self.specialist.username, password=self.PASSWORD
            )
        )

    def test_inactive_user_cannot_login(self):
        self.specialist.estado = self.inactivo
        self.specialist.save()

        self.assertFalse(
            self.client.login(
                username=self.specialist.username, password=self.PASSWORD
            )
        )

    def test_inactive_user_login_endpoint_rejects_credentials(self):
        self.specialist.estado = self.inactivo
        self.specialist.save()

        response = self.client.post(
            reverse("login"),
            {"username": self.specialist.username, "password": self.PASSWORD},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_user_without_state_cannot_login(self):
        sin_estado = self.crear_usuario(
            "usuario_sin_estado", admin=False, estado=None
        )

        self.assertFalse(
            self.client.login(username=sin_estado.username, password=self.PASSWORD)
        )

    def test_deactivated_session_is_closed(self):
        self.client.force_login(self.specialist)
        self.specialist.estado = self.inactivo
        self.specialist.save()

        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(
            response, reverse("login"), fetch_redirect_response=False
        )

    def test_admin_can_reactivate_specialist(self):
        self.specialist.estado = self.inactivo
        self.specialist.save()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("reactivar_usuario", args=[self.specialist.id])
        )

        self.assertRedirects(response, reverse("especialista"))
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.estado, self.activo)

    def test_admin_can_reactivate_admin(self):
        self.admin.estado = self.inactivo
        self.admin.save()
        reactivador = self.crear_usuario(
            "admin_reactivador", admin=True, estado=self.activo
        )
        self.client.force_login(reactivador)

        response = self.client.post(reverse("reactivar_admin", args=[self.admin.id]))

        self.assertRedirects(response, reverse("administrador"))
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, self.activo)

    def test_cannot_deactivate_last_active_admin(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("desactivar_admin", args=[self.admin.id])
        )

        self.assertRedirects(response, reverse("administrador"))
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, self.activo)

    def test_can_deactivate_admin_when_another_active_admin_exists(self):
        otro_admin = self.crear_usuario(
            "admin_extra", admin=True, estado=self.activo
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("desactivar_admin", args=[otro_admin.id])
        )

        self.assertRedirects(response, reverse("administrador"))
        otro_admin.refresh_from_db()
        self.assertEqual(otro_admin.estado, self.inactivo)

    def test_specialist_endpoint_rejects_admin_target(self):
        self.client.force_login(self.admin)

        self.assertEqual(
            self.client.post(
                reverse("desactivar_usuario", args=[self.admin.id])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("reactivar_usuario", args=[self.admin.id])
            ).status_code,
            404,
        )

    def test_admin_endpoint_rejects_specialist_target(self):
        self.client.force_login(self.admin)

        self.assertEqual(
            self.client.post(
                reverse("desactivar_admin", args=[self.specialist.id])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("reactivar_admin", args=[self.specialist.id])
            ).status_code,
            404,
        )

    def test_specialist_cannot_manage_user_state(self):
        self.client.force_login(self.specialist)

        self.assertEqual(
            self.client.post(
                reverse("reactivar_usuario", args=[self.specialist.id])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("reactivar_admin", args=[self.admin.id])
            ).status_code,
            403,
        )

    def test_admin_list_shows_inactive_users_and_reactivation_action(self):
        self.specialist.estado = self.inactivo
        self.specialist.save()
        self.client.force_login(self.admin)

        response = self.client.get(reverse("especialista"))

        self.assertContains(response, "Inactivo")
        self.assertContains(
            response, reverse("reactivar_usuario", args=[self.specialist.id])
        )


class PredictionFlowTests(TestCase):
    PASSWORD = "ClaveSegura123"
    FEATURES = {
        "pelvic_incidence": "44.318907",
        "pelvic_tilt": "12.537992",
        "lumbar_lordosis_angle": "36.098763",
        "sacral_slope": "31.780915",
        "pelvic_radius": "124.115836",
        "degree_spondylolisthesis": "5.415825",
    }

    @classmethod
    def setUpTestData(cls):
        estado_activo = Estado.objects.create(name="Activo")
        estado_inactivo = Estado.objects.create(name="Inactivo")

        cls.especialista = Usuario.objects.create_user(
            email="especialista.prediccion@test.local",
            username="especialista_prediccion",
            primer_nombre="Especialista",
            segundo_nombre="",
            apellido_paterno="Prediccion",
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        cls.especialista.usuario_administrador = False
        cls.especialista.estado = estado_activo
        cls.especialista.save()

        cls.admin = Usuario.objects.create_user(
            email="admin.prediccion@test.local",
            username="admin_prediccion",
            primer_nombre="Admin",
            segundo_nombre="",
            apellido_paterno="Prediccion",
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        cls.admin.usuario_administrador = True
        cls.admin.estado = estado_activo
        cls.admin.save()

        cls.paciente_activo = Paciente.objects.create(
            primer_nombre="Paciente",
            segundo_nombre="",
            apellido_paterno="Activo",
            apellido_materno="Pruebas",
            correo="paciente.activo@test.local",
            telefono="999999999",
            dni="12345678",
        )
        cls.paciente_inactivo = Paciente.objects.create(
            primer_nombre="Paciente",
            segundo_nombre="",
            apellido_paterno="Inactivo",
            apellido_materno="Pruebas",
            correo="paciente.inactivo@test.local",
            telefono="988888888",
            dni="87654321",
            activo=False,
        )

        Padecimiento.objects.update_or_create(
            id=1, defaults={"name": "Hernia de Disco"}
        )
        Padecimiento.objects.update_or_create(
            id=2, defaults={"name": "Espondilolistesis"}
        )
        Padecimiento.objects.update_or_create(id=3, defaults={"name": "Normal"})

    def url_prediccion(self, paciente=None):
        paciente = paciente or self.paciente_activo
        return reverse("diagnosticof", args=[paciente.id])

    def test_get_prediction_is_not_allowed_and_does_not_write(self):
        self.client.force_login(self.especialista)

        response = self.client.get(self.url_prediccion())

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Historial_paciente.objects.count(), 0)
        self.assertEqual(Datos.objects.count(), 0)

    def test_prediction_with_valid_parameters_creates_history_and_data(self):
        self.client.force_login(self.especialista)

        response = self.client.post(self.url_prediccion(), self.FEATURES)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Historial_paciente.objects.count(), 1)
        self.assertEqual(Datos.objects.count(), 1)

        historial = Historial_paciente.objects.get()
        self.assertEqual(historial.empleado, self.especialista)
        self.assertEqual(historial.paciente, self.paciente_activo)
        self.assertIn(historial.padecimiento_id, (1, 2, 3))

        datos = Datos.objects.get(historial_paciente=historial)
        self.assertAlmostEqual(
            datos.pelvic_incidence, float(self.FEATURES["pelvic_incidence"])
        )
        self.assertAlmostEqual(
            datos.pelvic_tilt, float(self.FEATURES["pelvic_tilt"])
        )
        self.assertAlmostEqual(
            datos.lumbar_lordosis_angle,
            float(self.FEATURES["lumbar_lordosis_angle"]),
        )
        self.assertAlmostEqual(
            datos.sacral_slope, float(self.FEATURES["sacral_slope"])
        )
        self.assertAlmostEqual(
            datos.pelvic_radius, float(self.FEATURES["pelvic_radius"])
        )
        self.assertAlmostEqual(
            datos.degree_spondylolisthesis,
            float(self.FEATURES["degree_spondylolisthesis"]),
        )

    def test_prediction_requires_all_parameters(self):
        self.client.force_login(self.especialista)

        response = self.client.post(self.url_prediccion(), {})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Historial_paciente.objects.count(), 0)
        self.assertEqual(set(response.context["form"].errors), set(self.FEATURES))

    def test_prediction_rejects_negative_values(self):
        self.client.force_login(self.especialista)
        datos = dict(self.FEATURES, pelvic_tilt="-1")

        response = self.client.post(self.url_prediccion(), datos)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Historial_paciente.objects.count(), 0)
        self.assertIn("pelvic_tilt", response.context["form"].errors)

    def test_prediction_rejects_non_numeric_values(self):
        self.client.force_login(self.especialista)
        datos = dict(self.FEATURES, pelvic_radius="abc")

        response = self.client.post(self.url_prediccion(), datos)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Historial_paciente.objects.count(), 0)
        self.assertIn("pelvic_radius", response.context["form"].errors)

    def test_prediction_rejects_non_finite_values(self):
        self.client.force_login(self.especialista)
        datos = dict(self.FEATURES, sacral_slope="nan")

        response = self.client.post(self.url_prediccion(), datos)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Historial_paciente.objects.count(), 0)
        self.assertIn("sacral_slope", response.context["form"].errors)

    def test_prediction_requires_specialist(self):
        self.client.force_login(self.admin)

        response = self.client.post(self.url_prediccion(), self.FEATURES)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Historial_paciente.objects.count(), 0)

    def test_inactive_patient_cannot_reach_diagnostic_stages(self):
        self.client.force_login(self.especialista)

        for name in ("diagnostico2", "diagnostico3"):
            response = self.client.get(reverse(name, args=[self.paciente_inactivo.id]))
            self.assertEqual(response.status_code, 404)

        response = self.client.post(
            self.url_prediccion(self.paciente_inactivo), self.FEATURES
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Historial_paciente.objects.count(), 0)

    @patch("tasks.views.Datos.objects.create", side_effect=IntegrityError("fallo"))
    def test_prediction_is_atomic_when_data_save_fails(self, datos_create):
        self.client.force_login(self.especialista)

        with self.assertRaises(IntegrityError):
            self.client.post(self.url_prediccion(), self.FEATURES)

        datos_create.assert_called_once()
        self.assertEqual(Historial_paciente.objects.count(), 0)
        self.assertEqual(Datos.objects.count(), 0)


class PatientManagementTests(TestCase):
    PASSWORD = "ClaveSegura123"

    @classmethod
    def setUpTestData(cls):
        estado_activo = Estado.objects.create(name="Activo")
        estado_inactivo = Estado.objects.create(name="Inactivo")

        cls.especialista = Usuario.objects.create_user(
            email="especialista.pacientes@test.local",
            username="especialista_pacientes",
            primer_nombre="Especialista",
            segundo_nombre="",
            apellido_paterno="Pacientes",
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        cls.especialista.usuario_administrador = False
        cls.especialista.estado = estado_activo
        cls.especialista.save()

        cls.admin = Usuario.objects.create_user(
            email="admin.pacientes@test.local",
            username="admin_pacientes",
            primer_nombre="Admin",
            segundo_nombre="",
            apellido_paterno="Pacientes",
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        cls.admin.usuario_administrador = True
        cls.admin.estado = estado_activo
        cls.admin.save()

        cls.paciente_activo = Paciente.objects.create(
            primer_nombre="Paciente",
            segundo_nombre="",
            apellido_paterno="Activo",
            apellido_materno="Pruebas",
            correo="paciente.activo@test.local",
            telefono="999999999",
            dni="12345678",
        )
        cls.paciente_inactivo = Paciente.objects.create(
            primer_nombre="Paciente",
            segundo_nombre="",
            apellido_paterno="Inactivo",
            apellido_materno="Pruebas",
            correo="paciente.inactivo@test.local",
            telefono="988888888",
            dni="87654321",
            activo=False,
        )
        cls.paciente_ajeno = Paciente.objects.create(
            primer_nombre="Paciente",
            segundo_nombre="",
            apellido_paterno="Ajeno",
            apellido_materno="Pruebas",
            correo="paciente.ajeno@test.local",
            telefono="977777777",
            dni="11223344",
        )

        padecimiento = Padecimiento.objects.create(name="Hernia de Disco")
        cls.historial = Historial_paciente.objects.create(
            empleado=cls.especialista,
            paciente=cls.paciente_activo,
            padecimiento=padecimiento,
            precision_value="91.50",
        )

    def datos_paciente(self, paciente, **cambios):
        datos = {
            "primer_nombre": paciente.primer_nombre,
            "segundo_nombre": paciente.segundo_nombre,
            "apellido_paterno": paciente.apellido_paterno,
            "apellido_materno": paciente.apellido_materno,
            "correo": paciente.correo,
            "telefono": paciente.telefono,
            "dni": paciente.dni,
        }
        datos.update(cambios)
        return datos

    def test_admin_can_view_active_and_inactive_patient_detail(self):
        self.client.force_login(self.admin)

        for paciente in (self.paciente_activo, self.paciente_inactivo):
            response = self.client.get(
                reverse("paciente_detalle", args=[paciente.id])
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, paciente.primer_nombre)
            self.assertContains(response, paciente.dni)

    def test_specialist_can_view_detail_with_history(self):
        self.client.force_login(self.especialista)

        response = self.client.get(
            reverse("paciente_detalle", args=[self.paciente_activo.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hernia de disco")
        self.assertContains(response, self.especialista.primer_nombre)
        self.assertEqual(response.context["cantidad"], 1)
        self.assertEqual(
            str(response.context["historial"][0].precision_value), "91.50"
        )

    def test_unauthenticated_users_redirected_from_detail(self):
        response = self.client.get(
            reverse("paciente_detalle", args=[self.paciente_activo.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/accounts/login/"))

    def test_specialist_can_edit_active_patient(self):
        self.client.force_login(self.especialista)

        response = self.client.post(
            reverse("paciente_editar", args=[self.paciente_activo.id]),
            self.datos_paciente(
                self.paciente_activo,
                primer_nombre="Paciente Editado",
                correo="paciente.editado@test.local",
            ),
        )

        self.assertRedirects(
            response,
            reverse("paciente_detalle", args=[self.paciente_activo.id]),
        )
        self.paciente_activo.refresh_from_db()
        self.assertEqual(self.paciente_activo.primer_nombre, "Paciente Editado")
        self.assertEqual(
            self.paciente_activo.correo, "paciente.editado@test.local"
        )

    def test_edit_patient_validates_unique_dni(self):
        self.client.force_login(self.especialista)

        response = self.client.post(
            reverse("paciente_editar", args=[self.paciente_activo.id]),
            self.datos_paciente(
                self.paciente_activo, dni=self.paciente_ajeno.dni
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("dni", response.context["form"].errors)
        self.paciente_activo.refresh_from_db()
        self.assertEqual(self.paciente_activo.dni, "12345678")

    def test_admin_cannot_edit_patient(self):
        self.client.force_login(self.admin)
        url = reverse("paciente_editar", args=[self.paciente_activo.id])

        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(
            self.client.post(url, self.datos_paciente(self.paciente_activo)).status_code,
            403,
        )

    def test_inactive_patient_cannot_be_edited(self):
        self.client.force_login(self.especialista)
        url = reverse("paciente_editar", args=[self.paciente_inactivo.id])

        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.post(
                url, self.datos_paciente(self.paciente_inactivo)
            ).status_code,
            404,
        )

    def test_patient_list_shows_active_only_by_default(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("paciente"))

        self.assertContains(response, self.paciente_activo.dni)
        self.assertNotContains(response, self.paciente_inactivo.dni)

    def test_patient_list_can_show_inactive_patients(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("paciente"), {"inactivos": "1"})

        self.assertContains(response, self.paciente_inactivo.dni)
        self.assertNotContains(response, self.paciente_activo.dni)

    def test_patient_list_links_to_detail_and_actions(self):
        self.client.force_login(self.especialista)

        response = self.client.get(reverse("paciente"))

        self.assertContains(
            response, reverse("paciente_detalle", args=[self.paciente_activo.id])
        )
        self.assertContains(
            response, reverse("paciente_editar", args=[self.paciente_activo.id])
        )

    def test_inactive_detail_hides_edit_and_diagnose_actions(self):
        self.client.force_login(self.especialista)

        response = self.client.get(
            reverse("paciente_detalle", args=[self.paciente_inactivo.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("paciente_editar", args=[self.paciente_inactivo.id]),
        )
        self.assertNotContains(
            response,
            reverse("diagnostico2", args=[self.paciente_inactivo.id]),
        )

    def test_admin_detail_hides_edit_and_diagnose_actions(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("paciente_detalle", args=[self.paciente_activo.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("paciente_editar", args=[self.paciente_activo.id]),
        )
        self.assertNotContains(
            response,
            reverse("diagnostico2", args=[self.paciente_activo.id]),
        )

    def test_cannot_deactivate_already_inactive_patient(self):
        self.client.force_login(self.especialista)

        response = self.client.post(
            reverse("desactivar_paciente", args=[self.paciente_inactivo.id])
        )

        self.assertEqual(response.status_code, 404)


class UserManagementTests(TestCase):
    PASSWORD = "ClaveSegura123"

    @classmethod
    def setUpTestData(cls):
        cls.activo = Estado.objects.create(name="Activo")
        cls.inactivo = Estado.objects.create(name="Inactivo")
        cls.admin = cls.crear_usuario(
            "admin_ficha", "admin.ficha@test.local", admin=True, estado=cls.activo
        )
        cls.specialist = cls.crear_usuario(
            "esp_ficha", "esp.ficha@test.local", admin=False, estado=cls.activo
        )
        cls.otro_admin = cls.crear_usuario(
            "admin_ficha2", "admin.ficha2@test.local", admin=True, estado=cls.activo
        )
        cls.specialist_inactivo = cls.crear_usuario(
            "esp_ficha2", "esp.ficha2@test.local", admin=False, estado=cls.inactivo
        )

        paciente = Paciente.objects.create(
            primer_nombre="Paciente",
            segundo_nombre="",
            apellido_paterno="Ficha",
            apellido_materno="Pruebas",
            correo="paciente.ficha@test.local",
            telefono="999999999",
            dni="12345678",
        )
        padecimiento = Padecimiento.objects.create(name="Normal")
        cls.historial = Historial_paciente.objects.create(
            empleado=cls.specialist,
            paciente=paciente,
            padecimiento=padecimiento,
            precision_value="88.00",
        )

    @classmethod
    def crear_usuario(cls, username, email, admin, estado):
        usuario = Usuario.objects.create_user(
            email=email,
            username=username,
            primer_nombre="Nombre",
            segundo_nombre="",
            apellido_paterno="Apellido",
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        usuario.usuario_administrador = admin
        usuario.estado = estado
        usuario.codigo_empl = "EMP0001"
        usuario.telefono = "999999999"
        usuario.dni = "12345678"
        usuario.save()
        return usuario

    def datos_usuario(self, usuario, **cambios):
        datos = {
            "primer_nombre": usuario.primer_nombre,
            "segundo_nombre": usuario.segundo_nombre,
            "apellido_paterno": usuario.apellido_paterno,
            "apellido_materno": usuario.apellido_materno,
            "codigo_empl": usuario.codigo_empl,
            "username": usuario.username,
            "email": usuario.email,
            "telefono": usuario.telefono or "",
            "dni": usuario.dni or "",
        }
        datos.update(cambios)
        return datos

    def test_admin_can_view_specialist_and_admin_detail(self):
        self.client.force_login(self.admin)

        for usuario in (self.specialist, self.otro_admin):
            response = self.client.get(
                reverse("usuario_detalle", args=[usuario.id])
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, usuario.username)
            self.assertContains(response, usuario.email)

    def test_detail_shows_role_and_specialist_diagnostics(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("usuario_detalle", args=[self.specialist.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Especialista")
        self.assertContains(response, "Diagnósticos recientes")
        self.assertContains(response, "Normal")
        self.assertEqual(response.context["cantidad_diagnosticos"], 1)

    def test_admin_detail_does_not_show_diagnostics(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("usuario_detalle", args=[self.otro_admin.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrador")
        self.assertNotContains(response, "Diagnósticos recientes")

    def test_inactive_user_detail_is_accessible(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("usuario_detalle", args=[self.specialist_inactivo.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inactivo")

    def test_specialist_cannot_view_or_edit_users(self):
        self.client.force_login(self.specialist)
        detalle = reverse("usuario_detalle", args=[self.otro_admin.id])
        editar = reverse("usuario_editar", args=[self.otro_admin.id])

        self.assertEqual(self.client.get(detalle).status_code, 403)
        self.assertEqual(self.client.get(editar).status_code, 403)
        self.assertEqual(
            self.client.post(
                editar, self.datos_usuario(self.otro_admin)
            ).status_code,
            403,
        )

    def test_unauthenticated_users_redirected_from_user_pages(self):
        self.client.logout()

        for name in ("usuario_detalle", "usuario_editar"):
            response = self.client.get(reverse(name, args=[self.specialist.id]))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response["Location"].startswith("/accounts/login/"))

    def test_admin_can_edit_specialist_preserving_role_and_state(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("usuario_editar", args=[self.specialist.id]),
            self.datos_usuario(
                self.specialist,
                primer_nombre="Especialista Editado",
                email="esp.editado@test.local",
                usuario_administrador="on",
                estado=self.inactivo.id,
            ),
        )

        self.assertRedirects(
            response, reverse("usuario_detalle", args=[self.specialist.id])
        )
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.primer_nombre, "Especialista Editado")
        self.assertEqual(self.specialist.email, "esp.editado@test.local")
        self.assertFalse(self.specialist.usuario_administrador)
        self.assertEqual(self.specialist.estado_id, self.activo.id)

    def test_admin_can_edit_admin_preserving_role(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("usuario_editar", args=[self.otro_admin.id]),
            self.datos_usuario(
                self.otro_admin,
                apellido_paterno="Editado",
                usuario_administrador="on",
            ),
        )

        self.assertRedirects(
            response, reverse("usuario_detalle", args=[self.otro_admin.id])
        )
        self.otro_admin.refresh_from_db()
        self.assertEqual(self.otro_admin.apellido_paterno, "Editado")
        self.assertTrue(self.otro_admin.usuario_administrador)

    def test_edit_user_validates_unique_username(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("usuario_editar", args=[self.specialist.id]),
            self.datos_usuario(
                self.specialist, username=self.otro_admin.username
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.username, "esp_ficha")

    def test_edit_user_validates_unique_email(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("usuario_editar", args=[self.specialist.id]),
            self.datos_usuario(self.specialist, email=self.otro_admin.email),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.email, "esp.ficha@test.local")

    def test_edit_form_excludes_sensitive_fields(self):
        form = EditarUsuarioForm(instance=self.specialist)

        for field in (
            "usuario_administrador",
            "estado",
            "contrasena",
            "confirmar_contrasena",
        ):
            self.assertNotIn(field, form.fields)

    def test_inactive_user_can_be_edited(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("usuario_editar", args=[self.specialist_inactivo.id]),
            self.datos_usuario(
                self.specialist_inactivo, primer_nombre="Reactivado"
            ),
        )

        self.assertRedirects(
            response,
            reverse("usuario_detalle", args=[self.specialist_inactivo.id]),
        )
        self.specialist_inactivo.refresh_from_db()
        self.assertEqual(self.specialist_inactivo.primer_nombre, "Reactivado")
        self.assertEqual(self.specialist_inactivo.estado_id, self.inactivo.id)

    def test_user_lists_link_to_detail_and_edit(self):
        self.client.force_login(self.admin)

        for name, usuario in (
            ("especialista", self.specialist),
            ("administrador", self.otro_admin),
        ):
            response = self.client.get(reverse(name))
            self.assertContains(
                response, reverse("usuario_detalle", args=[usuario.id])
            )
            self.assertContains(
                response, reverse("usuario_editar", args=[usuario.id])
            )


class DiagnosticHistoryTests(TestCase):
    PASSWORD = "ClaveSegura123"

    @classmethod
    def setUpTestData(cls):
        estado_activo = Estado.objects.create(name="Activo")

        cls.admin = Usuario.objects.create_user(
            email="admin.historial@test.local",
            username="admin_historial",
            primer_nombre="Admin",
            segundo_nombre="",
            apellido_paterno="Historial",
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        cls.admin.usuario_administrador = True
        cls.admin.estado = estado_activo
        cls.admin.codigo_empl = "ADM0001"
        cls.admin.save()

        cls.specialist = Usuario.objects.create_user(
            email="especialista.historial@test.local",
            username="esp_historial",
            primer_nombre="Especialista",
            segundo_nombre="",
            apellido_paterno="Historial",
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        cls.specialist.usuario_administrador = False
        cls.specialist.estado = estado_activo
        cls.specialist.codigo_empl = "ESP0001"
        cls.specialist.save()

        cls.paciente = Paciente.objects.create(
            primer_nombre="Paciente",
            segundo_nombre="",
            apellido_paterno="Historial",
            apellido_materno="Pruebas",
            correo="paciente.historial@test.local",
            telefono="999999999",
            dni="12345678",
        )
        cls.padecimiento = Padecimiento.objects.create(name="Hernia de Disco")

        cls.historial = Historial_paciente.objects.create(
            empleado=cls.specialist,
            paciente=cls.paciente,
            padecimiento=cls.padecimiento,
            precision_value="91.50",
        )
        Datos.objects.create(
            historial_paciente=cls.historial,
            pelvic_incidence=44.3,
            pelvic_tilt=12.5,
            lumbar_lordosis_angle=36.1,
            sacral_slope=31.8,
            pelvic_radius=124.1,
            degree_spondylolisthesis=5.4,
        )

        cls.historial_sin_datos = Historial_paciente.objects.create(
            empleado=cls.specialist,
            paciente=cls.paciente,
            padecimiento=cls.padecimiento,
            precision_value="50.00",
        )

    def test_admin_can_view_diagnostic_detail(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("diagnostico_detalle", args=[self.historial.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hernia de disco")
        self.assertEqual(
            str(response.context["historial_paciente"].precision_value),
            str(self.historial.precision_value),
        )
        self.assertEqual(response.context["datos"].pelvic_incidence, 44.3)
        self.assertEqual(response.context["datos"].pelvic_radius, 124.1)
        self.assertEqual(
            response.context["datos"].pk,
            self.historial.datos_set.first().pk,
        )

    def test_specialist_can_view_diagnostic_detail(self):
        self.client.force_login(self.specialist)

        response = self.client.get(
            reverse("diagnostico_detalle", args=[self.historial.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paciente")
        self.assertContains(response, "Especialista")

    def test_unauthenticated_users_redirected_from_detail(self):
        response = self.client.get(
            reverse("diagnostico_detalle", args=[self.historial.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/accounts/login/"))

    def test_detail_without_data_shows_empty_state(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("diagnostico_detalle", args=[self.historial_sin_datos.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sin parámetros registrados")

    def test_detail_for_unknown_diagnostic_returns_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("diagnostico_detalle", args=[9999])
        )

        self.assertEqual(response.status_code, 404)

    def test_pdf_is_generated_for_specific_diagnostic(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("diagnostico_pdf", args=[self.historial.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(
            f'diagnostico_{self.historial.id}.pdf',
            response["Content-Disposition"],
        )
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_specialist_can_download_pdf(self):
        self.client.force_login(self.specialist)

        response = self.client.get(
            reverse("diagnostico_pdf", args=[self.historial.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_pdf_requires_login(self):
        response = self.client.get(
            reverse("diagnostico_pdf", args=[self.historial.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/accounts/login/"))

    def test_pdf_for_unknown_diagnostic_returns_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("diagnostico_pdf", args=[9999]))

        self.assertEqual(response.status_code, 404)

    def test_pdf_without_data_returns_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("diagnostico_pdf", args=[self.historial_sin_datos.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_history_lists_link_to_detail_and_pdf(self):
        self.client.force_login(self.admin)

        for name in ("historial_d",):
            response = self.client.get(reverse(name))
            self.assertContains(
                response,
                reverse("diagnostico_detalle", args=[self.historial.id]),
            )
            self.assertContains(
                response,
                reverse("diagnostico_pdf", args=[self.historial.id]),
            )

    def test_specialist_history_links_include_origen(self):
        self.client.force_login(self.specialist)

        response = self.client.get(reverse("historial_m"))

        self.assertContains(
            response,
            reverse("diagnostico_detalle", args=[self.historial.id])
            + "?origen=mis",
        )
        self.assertContains(
            response,
            reverse("diagnostico_pdf", args=[self.historial.id]),
        )


class ListingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.activo = Estado.objects.create(name="Activo")
        cls.inactivo = Estado.objects.create(name="Inactivo")

        cls.admin = Usuario.objects.create_user(
            email="admin.listas@test.local",
            username="admin_listas",
            primer_nombre="Admin",
            segundo_nombre="",
            apellido_paterno="Listas",
            apellido_materno="Pruebas",
            password=None,
        )
        cls.admin.usuario_administrador = True
        cls.admin.estado = cls.activo
        cls.admin.save()

        cls.specialist = Usuario.objects.create_user(
            email="esp.listas@test.local",
            username="esp_listas",
            primer_nombre="Especialista",
            segundo_nombre="",
            apellido_paterno="Listas",
            apellido_materno="Pruebas",
            password=None,
        )
        cls.specialist.usuario_administrador = False
        cls.specialist.estado = cls.activo
        cls.specialist.save()

        for i in range(25):
            Paciente.objects.create(
                primer_nombre=f"Paciente{i:02d}",
                segundo_nombre="",
                apellido_paterno="Listado",
                apellido_materno="Pruebas",
                correo=f"paciente{i:02d}@test.local",
                telefono="999999999",
                dni=f"{10000000 + i:08d}",
            )

        cls.paciente_buscado = Paciente.objects.create(
            primer_nombre="Buscado",
            segundo_nombre="",
            apellido_paterno="Especial",
            apellido_materno="Pruebas",
            correo="buscado@test.local",
            telefono="988888888",
            dni="20000000",
        )
        cls.paciente_inactivo = Paciente.objects.create(
            primer_nombre="Inactivo",
            segundo_nombre="",
            apellido_paterno="Buscado",
            apellido_materno="Pruebas",
            correo="inactivo@test.local",
            telefono="977777777",
            dni="30000000",
            activo=False,
        )

        for i in range(25):
            usuario = Usuario.objects.create_user(
                email=f"bulk.esp{i:02d}@test.local",
                username=f"bulk_esp{i:02d}",
                primer_nombre=f"Especialista{i:02d}",
                segundo_nombre="",
                apellido_paterno="Listado",
                apellido_materno="Pruebas",
                password=None,
            )
            usuario.usuario_administrador = False
            usuario.estado = cls.activo
            usuario.codigo_empl = f"E{i:04d}"
            usuario.save()

        for i in range(25):
            usuario = Usuario.objects.create_user(
                email=f"bulk.adm{i:02d}@test.local",
                username=f"bulk_adm{i:02d}",
                primer_nombre=f"Admin{i:02d}",
                segundo_nombre="",
                apellido_paterno="Listado",
                apellido_materno="Pruebas",
                password=None,
            )
            usuario.usuario_administrador = True
            usuario.estado = cls.activo
            usuario.codigo_empl = f"A{i:04d}"
            usuario.save()

        padecimiento = Padecimiento.objects.create(name="Hernia de Disco")
        cls.historial_detalle = None
        for i in range(25):
            historial = Historial_paciente.objects.create(
                empleado=cls.specialist,
                paciente=cls.paciente_buscado,
                padecimiento=padecimiento,
                precision_value="90.00",
            )
            if cls.historial_detalle is None:
                cls.historial_detalle = historial

        Datos.objects.create(
            historial_paciente=cls.historial_detalle,
            pelvic_incidence=44.3,
            pelvic_tilt=10.5,
            lumbar_lordosis_angle=50.2,
            sacral_slope=33.8,
            pelvic_radius=124.1,
            degree_spondylolisthesis=2.4,
        )

    def test_patient_list_paginates_ten_per_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("paciente"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["object_list"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.count, 26)

        response = self.client.get(reverse("paciente"), {"page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["object_list"]), 10)

        response = self.client.get(reverse("paciente"), {"page": 3})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["object_list"]), 6)

    def test_patient_search_filters_by_name_and_dni(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("paciente"), {"q": "Buscado"})

        self.assertEqual(response.context["cantidad"], 1)
        self.assertContains(response, "Buscado")
        self.assertNotContains(response, "Paciente00")

        response = self.client.get(reverse("paciente"), {"q": "20000000"})

        self.assertEqual(response.context["cantidad"], 1)
        self.assertContains(response, "Buscado")

    def test_patient_search_keeps_inactive_toggle(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("paciente"), {"inactivos": "1", "q": "Inactivo"}
        )

        self.assertEqual(response.context["cantidad"], 1)
        self.assertContains(response, "Inactivo")
        self.assertContains(response, 'name="inactivos" value="1"')

    def test_pagination_preserves_search_query(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("paciente"), {"q": "Paciente", "page": 2}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "q=Paciente")

    def test_specialist_list_paginates_and_searches(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("especialista"))
        self.assertEqual(len(response.context["object_list"]), 10)

        response = self.client.get(reverse("especialista"), {"q": "bulk_esp24"})
        self.assertEqual(response.context["cantidad"], 1)
        self.assertContains(response, "bulk_esp24")

    def test_admin_list_searches(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("administrador"), {"q": "bulk_adm24"})

        self.assertEqual(response.context["cantidad"], 1)
        self.assertContains(response, "bulk_adm24")

    def test_history_list_paginates_and_searches(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("historial_d"))
        self.assertEqual(len(response.context["page_obj"].object_list), 10)

        response = self.client.get(reverse("historial_d"), {"q": "Paciente99"})
        self.assertEqual(response.context["cantidad"], 0)

        response = self.client.get(reverse("historial_d"), {"q": "Buscado"})
        self.assertEqual(response.context["cantidad"], 25)

    def test_dashboard_shows_real_specialist_count(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard"))

        expected = Usuario.objects.filter(
            usuario_administrador=False, estado__name="Activo"
        ).count()
        self.assertEqual(response.context["cantidad_especialista"], expected)
        self.assertContains(response, f'<strong class="stat__value">{expected}</strong>', html=True)

    def test_dashboard_recent_diagnoses_paginates_ten_per_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(len(response.context["historial_diagnosticos"]), 10)
        self.assertEqual(
            response.context["page_obj"].paginator.count, 25
        )
        self.assertContains(response, "Página 1 de 3")

    def test_specialist_detail_recent_diagnoses_paginates_ten_per_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("usuario_detalle", args=[self.specialist.id])
        )

        self.assertEqual(len(response.context["diagnosticos"]), 10)
        self.assertEqual(
            response.context["page_obj"].paginator.count, 25
        )
        self.assertContains(response, "Página 1 de 3")

        response = self.client.get(
            reverse("usuario_detalle", args=[self.specialist.id]),
            {"page": 3},
        )

        self.assertEqual(len(response.context["diagnosticos"]), 5)
        self.assertContains(response, "Página 3 de 3")

    def test_diagnosis_detail_parameters_paginate(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("diagnostico_detalle", args=[self.historial_detalle.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["parametros"]), 6)
        self.assertEqual(response.context["page_obj"].paginator.count, 6)
        self.assertContains(response, "Página 1 de 1")

    def test_patient_detail_paginates_diagnoses(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("paciente_detalle", args=[self.paciente_buscado.id])
        )
        self.assertEqual(len(response.context["historial"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.count, 25)

        response = self.client.get(
            reverse("paciente_detalle", args=[self.paciente_buscado.id]),
            {"page": 3},
        )
        self.assertEqual(len(response.context["historial"]), 5)

    def test_diagnosis_patient_step_paginates_patients(self):
        self.client.force_login(self.specialist)

        response = self.client.get(reverse("diagnostico"))
        self.assertEqual(len(response.context["pacientes"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.count, 26)

        response = self.client.get(reverse("diagnostico"), {"page": 2})
        self.assertEqual(len(response.context["pacientes"]), 10)

        response = self.client.get(reverse("diagnostico"), {"page": 3})
        self.assertEqual(len(response.context["pacientes"]), 6)

    def test_diagnosis_patient_step_searches_server_side(self):
        self.client.force_login(self.specialist)

        response = self.client.get(reverse("diagnostico"), {"q": "Buscado"})

        self.assertEqual(response.context["cantidad"], 1)
        self.assertEqual(response.context["q"], "Buscado")
        self.assertContains(response, "Buscado")
        self.assertNotContains(response, "Paciente00")
        self.assertContains(response, 'value="Buscado"')

    def test_dashboard_recent_diagnoses_second_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard"), {"page": 2})

        self.assertEqual(len(response.context["historial_diagnosticos"]), 10)
        self.assertContains(response, "Página 2 de 3")

    def test_pagination_is_visible_with_a_single_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("especialista"), {"q": "esp_listas"})

        self.assertEqual(response.context["page_obj"].paginator.num_pages, 1)
        self.assertContains(response, "Página 1 de 1")

    def test_pagination_is_visible_with_empty_results(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("especialista"), {"q": "sin_coincidencias"})

        self.assertEqual(response.context["page_obj"].paginator.count, 0)
        self.assertContains(response, "Página 1 de 1")
        self.assertContains(response, "0 registros")


class ProfileAndPasswordTests(TestCase):
    PASSWORD = "ClaveSegura123!"

    @classmethod
    def setUpTestData(cls):
        cls.activo = Estado.objects.create(name="Activo")
        cls.inactivo = Estado.objects.create(name="Inactivo")

        cls.admin = Usuario.objects.create_user(
            email="perfil.admin@test.local",
            username="perfil_admin",
            primer_nombre="Admin",
            segundo_nombre="",
            apellido_paterno="Perfil",
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        cls.admin.usuario_administrador = True
        cls.admin.estado = cls.activo
        cls.admin.codigo_empl = "ADM001"
        cls.admin.telefono = "911111111"
        cls.admin.dni = "11111111"
        cls.admin.save()

        cls.specialist = Usuario.objects.create_user(
            email="perfil.especialista@test.local",
            username="perfil_especialista",
            primer_nombre="Especialista",
            segundo_nombre="",
            apellido_paterno="Perfil",
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        cls.specialist.usuario_administrador = False
        cls.specialist.estado = cls.activo
        cls.specialist.codigo_empl = "ESP001"
        cls.specialist.telefono = "922222222"
        cls.specialist.dni = "22222222"
        cls.specialist.save()

    def datos_perfil(self, usuario, **overrides):
        datos = {
            "primer_nombre": usuario.primer_nombre,
            "segundo_nombre": usuario.segundo_nombre,
            "apellido_paterno": usuario.apellido_paterno,
            "apellido_materno": usuario.apellido_materno,
            "email": usuario.email,
            "telefono": usuario.telefono or "",
            "dni": usuario.dni or "",
        }
        datos.update(overrides)
        return datos

    def test_profile_requires_login(self):
        response = self.client.get(reverse("perfil"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('perfil')}",
            fetch_redirect_response=False,
        )

    def test_profile_shows_own_data(self):
        self.client.force_login(self.specialist)

        response = self.client.get(reverse("perfil"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.specialist.username)
        self.assertContains(response, self.specialist.email)
        self.assertContains(response, self.specialist.codigo_empl)
        self.assertContains(response, reverse("perfil_editar"))
        self.assertContains(response, reverse("password_change"))

    def test_profile_edit_updates_own_data(self):
        self.client.force_login(self.specialist)

        response = self.client.post(
            reverse("perfil_editar"),
            self.datos_perfil(
                self.specialist,
                primer_nombre="Nombre",
                apellido_paterno="Actualizado",
                email="perfil.nuevo@test.local",
                telefono="933333333",
                dni="33333333",
            ),
            follow=True,
        )

        self.assertRedirects(response, reverse("perfil"))
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.primer_nombre, "Nombre")
        self.assertEqual(self.specialist.apellido_paterno, "Actualizado")
        self.assertEqual(self.specialist.email, "perfil.nuevo@test.local")
        self.assertEqual(self.specialist.telefono, "933333333")
        self.assertContains(response, "Tus datos se actualizaron correctamente.")

    def test_profile_edit_ignores_sensitive_fields(self):
        self.client.force_login(self.specialist)

        datos = self.datos_perfil(self.specialist, primer_nombre="Cambio")
        datos.update(
            {
                "username": "otro_usuario",
                "codigo_empl": "HACK01",
                "usuario_administrador": "on",
                "estado": self.inactivo.id,
            }
        )

        response = self.client.post(reverse("perfil_editar"), datos, follow=True)

        self.assertRedirects(response, reverse("perfil"))
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.primer_nombre, "Cambio")
        self.assertEqual(self.specialist.username, "perfil_especialista")
        self.assertEqual(self.specialist.codigo_empl, "ESP001")
        self.assertFalse(self.specialist.usuario_administrador)
        self.assertEqual(self.specialist.estado, self.activo)

    def test_profile_edit_validates_unique_email(self):
        self.client.force_login(self.specialist)

        response = self.client.post(
            reverse("perfil_editar"),
            self.datos_perfil(self.specialist, email=self.admin.email),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.email, "perfil.especialista@test.local")

    def test_profile_edit_form_excludes_sensitive_fields(self):
        self.client.force_login(self.specialist)

        response = self.client.get(reverse("perfil_editar"))

        form = response.context["form"]
        for field in (
            "username",
            "codigo_empl",
            "usuario_administrador",
            "estado",
            "contrasena",
        ):
            self.assertNotIn(field, form.fields)

    def test_password_change_requires_login(self):
        response = self.client.get(reverse("password_change"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('password_change')}",
            fetch_redirect_response=False,
        )

    def test_password_change_uses_project_template(self):
        self.client.force_login(self.specialist)

        response = self.client.get(reverse("password_change"))

        self.assertTemplateUsed(response, "cuenta/password_change_form.html")
        self.assertContains(response, "Cambiar contraseña")
        self.assertNotContains(response, "Administración de Django")

    def test_global_nav_links_to_profile_and_password(self):
        self.client.force_login(self.specialist)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, reverse("perfil"))
        self.assertContains(response, reverse("password_change"))

    def test_password_change_success_keeps_session(self):
        self.client.force_login(self.specialist)

        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": self.PASSWORD,
                "new_password1": "NuevaClave987!",
                "new_password2": "NuevaClave987!",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("perfil"))
        self.specialist.refresh_from_db()
        self.assertTrue(self.specialist.check_password("NuevaClave987!"))
        self.assertEqual(
            self.client.get(reverse("perfil")).status_code,
            200,
        )
        self.assertContains(response, "Tu contraseña se actualizó correctamente.")

    def test_password_change_rejects_wrong_old_password(self):
        self.client.force_login(self.specialist)

        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "Incorrecta123!",
                "new_password1": "NuevaClave987!",
                "new_password2": "NuevaClave987!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("old_password", response.context["form"].errors)
        self.specialist.refresh_from_db()
        self.assertTrue(self.specialist.check_password(self.PASSWORD))

    def test_password_change_rejects_weak_password(self):
        self.client.force_login(self.specialist)

        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": self.PASSWORD,
                "new_password1": "12345678",
                "new_password2": "12345678",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("new_password2", response.context["form"].errors)
        self.specialist.refresh_from_db()
        self.assertTrue(self.specialist.check_password(self.PASSWORD))

    def test_password_change_rejects_mismatch(self):
        self.client.force_login(self.specialist)

        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": self.PASSWORD,
                "new_password1": "NuevaClave987!",
                "new_password2": "OtraClave987!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("new_password2", response.context["form"].errors)
        self.specialist.refresh_from_db()
        self.assertTrue(self.specialist.check_password(self.PASSWORD))

    def test_password_reset_routes_are_not_exposed(self):
        self.client.force_login(self.specialist)

        for ruta in (
            "/accounts/password_reset/",
            "/accounts/password_reset/done/",
            "/accounts/reset/MQ/set-password/",
            "/accounts/password_change/done/",
        ):
            self.assertEqual(self.client.get(ruta).status_code, 404)

    def test_registration_rejects_weak_password(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("registro_e"),
            {
                "primer_nombre": "Debil",
                "segundo_nombre": "",
                "apellido_paterno": "Clave",
                "apellido_materno": "Prueba",
                "codigo_empl": "DBL001",
                "estado": self.activo.id,
                "username": "usuario_debil",
                "email": "debil@test.local",
                "telefono": "944444444",
                "dni": "44444444",
                "contrasena": "12345678",
                "confirmar_contrasena": "12345678",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("contrasena", response.context["form"].errors)
        self.assertFalse(Usuario.objects.filter(username="usuario_debil").exists())


class AuditTests(TestCase):
    PASSWORD = "ClaveSegura123"

    @classmethod
    def setUpTestData(cls):
        cls.activo = Estado.objects.create(name="Activo")
        cls.inactivo = Estado.objects.create(name="Inactivo")

        cls.admin = cls.crear_usuario(
            "audit_admin", "audit.admin@test.local", admin=True, estado=cls.activo
        )
        cls.admin_objetivo = cls.crear_usuario(
            "audit_admin2", "audit.admin2@test.local", admin=True, estado=cls.activo
        )
        cls.specialist = cls.crear_usuario(
            "audit_esp", "audit.esp@test.local", admin=False, estado=cls.activo
        )
        cls.paciente = Paciente.objects.create(
            primer_nombre="Paciente",
            segundo_nombre="",
            apellido_paterno="Auditoria",
            apellido_materno="Pruebas",
            correo="audit.paciente@test.local",
            telefono="999999999",
            dni="55667788",
        )

    @classmethod
    def crear_usuario(cls, username, email, admin, estado):
        usuario = Usuario.objects.create_user(
            email=email,
            username=username,
            primer_nombre="Nombre",
            segundo_nombre="",
            apellido_paterno=username.title(),
            apellido_materno="Pruebas",
            password=cls.PASSWORD,
        )
        usuario.usuario_administrador = admin
        usuario.estado = estado
        usuario.codigo_empl = username.upper()[:10]
        usuario.telefono = "999999999"
        usuario.dni = "12345678"
        usuario.save()
        return usuario

    def datos_usuario(self, usuario, **cambios):
        datos = {
            "primer_nombre": usuario.primer_nombre,
            "segundo_nombre": usuario.segundo_nombre,
            "apellido_paterno": usuario.apellido_paterno,
            "apellido_materno": usuario.apellido_materno,
            "codigo_empl": usuario.codigo_empl,
            "username": usuario.username,
            "email": usuario.email,
            "telefono": usuario.telefono or "",
            "dni": usuario.dni or "",
        }
        datos.update(cambios)
        return datos

    def datos_paciente(self, paciente, **cambios):
        datos = {
            "primer_nombre": paciente.primer_nombre,
            "segundo_nombre": paciente.segundo_nombre,
            "apellido_paterno": paciente.apellido_paterno,
            "apellido_materno": paciente.apellido_materno,
            "correo": paciente.correo,
            "telefono": paciente.telefono,
            "dni": paciente.dni,
        }
        datos.update(cambios)
        return datos

    def test_create_specialist_records_audit(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("registro_e"),
            {
                "primer_nombre": "Nuevo",
                "segundo_nombre": "",
                "apellido_paterno": "Auditado",
                "apellido_materno": "Pruebas",
                "codigo_empl": "AUD001",
                "estado": self.activo.id,
                "username": "audit_nuevo",
                "email": "audit.nuevo@test.local",
                "telefono": "988888888",
                "dni": "66778899",
                "contrasena": "NuevaClave987!",
                "confirmar_contrasena": "NuevaClave987!",
            },
        )

        self.assertEqual(response.status_code, 302)
        creado = Usuario.objects.get(username="audit_nuevo")
        registro = Crud_empleado.objects.get()
        self.assertEqual(registro.editor, self.admin)
        self.assertEqual(registro.afectado, creado)
        self.assertEqual(registro.accion, "Crear")

    def test_create_admin_records_audit(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("registro_a"),
            {
                "primer_nombre": "Nuevo",
                "segundo_nombre": "",
                "apellido_paterno": "Admin",
                "apellido_materno": "Auditado",
                "codigo_empl": "AUD002",
                "estado": self.activo.id,
                "username": "audit_admin_nuevo",
                "email": "audit.admin.nuevo@test.local",
                "telefono": "977777777",
                "dni": "77889900",
                "contrasena": "NuevaClave987!",
                "confirmar_contrasena": "NuevaClave987!",
            },
        )

        self.assertEqual(response.status_code, 302)
        creado = Usuario.objects.get(username="audit_admin_nuevo")
        registro = Crud_empleado.objects.get()
        self.assertEqual(registro.editor, self.admin)
        self.assertEqual(registro.afectado, creado)
        self.assertEqual(registro.accion, "Crear")

    def test_edit_user_records_audit(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("usuario_editar", args=[self.specialist.id]),
            self.datos_usuario(self.specialist, primer_nombre="Editado"),
        )

        self.assertEqual(response.status_code, 302)
        registro = Crud_empleado.objects.get()
        self.assertEqual(registro.editor, self.admin)
        self.assertEqual(registro.afectado, self.specialist)
        self.assertEqual(registro.accion, "Editar")

    def test_deactivate_and_reactivate_specialist_record_audit(self):
        self.client.force_login(self.admin)

        self.client.post(reverse("desactivar_usuario", args=[self.specialist.id]))
        self.client.post(reverse("reactivar_usuario", args=[self.specialist.id]))

        acciones = list(
            Crud_empleado.objects.order_by("id").values_list("accion", flat=True)
        )
        self.assertEqual(acciones, ["Desactivar", "Reactivar"])
        self.assertEqual(Crud_empleado.objects.first().editor, self.admin)

    def test_deactivate_admin_records_audit(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("desactivar_admin", args=[self.admin_objetivo.id])
        )

        self.assertRedirects(response, reverse("administrador"))
        registro = Crud_empleado.objects.get()
        self.assertEqual(registro.editor, self.admin)
        self.assertEqual(registro.afectado, self.admin_objetivo)
        self.assertEqual(registro.accion, "Desactivar")

    def test_blocked_last_admin_deactivation_is_not_recorded(self):
        self.admin_objetivo.estado = self.inactivo
        self.admin_objetivo.save()
        self.client.force_login(self.admin)

        self.client.post(reverse("desactivar_admin", args=[self.admin.id]))

        self.assertFalse(
            Crud_empleado.objects.filter(accion="Desactivar").exists()
        )

    def test_patient_actions_record_audit(self):
        self.client.force_login(self.specialist)

        self.client.post(
            reverse("registro_p"),
            {
                "primer_nombre": "Paciente",
                "segundo_nombre": "",
                "apellido_paterno": "Nuevo",
                "apellido_materno": "Auditoria",
                "correo": "paciente.nuevo@test.local",
                "telefono": "966666666",
                "dni": "88990011",
            },
        )
        creado = Paciente.objects.get(dni="88990011")

        self.client.post(
            reverse("paciente_editar", args=[creado.id]),
            self.datos_paciente(creado, primer_nombre="Paciente editado"),
        )
        self.client.post(reverse("desactivar_paciente", args=[creado.id]))

        acciones = list(
            Crud_paciente.objects.order_by("id").values_list("accion", flat=True)
        )
        self.assertEqual(acciones, ["Crear", "Editar", "Desactivar"])
        self.assertTrue(
            Crud_paciente.objects.filter(
                editor=self.specialist, afectado=creado
            ).exists()
        )

    def test_profile_edit_records_audit(self):
        self.client.force_login(self.specialist)

        self.client.post(
            reverse("perfil_editar"),
            {
                "primer_nombre": "Perfil",
                "segundo_nombre": "",
                "apellido_paterno": "Editado",
                "apellido_materno": "Pruebas",
                "email": self.specialist.email,
                "telefono": self.specialist.telefono,
                "dni": self.specialist.dni,
            },
        )

        registro = Crud_empleado.objects.get()
        self.assertEqual(registro.editor, self.specialist)
        self.assertEqual(registro.afectado, self.specialist)
        self.assertEqual(registro.accion, "Editar perfil")

    def test_password_change_records_audit(self):
        self.client.force_login(self.specialist)

        self.client.post(
            reverse("password_change"),
            {
                "old_password": self.PASSWORD,
                "new_password1": "NuevaClave987!",
                "new_password2": "NuevaClave987!",
            },
        )

        registro = Crud_empleado.objects.get()
        self.assertEqual(registro.editor, self.specialist)
        self.assertEqual(registro.afectado, self.specialist)
        self.assertEqual(registro.accion, "Cambiar contraseña")

    def test_audit_page_is_admin_only(self):
        self.client.force_login(self.specialist)
        self.assertEqual(self.client.get(reverse("auditoria")).status_code, 403)

        self.client.logout()
        self.assertRedirects(
            self.client.get(reverse("auditoria")),
            f"{reverse('login')}?next={reverse('auditoria')}",
            fetch_redirect_response=False,
        )

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("auditoria")).status_code, 200)

    def test_audit_page_shows_records_and_tabs(self):
        Crud_empleado.objects.create(
            editor=self.admin,
            afectado=self.specialist,
            accion="Editar",
        )
        Crud_paciente.objects.create(
            editor=self.specialist,
            afectado=self.paciente,
            accion="Crear",
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("auditoria"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tipo"], "empleados")
        self.assertEqual(response.context["cantidad"], 1)
        self.assertContains(response, self.admin.username)
        self.assertContains(response, "Audit_Esp")
        self.assertContains(response, "Editar")
        self.assertContains(response, "?tipo=pacientes")
        self.assertNotContains(response, "Paciente Auditoria")

    def test_audit_page_filters_patients_and_search(self):
        Crud_empleado.objects.create(
            editor=self.admin,
            afectado=self.specialist,
            accion="Editar",
        )
        Crud_paciente.objects.create(
            editor=self.specialist,
            afectado=self.paciente,
            accion="Crear",
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("auditoria"), {"tipo": "pacientes"})
        self.assertEqual(response.context["tipo"], "pacientes")
        self.assertEqual(response.context["cantidad"], 1)
        self.assertContains(response, "Auditoria")
        self.assertContains(response, "Crear")

        response = self.client.get(
            reverse("auditoria"), {"tipo": "pacientes", "q": "55667788"}
        )
        self.assertEqual(response.context["cantidad"], 1)

        response = self.client.get(
            reverse("auditoria"), {"tipo": "empleados", "q": "Reactivar"}
        )
        self.assertEqual(response.context["cantidad"], 0)

    def test_audit_page_paginates(self):
        for i in range(25):
            Crud_empleado.objects.create(
                editor=self.admin,
                afectado=self.specialist,
                accion=f"Editar {i:02d}",
            )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("auditoria"))
        self.assertEqual(len(response.context["object_list"]), 10)

        response = self.client.get(reverse("auditoria"), {"page": 3})
        self.assertEqual(len(response.context["object_list"]), 5)

    def test_audit_nav_link_is_visible_only_to_admins(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, reverse("auditoria"))

        self.client.force_login(self.specialist)
        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, reverse("auditoria"))


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class ErrorPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.activo = Estado.objects.create(name="Activo")
        cls.specialist = Usuario.objects.create_user(
            email="errores.especialista@test.local",
            username="errores_especialista",
            primer_nombre="Especialista",
            segundo_nombre="",
            apellido_paterno="Errores",
            apellido_materno="Pruebas",
            password="ClaveSegura123!",
        )
        cls.specialist.usuario_administrador = False
        cls.specialist.estado = cls.activo
        cls.specialist.save()

    def test_404_uses_custom_template(self):
        response = self.client.get("/esta-ruta-no-existe/")

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "Página no encontrada", status_code=404)
        self.assertContains(response, reverse("login"), status_code=404)

    def test_403_uses_custom_template(self):
        self.client.force_login(self.specialist)

        response = self.client.get(reverse("auditoria"))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")
        self.assertContains(response, "Acceso denegado", status_code=403)

    def test_500_and_csrf_error_templates_render_without_context(self):
        html = render_to_string("500.html")

        self.assertIn("Error interno del servidor", html)
        self.assertIn("Volver al inicio", html)

        html = render_to_string("403_csrf.html")
        self.assertIn("Sesión expirada", html)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
    def test_400_handler_returns_custom_template(self):
        from tasks.errors import bad_request
        request = RequestFactory().get('/bad/')
        response = bad_request(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Solicitud inválida', response.content.decode('utf-8'))

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
    def test_403_handler_returns_custom_template(self):
        from tasks.errors import permission_denied
        request = RequestFactory().get('/forbidden/')
        response = permission_denied(request)
        self.assertEqual(response.status_code, 403)
        self.assertIn('Acceso denegado', response.content.decode('utf-8'))

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
    def test_404_handler_returns_custom_template(self):
        from tasks.errors import page_not_found
        request = RequestFactory().get('/missing/')
        response = page_not_found(request)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Página no encontrada', response.content.decode('utf-8'))

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
    def test_500_handler_returns_custom_template(self):
        from tasks.errors import server_error
        request = RequestFactory().get('/error/')
        response = server_error(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn('Error interno del servidor', response.content.decode('utf-8'))

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
    def test_csrf_failure_returns_custom_template(self):
        client = self.client_class(enforce_csrf_checks=True)
        response = client.post(reverse('login'), {'username': 'x', 'password': 'y'})
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403_csrf.html')
        self.assertContains(response, 'Sesión expirada', status_code=403)

    def test_home_redirects_to_dashboard(self):
        response = self.client.get(reverse("home"))

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )

