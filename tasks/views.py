from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import (
    Paciente,
    Historial_paciente,
    Datos,
    Padecimiento,
    Usuario,
    Estado,
    Crud_empleado,
    Crud_paciente,
)
from .forms import (
    ValidarPrediccion,
    CrearPaciente,
    CrearUsuario,
    EditarUsuarioForm,
    PerfilForm,
)
from django.contrib.auth.views import PasswordChangeView
from .permissions import (
    AdminRequiredMixin,
    SpecialistRequiredMixin,
    specialist_required,
)
from .audit import (
    ACCION_CONTRASENA,
    ACCION_CREAR,
    ACCION_DESACTIVAR,
    ACCION_EDITAR,
    ACCION_PERFIL,
    ACCION_REACTIVAR,
    registrar_accion_empleado,
    registrar_accion_paciente,
)
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_GET, require_POST
import joblib
import pandas as pd
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image
from django.conf import settings
from decimal import Decimal
from django.db.models import Avg, Q
from django.core.paginator import Paginator
from django.views.generic import CreateView,UpdateView,ListView,DetailView,View
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.db import transaction

# Create your views here.
def _querystring_sin_pagina(request):
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


def _texto_busqueda(request):
    return (request.GET.get('q') or '').strip()


@login_required
def dashboard(request):
    cantidad = Historial_paciente.objects.count()
    cantidad_paciente = Paciente.objects.filter(activo=True).count()
    cantidad_especialista = Usuario.objects.filter(
        usuario_administrador=False, estado__name="Activo"
    ).count()
    hernia = Historial_paciente.objects.filter(padecimiento=1).count()
    spon = Historial_paciente.objects.filter(padecimiento=2).count()
    normal = Historial_paciente.objects.filter(padecimiento=3).count()
    historial = Historial_paciente.objects.select_related(
        'paciente', 'padecimiento', 'empleado'
    ).order_by('-fecha')
    paginator = Paginator(historial, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    nomal_precision = Historial_paciente.objects.filter(padecimiento=3).aggregate(Avg('precision_value'))
    hernia_precision = Historial_paciente.objects.filter(padecimiento=1).aggregate(Avg('precision_value'))
    spon_precision = Historial_paciente.objects.filter(padecimiento=2).aggregate(Avg('precision_value'))
    
    return render(request, "dashboard/dashboard.html",{
        'diagnosticos_cantidad':cantidad,
        'cantidad_paciente':cantidad_paciente,
        'cantidad_especialista':cantidad_especialista,
        'normal_count': normal,
        'hernia_count':hernia,
        'spon_count':spon,
        'historial_diagnosticos':page_obj,
        'page_obj':page_obj,
        'querystring':_querystring_sin_pagina(request),
        'precision_n':nomal_precision,
        'precision_hernia':hernia_precision,
        'precision_spon':spon_precision
    })

@login_required
def moduloDiagnostico(request):
    return render(request, "dashboard/diagnostico.html")

@specialist_required
def moduloDiagnosticoEtp1(request):
    q = _texto_busqueda(request)
    pacientes = Paciente.objects.filter(activo=True)
    if q:
        pacientes = pacientes.filter(
            Q(primer_nombre__icontains=q)
            | Q(segundo_nombre__icontains=q)
            | Q(apellido_paterno__icontains=q)
            | Q(apellido_materno__icontains=q)
            | Q(dni__icontains=q)
        )
    pacientes = pacientes.order_by("apellido_paterno", "primer_nombre", "id")
    paginator = Paginator(pacientes, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request,"dashboard/modulos/etapa1.html",{
        'pacientes': page_obj,
        'page_obj': page_obj,
        'cantidad': paginator.count,
        'q': q,
        'querystring': _querystring_sin_pagina(request),
    })
    
@specialist_required
def moduloDiagnosticoEtp2(request,id):
    paciente = get_object_or_404(Paciente,id=id,activo=True)
    return render(request,"dashboard/modulos/etapa2.html",{
        'paciente':paciente
    })
    
@specialist_required
def moduloDiagnosticoEtp3(request,id):
    paciente = get_object_or_404(Paciente,id=id,activo=True)
    return render(request,"dashboard/modulos/etapa3.html",{
        'paciente':paciente,
        'form': ValidarPrediccion()
    })

# Genera el informe del diagnostico en PDF
def _construir_informe_pdf(historial_paciente):
    paciente = historial_paciente.paciente
    datos = historial_paciente.datos_set.first()

    if datos is None:
        return HttpResponse(
            "No se encontraron parámetros para este diagnóstico.", status=404
        )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="diagnostico_{historial_paciente.id}.pdf"'
    )

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='subTitle',
        fontSize=14,
        leading=16,
        spaceAfter=12,
        alignment=1,  # Centrado
        textColor=colors.black
    ))

    title = Paragraph(
        f"<b>Informe Diagnóstico - {paciente.primer_nombre} {paciente.apellido_paterno}</b>",
        styles['Title'],
    )
    elements.append(title)

    empleado = historial_paciente.empleado
    subtitle = Paragraph(
        f"<b>Realizado por el Dr. {empleado.primer_nombre} {empleado.apellido_paterno}</b>",
        styles['subTitle'],
    )
    elements.append(subtitle)

    image_path = os.path.join(
        settings.BASE_DIR, 'tasks', 'static', 'img',
        'logo-hospital-transparente.png',
    )
    logo = Image(image_path, width=2 * inch, height=2 * inch)
    elements.append(logo)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Información del paciente y del diagnóstico
    info_paciente = [
        ["Campo", "Valor"],
        ["Nombre completo", f"{paciente.primer_nombre} {paciente.segundo_nombre or ''} {paciente.apellido_paterno} {paciente.apellido_materno}"],
        ["Documento (DNI)", paciente.dni or "No registrado"],
        ["Correo", paciente.correo or "No registrado"],
        ["Fecha del diagnóstico", historial_paciente.fecha.strftime("%d/%m/%Y %H:%M")],
        ["Especialista", f"{empleado.primer_nombre} {empleado.apellido_paterno} ({empleado.codigo_empl})"],
    ]

    table_paciente = Table(info_paciente, hAlign="LEFT", colWidths=[3 * inch, 3 * inch])
    table_paciente.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table_paciente)

    # Información del diagnóstico
    datos_historial = [
        ["Parámetro", "Valor"],
        ["Incidencia pélvica", f"{datos.pelvic_incidence:.2f}°"],
        ["Inclinación pélvica", f"{datos.pelvic_tilt:.2f}°"],
        ["Ángulo de lordosis lumbar", f"{datos.lumbar_lordosis_angle:.2f}°"],
        ["Pendiente sacra", f"{datos.sacral_slope:.2f}°"],
        ["Radio pélvico", f"{datos.pelvic_radius:.2f} mm"],
        ["Grado de espondilolistesis", f"{datos.degree_spondylolisthesis:.2f}%"],
        ["Nivel de confianza", f"{historial_paciente.precision_value}%"],
    ]

    table_historial = Table(datos_historial, hAlign="LEFT", colWidths=[3 * inch, 3 * inch])
    table_historial.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    elements.append(table_historial)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    precision = Paragraph(
        f"<b>Diagnóstico obtenido: {historial_paciente.padecimiento}</b>",
        styles['subTitle'],
    )
    elements.append(precision)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Leyenda
    leyenda = Paragraph(
        "El Hospital Regional Eleazar Guzmán Barrón es una institución dedicada a la atención integral de salud en la región, "
        "brindando servicios médicos de calidad con un enfoque en la mejora continua. Este informe tiene como propósito "
        "evaluar los datos del paciente para identificar áreas críticas y garantizar una atención efectiva.",
        styles['Normal']
    )
    elements.append(leyenda)

    doc.build(elements)

    return response


@login_required
def moduloInformeDiagnostico(request, paciente_id):
    """Informe del último diagnóstico del paciente (compatibilidad)."""
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historial_paciente = Historial_paciente.objects.filter(
        paciente=paciente
    ).order_by('-fecha').first()

    if not historial_paciente:
        return HttpResponse("No se encontró historial para el paciente.", status=404)

    return _construir_informe_pdf(historial_paciente)


@login_required
def informe_diagnostico_pdf(request, pk):
    historial_paciente = get_object_or_404(
        Historial_paciente.objects.select_related(
            'paciente', 'empleado', 'padecimiento'
        ),
        pk=pk,
    )
    return _construir_informe_pdf(historial_paciente)

# Realiza la predicción de la patología
@specialist_required
@require_POST
def realizar_prediccion(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id, activo=True)
    form = ValidarPrediccion(request.POST)

    if not form.is_valid():
        return render(request, 'dashboard/modulos/etapa3.html', {
            'paciente': paciente,
            'form': form,
        })

    # Obtener la ruta base de la aplicación 'tasks'
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

    # Construir las rutas absolutas para los archivos
    xgb_model_path = os.path.join(APP_DIR, 'xgb_model.pkl')
    scaler_path = os.path.join(APP_DIR, 'scalerXG.pkl')
    label_encoder_path = os.path.join(APP_DIR, 'label_encoderXG.pkl')

    # Cargar el modelo de XGBoost, el escalador y el codificador de etiquetas
    try:
        xgb_model = joblib.load(xgb_model_path)
        scaler = joblib.load(scaler_path)
        label_encoder = joblib.load(label_encoder_path)
    except FileNotFoundError as e:
        return render(request, 'dashboard/modulos/etapaf.html', {'error': f'Archivo no encontrado: {e}'})

    feature_names = [
        'pelvic_incidence',
        'pelvic_tilt',
        'lumbar_lordosis_angle',
        'sacral_slope',
        'pelvic_radius',
        'degree_spondylolisthesis',
    ]
    example_features = [form.cleaned_data[name] for name in feature_names]
    nuevos_datos = pd.DataFrame([example_features], columns=feature_names)

    # Estandarizar los nuevos datos usando el mismo escalador que durante el entrenamiento
    nuevos_datos_scaled = scaler.transform(nuevos_datos)

    # Realizar predicciones
    predicciones_xgb = xgb_model.predict(nuevos_datos_scaled)
    predicciones_proba_xgb = xgb_model.predict_proba(nuevos_datos_scaled)

    # Decodificar la predicción a la clase original
    prediccion_decodificada_xgb = label_encoder.inverse_transform(predicciones_xgb)[0]
    confidence_xgb = max(predicciones_proba_xgb[0]) * 100  # Porcentaje de confianza

    if not prediccion_decodificada_xgb:
        return render(request, 'dashboard/modulos/etapaf.html', {'error': 'Error en la predicción'})

    if prediccion_decodificada_xgb == "Hernia":
        padecimiento = get_object_or_404(Padecimiento, id=1)
    elif prediccion_decodificada_xgb == "Spondylolisthesis":
        padecimiento = get_object_or_404(Padecimiento, id=2)
    else:
        padecimiento = get_object_or_404(Padecimiento, id=3)

    with transaction.atomic():
        historial_paciente = Historial_paciente.objects.create(
            empleado=request.user,
            paciente=paciente,
            padecimiento=padecimiento,
            precision_value=Decimal(str(confidence_xgb))
        )

        Datos.objects.create(
            historial_paciente=historial_paciente,
            pelvic_incidence=example_features[0],
            pelvic_tilt=example_features[1],
            lumbar_lordosis_angle=example_features[2],
            sacral_slope=example_features[3],
            pelvic_radius=example_features[4],
            degree_spondylolisthesis=example_features[5]
        )

    contexto = {
        'historial': historial_paciente,
        'datos': historial_paciente.datos_set.all(),
        'prediccion': prediccion_decodificada_xgb,
        'confidence': confidence_xgb,
        'paciente': paciente,
    }

    return render(request, 'dashboard/modulos/etapaf.html', {
        'contexto': contexto
    })

def _buscar_historial(queryset, q):
    if not q:
        return queryset
    return queryset.filter(
        Q(paciente__primer_nombre__icontains=q)
        | Q(paciente__segundo_nombre__icontains=q)
        | Q(paciente__apellido_paterno__icontains=q)
        | Q(paciente__apellido_materno__icontains=q)
        | Q(paciente__dni__icontains=q)
        | Q(padecimiento__name__icontains=q)
        | Q(empleado__primer_nombre__icontains=q)
        | Q(empleado__apellido_paterno__icontains=q)
    )


@login_required
def moduloHistorialD(request):
    titulo = "Historial de diagnósticos"
    q = _texto_busqueda(request)
    historial = Historial_paciente.objects.select_related(
        'paciente', 'padecimiento', 'empleado'
    ).order_by('-fecha')
    historial = _buscar_historial(historial, q)

    paginator = Paginator(historial, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, "crud/historiald.html",{
        'titulo':titulo,
        'historial':page_obj,
        'page_obj':page_obj,
        'cantidad':paginator.count,
        'q':q,
        'querystring':_querystring_sin_pagina(request),
    })
    
@specialist_required
def moduloHistorialInteracciones(request):
    titulo = "Mi Historial de diagnósticos"
    q = _texto_busqueda(request)
    usuario_actual = request.user
    historial = Historial_paciente.objects.select_related(
        'paciente', 'padecimiento', 'empleado'
    ).filter(empleado=usuario_actual).order_by('-fecha')
    historial = _buscar_historial(historial, q)

    paginator = Paginator(historial, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, "crud/mihistorial.html",{
        'titulo':titulo,
        'historial':page_obj,
        'page_obj':page_obj,
        'cantidad':paginator.count,
        'q':q,
        'querystring':_querystring_sin_pagina(request),
    })

@method_decorator(login_required, name='dispatch')
class ListadoPaciente(ListView):
    model = Paciente
    template_name= "crud/pacientes.html"
    paginate_by = 10

    def mostrar_inactivos(self):
        return self.request.GET.get('inactivos') == '1'
    
    def get_queryset(self):
        queryset = self.model.objects.filter(
            activo=not self.mostrar_inactivos()
        ).order_by("apellido_paterno", "primer_nombre", "id")
        q = _texto_busqueda(self.request)
        if q:
            queryset = queryset.filter(
                Q(primer_nombre__icontains=q)
                | Q(segundo_nombre__icontains=q)
                | Q(apellido_paterno__icontains=q)
                | Q(apellido_materno__icontains=q)
                | Q(dni__icontains=q)
                | Q(correo__icontains=q)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        # Primero, obtiene el contexto original de la vista
        context = super().get_context_data(**kwargs)

        # Agregar datos adicionales al contexto
        context['titulo'] = "Paciente"  # Agregar título
        context['cantidad'] = self.get_queryset().count()
        context['cantidad_total'] = self.model.objects.filter(
            activo=not self.mostrar_inactivos()
        ).count()
        context['cantidad_activos'] = Paciente.objects.filter(activo=True).count()
        context['cantidad_inactivos'] = Paciente.objects.filter(activo=False).count()
        context['mostrar_inactivos'] = self.mostrar_inactivos()
        context['q'] = _texto_busqueda(self.request)
        context['querystring'] = _querystring_sin_pagina(self.request)
        
        return context


class DetallePaciente(LoginRequiredMixin, DetailView):
    model = Paciente
    template_name = 'crud/paciente_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        historial = Historial_paciente.objects.filter(
            paciente=self.object
        ).select_related('empleado', 'padecimiento').order_by('-fecha')
        paginator = Paginator(historial, 10)
        page_obj = paginator.get_page(self.request.GET.get('page'))
        context['historial'] = page_obj
        context['page_obj'] = page_obj
        context['cantidad'] = paginator.count
        context['querystring'] = _querystring_sin_pagina(self.request)
        return context


class EditarPaciente(SpecialistRequiredMixin, UpdateView):
    model = Paciente
    form_class = CrearPaciente
    template_name = 'crud/registrocrud/r_paciente.html'

    def get_queryset(self):
        return self.model.objects.filter(activo=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['texto_boton'] = "Guardar cambios"
        context['tipo_usuario'] = "paciente"
        context['accion'] = "Editar"
        context['url_cancelar'] = reverse_lazy(
            'paciente_detalle', args=[self.object.pk]
        )
        return context

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            registrar_accion_paciente(
                self.request.user, self.object, ACCION_EDITAR
            )
        return response

    def get_success_url(self):
        return reverse_lazy('paciente_detalle', args=[self.object.pk])


class RegistrarPaciente(SpecialistRequiredMixin, CreateView):
    paciente = Paciente
    form_class = CrearPaciente
    template_name = 'crud/registrocrud/r_paciente.html'
    success_url = reverse_lazy('paciente')
    
    def get_context_data(self, **kwargs):
        # Primero, obtiene el contexto original de la vista
        context = super().get_context_data(**kwargs)
        context['texto_boton'] = "Enviar" 
        context['tipo_usuario']="paciente"
        return context

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            registrar_accion_paciente(
                self.request.user, self.object, ACCION_CREAR
            )
        return response
    
class DesactivarPaciente(SpecialistRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        paciente_id = kwargs.get('pk')
        paciente = get_object_or_404(Paciente, pk=paciente_id, activo=True)
        
        # Cambiar el estado de 'activo' a False
        with transaction.atomic():
            paciente.activo = False
            paciente.save()
            registrar_accion_paciente(request.user, paciente, ACCION_DESACTIVAR)

        # Redirigir a la lista de pacientes u otra p�gina
        return redirect(reverse_lazy('paciente'))

# METODOS PARA LOS ESPECIALISTAS

def _filtro_usuario_auditoria(prefijo, q):
    return (
        Q(**{f"{prefijo}primer_nombre__icontains": q})
        | Q(**{f"{prefijo}segundo_nombre__icontains": q})
        | Q(**{f"{prefijo}apellido_paterno__icontains": q})
        | Q(**{f"{prefijo}apellido_materno__icontains": q})
        | Q(**{f"{prefijo}dni__icontains": q})
        | Q(**{f"{prefijo}username__icontains": q})
        | Q(**{f"{prefijo}codigo_empl__icontains": q})
        | Q(**{f"{prefijo}email__icontains": q})
    )


def _buscar_auditoria_empleados(queryset, q):
    if not q:
        return queryset
    return queryset.filter(
        Q(accion__icontains=q)
        | _filtro_usuario_auditoria("editor__", q)
        | _filtro_usuario_auditoria("afectado__", q)
    )


def _buscar_auditoria_pacientes(queryset, q):
    if not q:
        return queryset
    return queryset.filter(
        Q(accion__icontains=q)
        | _filtro_usuario_auditoria("editor__", q)
        | Q(afectado__primer_nombre__icontains=q)
        | Q(afectado__segundo_nombre__icontains=q)
        | Q(afectado__apellido_paterno__icontains=q)
        | Q(afectado__apellido_materno__icontains=q)
        | Q(afectado__dni__icontains=q)
        | Q(afectado__correo__icontains=q)
    )


def _buscar_usuarios(queryset, q):
    if not q:
        return queryset
    return queryset.filter(
        Q(primer_nombre__icontains=q)
        | Q(segundo_nombre__icontains=q)
        | Q(apellido_paterno__icontains=q)
        | Q(apellido_materno__icontains=q)
        | Q(dni__icontains=q)
        | Q(username__icontains=q)
        | Q(codigo_empl__icontains=q)
        | Q(email__icontains=q)
    )


class ListadoDoctor(AdminRequiredMixin, ListView):
    model = Usuario
    template_name = "crud/especialista.html"
    paginate_by = 10
    
    def get_queryset(self):
        queryset = self.model.objects.filter(
            usuario_administrador=False
        ).order_by("apellido_paterno", "primer_nombre")
        return _buscar_usuarios(queryset, _texto_busqueda(self.request))
    
    def get_context_data(self, **kwargs):
        # Obtiene el contexto original de la vista
        context = super().get_context_data(**kwargs)

        # Agregar datos adicionales al contexto
        context['titulo'] = "Especialista"  # Título de la vista
        context['cantidad'] = self.get_queryset().count()
        base = self.model.objects.filter(usuario_administrador=False)
        context['cantidad_total'] = base.count()
        context['cantidad_activos'] = base.filter(
            estado__name="Activo"
        ).count()
        context['q'] = _texto_busqueda(self.request)
        context['querystring'] = _querystring_sin_pagina(self.request)
        
        return context


class RegistrarUsuario(AdminRequiredMixin, CreateView):
    paciente = Usuario
    form_class = CrearUsuario
    template_name = 'crud/registrocrud/r_paciente.html'
    success_url = reverse_lazy('especialista')
    
    def get_context_data(self, **kwargs):
        # Primero, obtiene el contexto original de la vista
        context = super().get_context_data(**kwargs)
        context['texto_boton'] = "Enviar" 
        context['tipo_usuario']="Doctor"
        return context

    def form_valid(self, form):
        form.instance.usuario_administrador = False
        with transaction.atomic():
            response = super().form_valid(form)
            registrar_accion_empleado(
                self.request.user, self.object, ACCION_CREAR
            )
        return response
    
    
class DesactivarUsuario(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        usuario_id = kwargs.get('pk')
        usuario = get_object_or_404(
            Usuario, pk=usuario_id, usuario_administrador=False
        )
        
        with transaction.atomic():
            if usuario.is_active:
                usuario.estado = Estado.objects.get(name="Inactivo")
                usuario.save()
                registrar_accion_empleado(
                    request.user, usuario, ACCION_DESACTIVAR
                )

        return redirect(reverse_lazy('especialista'))


class ReactivarUsuario(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        usuario_id = kwargs.get('pk')
        usuario = get_object_or_404(
            Usuario, pk=usuario_id, usuario_administrador=False
        )

        with transaction.atomic():
            if not usuario.is_active:
                usuario.estado = Estado.objects.get(name="Activo")
                usuario.save()
                registrar_accion_empleado(
                    request.user, usuario, ACCION_REACTIVAR
                )

        return redirect(reverse_lazy('especialista'))
    
    
# METODOS PARA LOS ADMINS

class ListadoAdmin(AdminRequiredMixin, ListView):
    model = Usuario
    template_name = "crud/admin.html"
    paginate_by = 10
    
    def get_queryset(self):
        queryset = self.model.objects.filter(
            usuario_administrador=True
        ).order_by("apellido_paterno", "primer_nombre")
        return _buscar_usuarios(queryset, _texto_busqueda(self.request))
    
    def get_context_data(self, **kwargs):
        # Obtiene el contexto original de la vista
        context = super().get_context_data(**kwargs)

        # Agregar datos adicionales al contexto
        context['titulo'] = "Administrador"  # Título de la vista
        context['cantidad'] = self.get_queryset().count()
        base = self.model.objects.filter(usuario_administrador=True)
        context['cantidad_total'] = base.count()
        context['cantidad_activos'] = base.filter(
            estado__name="Activo"
        ).count()
        context['q'] = _texto_busqueda(self.request)
        context['querystring'] = _querystring_sin_pagina(self.request)
        
        return context


class RegistrarUsuarioAdmin(AdminRequiredMixin, CreateView):
    paciente = Usuario
    form_class = CrearUsuario
    template_name = 'crud/registrocrud/r_paciente.html'
    success_url = reverse_lazy('administrador')
    
    def get_context_data(self, **kwargs):
        # Primero, obtiene el contexto original de la vista
        context = super().get_context_data(**kwargs)
        context['texto_boton'] = "Enviar" 
        context['tipo_usuario']="Administrador"
        return context

    def form_valid(self, form):
        form.instance.usuario_administrador = True
        with transaction.atomic():
            response = super().form_valid(form)
            registrar_accion_empleado(
                self.request.user, self.object, ACCION_CREAR
            )
        return response
    
    
class DesactivarUsuarioAdmin(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        usuario_id = kwargs.get('pk')
        usuario = get_object_or_404(
            Usuario, pk=usuario_id, usuario_administrador=True
        )

        if usuario.is_active:
            administradores_activos = Usuario.objects.filter(
                usuario_administrador=True, estado__name="Activo"
            ).count()
            if administradores_activos <= 1:
                messages.error(
                    request,
                    "No se puede desactivar al último administrador activo.",
                )
                return redirect(reverse_lazy('administrador'))

        with transaction.atomic():
            if usuario.is_active:
                usuario.estado = Estado.objects.get(name="Inactivo")
                usuario.save()
                registrar_accion_empleado(
                    request.user, usuario, ACCION_DESACTIVAR
                )

        return redirect(reverse_lazy('administrador'))


class ReactivarUsuarioAdmin(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        usuario_id = kwargs.get('pk')
        usuario = get_object_or_404(
            Usuario, pk=usuario_id, usuario_administrador=True
        )

        with transaction.atomic():
            if not usuario.is_active:
                usuario.estado = Estado.objects.get(name="Activo")
                usuario.save()
                registrar_accion_empleado(
                    request.user, usuario, ACCION_REACTIVAR
                )

        return redirect(reverse_lazy('administrador'))


# AUDITORIA DE CAMBIOS

class ListadoAuditoria(AdminRequiredMixin, ListView):
    template_name = 'crud/auditoria.html'
    paginate_by = 10

    def get_tipo(self):
        return (
            'pacientes'
            if self.request.GET.get('tipo') == 'pacientes'
            else 'empleados'
        )

    def get_queryset(self):
        q = _texto_busqueda(self.request)
        if self.get_tipo() == 'pacientes':
            queryset = Crud_paciente.objects.select_related(
                'editor', 'afectado'
            ).order_by('-fecha', '-id')
            return _buscar_auditoria_pacientes(queryset, q)

        queryset = Crud_empleado.objects.select_related(
            'editor', 'afectado'
        ).order_by('-fecha', '-id')
        return _buscar_auditoria_empleados(queryset, q)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo'] = self.get_tipo()
        context['q'] = _texto_busqueda(self.request)
        context['querystring'] = _querystring_sin_pagina(self.request)
        context['cantidad'] = self.get_queryset().count()
        return context


# FICHA Y EDICION DE USUARIOS (ESPECIALISTAS Y ADMINISTRADORES)

class DetalleUsuario(AdminRequiredMixin, DetailView):
    model = Usuario
    template_name = 'crud/usuario_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        es_admin = self.object.usuario_administrador
        context['titulo'] = "Administrador" if es_admin else "Especialista"
        context['nav_section'] = "administrador" if es_admin else "especialista"

        if es_admin:
            context['diagnosticos'] = Historial_paciente.objects.none()
            context['cantidad_diagnosticos'] = 0
        else:
            diagnosticos = Historial_paciente.objects.filter(
                empleado=self.object
            ).select_related('paciente', 'padecimiento').order_by('-fecha')
            paginator = Paginator(diagnosticos, 10)
            page_obj = paginator.get_page(self.request.GET.get('page'))
            context['diagnosticos'] = page_obj
            context['page_obj'] = page_obj
            context['cantidad_diagnosticos'] = paginator.count
            context['querystring'] = _querystring_sin_pagina(self.request)

        return context


class EditarUsuario(AdminRequiredMixin, UpdateView):
    model = Usuario
    form_class = EditarUsuarioForm
    template_name = 'crud/registrocrud/r_paciente.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        es_admin = self.object.usuario_administrador
        context['texto_boton'] = "Guardar cambios"
        context['tipo_usuario'] = "Administrador" if es_admin else "Doctor"
        context['accion'] = "Editar"
        context['nav_section'] = "administrador" if es_admin else "especialista"
        context['url_cancelar'] = reverse_lazy(
            'usuario_detalle', args=[self.object.pk]
        )
        return context

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            registrar_accion_empleado(
                self.request.user, self.object, ACCION_EDITAR
            )
        return response

    def get_success_url(self):
        return reverse_lazy('usuario_detalle', args=[self.object.pk])


# PERFIL PROPIO Y CONTRASENA

class MiPerfil(LoginRequiredMixin, DetailView):
    model = Usuario
    template_name = 'cuenta/perfil.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav_section'] = "perfil"
        return context


class EditarPerfil(LoginRequiredMixin, UpdateView):
    model = Usuario
    form_class = PerfilForm
    template_name = 'crud/registrocrud/r_paciente.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['texto_boton'] = "Guardar cambios"
        context['tipo_usuario'] = "perfil"
        context['accion'] = "Editar"
        context['nav_section'] = "perfil"
        context['panel_hint'] = "Actualiza tus datos personales de contacto."
        context['texto_cancelar'] = "Volver a mi perfil"
        context['url_cancelar'] = reverse_lazy('perfil')
        return context

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            registrar_accion_empleado(
                self.request.user, self.request.user, ACCION_PERFIL
            )
        messages.success(self.request, "Tus datos se actualizaron correctamente.")
        return response

    def get_success_url(self):
        return reverse_lazy('perfil')


class CambiarContrasena(LoginRequiredMixin, PasswordChangeView):
    template_name = 'cuenta/password_change_form.html'
    success_url = reverse_lazy('perfil')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav_section'] = "perfil"
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            field.widget.attrs["class"] = "custom-input"
            if name == "old_password":
                field.widget.attrs["autocomplete"] = "current-password"
            else:
                field.widget.attrs["autocomplete"] = "new-password"
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        registrar_accion_empleado(
            self.request.user, self.request.user, ACCION_CONTRASENA
        )
        messages.success(self.request, "Tu contraseña se actualizó correctamente.")
        return response


# DETALLE DE DIAGNOSTICOS

class DetalleDiagnostico(LoginRequiredMixin, DetailView):
    model = Historial_paciente
    template_name = 'crud/diagnostico_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        origen = self.request.GET.get('origen', 'd')
        datos = self.object.datos_set.first()
        parametros = []
        if datos:
            parametros = [
                ("Incidencia pélvica", datos.pelvic_incidence, "°"),
                ("Inclinación pélvica", datos.pelvic_tilt, "°"),
                ("Ángulo de lordosis lumbar", datos.lumbar_lordosis_angle, "°"),
                ("Pendiente sacra", datos.sacral_slope, "°"),
                ("Radio pélvico", datos.pelvic_radius, " mm"),
                ("Grado de espondilolistesis", datos.degree_spondylolisthesis, "%"),
            ]
        paginator = Paginator(parametros, 10)
        page_obj = paginator.get_page(self.request.GET.get('page'))
        context['titulo'] = "Diagnóstico"
        context['datos'] = datos
        context['parametros'] = page_obj
        context['page_obj'] = page_obj
        context['querystring'] = _querystring_sin_pagina(self.request)
        context['origen'] = origen
        context['nav_section'] = (
            'historial_m' if origen == 'mis' else 'historial_d'
        )
        return context

@require_GET
def healthz(request):
    return JsonResponse({'status': 'ok'})


@require_POST
def demo_login(request, role):
    if not getattr(settings, 'DEMO_MODE', False):
        messages.error(request, 'El modo demo no está disponible.')
        return redirect('login')
    role_map = {
        'admin': getattr(settings, 'DEMO_ADMIN_USERNAME', 'demo_admin'),
        'especialista': getattr(settings, 'DEMO_SPECIALIST_USERNAME', 'demo_especialista'),
    }
    username = role_map.get(role)
    if not username:
        messages.error(request, 'Rol demo no válido.')
        return redirect('login')
    user = Usuario.objects.filter(username=username, es_demo=True).first()
    if not user:
        messages.error(request, 'La cuenta demo no está disponible. Ejecuta seed_demo.')
        return redirect('login')
    if user.estado_id is None or getattr(user.estado, 'name', '') != 'Activo':
        messages.error(request, 'La cuenta demo no está activa.')
        return redirect('login')
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    auth_login(request, user)
    messages.success(request, f'Has ingresado como cuenta demo ({role}).')
    return redirect(settings.LOGIN_REDIRECT_URL or '/')
