from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Paciente, Historial_paciente, Datos,Padecimiento,Usuario
from .forms import ValidarEmpleado,ValidarPrediccion, CrearPaciente,CrearUsuario
from django.contrib.auth.decorators import login_required
import joblib
import numpy as np
import pandas as pd
from . import utils
import os
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image
from django.conf import settings
from decimal import Decimal
from django.db.models import Avg
from django.views.generic import CreateView,UpdateView,ListView,DeleteView,View
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

# Create your views here.
def login(request):
    return render(request,"auth/login.html", {'form': ValidarEmpleado()})

def home(request):
    return render(request,"layout/base.html")

@login_required
def dashboard(request):
    cantidad = Historial_paciente.objects.count()
    cantidad_paciente = Paciente.objects.filter(activo=True).count()
    hernia = Historial_paciente.objects.filter(padecimiento=1).count()
    spon = Historial_paciente.objects.filter(padecimiento=2).count()
    normal = Historial_paciente.objects.filter(padecimiento=3).count()
    historial = Historial_paciente.objects.select_related('paciente', 'padecimiento', 'empleado').order_by('-fecha')
    nomal_precision = Historial_paciente.objects.filter(padecimiento=3).aggregate(Avg('precision_value'))
    hernia_precision = Historial_paciente.objects.filter(padecimiento=1).aggregate(Avg('precision_value'))
    spon_precision = Historial_paciente.objects.filter(padecimiento=2).aggregate(Avg('precision_value'))
    
    return render(request, "dashboard/dashboard.html",{
        'diagnosticos_cantidad':cantidad,
        'cantidad_paciente':cantidad_paciente,
        'normal_count': normal,
        'hernia_count':hernia,
        'spon_count':spon,
        'historial_diagnosticos':historial,
        'precision_n':nomal_precision,
        'precision_hernia':hernia_precision,
        'precision_spon':spon_precision
    })

@login_required
def moduloDiagnostico(request):
    return render(request, "dashboard/diagnostico.html")

# @login_required
# def moduloEspecialista(request):
#     return render(request, "crud/especialista.html")
        
# @login_required
# def moduloRegistroPaciente(request):
#     return render(request, "crud/registrocrud/r_paciente.html",{
#         'form': CrearPaciente(),
#         'tipo_usuario':"paciente",
#         'texto_boton': "Enviar"
#         })
    
@login_required
def moduloAdministrador(request):
    return render(request, "crud/administradores.html")
    
@login_required
def moduloDiagnosticoEtp1(request):
    pacientes = Paciente.objects.all().filter(activo=True)
    cantidad = Paciente.objects.filter(activo=True).count()
    return render(request,"dashboard/modulos/etapa1.html",{
        'pacientes':pacientes,
        'cantidad':cantidad
    })
    
@login_required
def moduloDiagnosticoEtp2(request,id):
    paciente = get_object_or_404(Paciente,id=id)
    return render(request,"dashboard/modulos/etapa2.html",{
        'paciente':paciente
    })
    
@login_required
def moduloDiagnosticoEtp3(request,id):
    paciente = get_object_or_404(Paciente,id=id)
    return render(request,"dashboard/modulos/etapa3.html",{
        'paciente':paciente,
        'form': ValidarPrediccion()
    })

# Genera el informe del diagnostico
@login_required
def moduloInformeDiagnostico(request, paciente_id):
    # Obtener datos del paciente y su historial
    image_path = os.path.join(settings.BASE_DIR, 'tasks', 'static', 'img', 'logo-hospital-transparente.png')
    logo = Image(image_path, width=2 * inch, height=2 * inch)
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historial_paciente = Historial_paciente.objects.filter(paciente=paciente).order_by('-fecha').first()

    if not historial_paciente:
        return HttpResponse("No se encontró historial para el paciente.", status=404)

    historial_con_datos = historial_paciente.datos_set.all()

    # Crear la respuesta HTTP para el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="informe_diagnostico_{paciente.id}.pdf"'

    # Configuración del PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Estilo de texto
    styles = getSampleStyleSheet()

    # Título del informe
    title = Paragraph(f"<b>Informe Diagnóstico - {paciente.primer_nombre} {paciente.apellido_paterno}</b>", styles['Title'])
    elements.append(title)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='subTitle',
        fontSize=14,
        leading=16,
        spaceAfter=12,
        alignment=1,  # Centrado
        textColor=colors.black
    ))
    
    subtitle = Paragraph(f"<b>Realizado por el Dr. {request.user.primer_nombre} {request.user.apellido_paterno}</b>", styles['subTitle'])
    elements.append(subtitle)
    elements.append(logo)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Información del paciente
    info_paciente = [
        ["Campo", "Valor"],
        ["Nombre completo", f"{paciente.primer_nombre} {paciente.segundo_nombre or ''} {paciente.apellido_paterno} {paciente.apellido_materno}"],
        ["Correo", paciente.correo],
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

    # Espaciado


    # Información del diagnóstico
    datos_historial = [["Parámetro", "Valor"]]
    for dato in historial_con_datos:
        datos_historial.append(["Incidencia pélvica", dato.pelvic_incidence])
        datos_historial.append(["Inclinación pélvica", dato.pelvic_tilt])
        datos_historial.append(["Ángulo de lordosis lumbar", dato.lumbar_lordosis_angle])
        datos_historial.append(["Pendiente sacra", dato.sacral_slope])
        datos_historial.append(["Radio pélvico", dato.pelvic_radius])
        datos_historial.append(["Grado de espondilolistesis", dato.degree_spondylolisthesis])
        datos_historial.append(["Nivel de confianza", f"{historial_paciente.precision_value}%"])

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
    precision = Paragraph(f"<b>Diagnostico obtenido: {historial_paciente.padecimiento}</b>", styles['subTitle'])
    elements.append(table_historial)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    elements.append(precision)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    
    

    # Espaciado
    elements.append(Paragraph("<br/>", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    

    # Leyenda
    leyenda = Paragraph(
        "El Hospital Regional Eleazar Guzmán Barrón es una institución dedicada a la atención integral de salud en la región, "
        "brindando servicios médicos de calidad con un enfoque en la mejora continua. Este informe tiene como propósito "
        "evaluar los datos del paciente para identificar áreas críticas y garantizar una atención efectiva.",
        styles['Normal']
    )
    elements.append(leyenda)

    # Construir el documento PDF
    doc.build(elements)

    return response

# Realiza la predicción de la patología
@login_required
def realizar_prediccion(request, paciente_id):
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

    # Obtener el paciente desde la URL
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
  
    
    # padecimiento = get_object_or_404(Padecimiento, id=1)

    # Definir los nuevos datos para predecir con los nombres de columna correctos
    # example_features = [44.318907, 12.537992, 36.098763, 31.780915, 124.115836, 5.415825]
    example_features = [request.GET['pelvic_incidence'],request.GET['pelvic_tilt'],request.GET['lumbar_lordosis_angle'],request.GET['sacral_slope'],request.GET['pelvic_radius'],request.GET['degree_spondylolisthesis']]
    nuevos_datos = pd.DataFrame([example_features], columns=[
        'pelvic_incidence', 'pelvic_tilt', 'lumbar_lordosis_angle', 'sacral_slope', 'pelvic_radius', 'degree_spondylolisthesis'
    ])

    # Estandarizar los nuevos datos usando el mismo escalador que durante el entrenamiento
    nuevos_datos_scaled = scaler.transform(nuevos_datos)

    # Realizar predicciones
    predicciones_xgb = xgb_model.predict(nuevos_datos_scaled)
    predicciones_proba_xgb = xgb_model.predict_proba(nuevos_datos_scaled)

    # Decodificar la predicción a la clase original
    prediccion_decodificada_xgb = label_encoder.inverse_transform(predicciones_xgb)[0]
    confidence_xgb = max(predicciones_proba_xgb[0]) * 100  # Porcentaje de confianza

    # Validación si la predicción se realizó correctamente
    if prediccion_decodificada_xgb:
        
        if(prediccion_decodificada_xgb=="Hernia"):
            padecimiento = get_object_or_404(Padecimiento, id=1)
        elif(prediccion_decodificada_xgb=="Spondylolisthesis"):
            padecimiento = get_object_or_404(Padecimiento, id=2)
        else:
            padecimiento = get_object_or_404(Padecimiento, id=3)
        
        
        # Crear el historial para el paciente
        historial_paciente = Historial_paciente.objects.create(
            empleado=request.user,  # El empleado es el usuario logueado (doctor)
            paciente=paciente,  # El paciente se pasa en la URL
            padecimiento=padecimiento,  # Puedes asignar el padecimiento si se recibe de alguna fuente
            precision_value=Decimal(str(confidence_xgb))
        )

        # Guardar los datos del paciente en la tabla Datos
        Datos.objects.create(
            historial_paciente=historial_paciente,
            pelvic_incidence=example_features[0],
            pelvic_tilt=example_features[1],
            lumbar_lordosis_angle=example_features[2],
            sacral_slope=example_features[3],
            pelvic_radius=example_features[4],
            degree_spondylolisthesis=example_features[5]
        )

        # Obtener los datos del historial para mostrar en la vista
        historial_paciente = Historial_paciente.objects.filter(paciente=paciente).order_by('-fecha').first()
        historial_con_datos = historial_paciente.datos_set.all() 

        # Pasar el historial y los datos al contexto para la vista
        contexto = {
            'historial': historial_paciente,
            'datos': historial_con_datos,
            'prediccion': prediccion_decodificada_xgb,
            'confidence': confidence_xgb,
            'paciente':paciente
        }

        # Renderizar la plantilla 'etapaf.html' con los datos
        return render(request, 'dashboard/modulos/etapaf.html', {
            'contexto':contexto
        })

    else:
        # Si la predicción no se realizó correctamente, redirigir o manejar el error
        return render(request, 'dashboard/modulos/etapaf.html', {'error': 'Error en la predicción'})
    

# @login_required
# def moduloPaciente(request):
#     titulo = "Paciente"
#     pacientes = Paciente.objects.all().filter(activo=True)
#     cantidad = Paciente.objects.filter(activo=True).count()
#     return render(request, "crud/pacientes.html",{
#         'titulo':titulo,
#         'pacientes':pacientes,
#         'cantidad':cantidad
#     })

@login_required
def moduloHistorialD(request):
    titulo = "Historial de diagnósticos"
    historial = Historial_paciente.objects.select_related('paciente', 'padecimiento', 'empleado').order_by('-fecha')
    return render(request, "crud/historiald.html",{
        'titulo':titulo,
        'historial':historial,
        'cantidad':historial.count(),
    })
    
@login_required
def moduloHistorialInteracciones(request):
    titulo = "Mi Historial de diagnósticos"
    usuario_actual = request.user
    historial = Historial_paciente.objects.select_related('paciente', 'padecimiento', 'empleado') \
        .filter(empleado=usuario_actual) \
        .order_by('-fecha')
    return render(request, "crud/mihistorial.html",{
        'titulo':titulo,
        'historial':historial,
        'cantidad':historial.count(),
    })

@method_decorator(login_required, name='dispatch')
class ListadoPaciente(ListView):
    model = Paciente
    template_name= "crud/pacientes.html"
    
    def get_queryset(self):
        return self.model.objects.filter(activo=True)
    
    def get_context_data(self, **kwargs):
        # Primero, obtiene el contexto original de la vista
        context = super().get_context_data(**kwargs)

        # Agregar datos adicionales al contexto
        context['titulo'] = "Paciente"  # Agregar título
        context['cantidad'] = Paciente.objects.filter(activo=True).count()  # Cantidad de pacientes activos
        
        return context

@method_decorator(login_required, name='dispatch')
class RegistrarPaciente(CreateView):
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
    
@method_decorator(login_required, name='dispatch')
class DesactivarPaciente(View):
    def post(self, request, *args, **kwargs):
        paciente_id = kwargs.get('pk')
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        
        # Cambiar el estado de 'activo' a False
        paciente.activo = False
        paciente.save()

        # Redirigir a la lista de pacientes u otra página
        return redirect(reverse_lazy('paciente'))

# METODOS PARA LOS ESPECIALISTAS

@method_decorator(login_required, name='dispatch')
class ListadoDoctor(ListView):
    model = Usuario
    template_name = "crud/especialista.html"
    
    def get_queryset(self):
        # Obtiene los usuarios activos
        return self.model.objects.filter(estado_id=1,usuario_administrador=0)
    
    def get_context_data(self, **kwargs):
        # Obtiene el contexto original de la vista
        context = super().get_context_data(**kwargs)

        # Agregar datos adicionales al contexto
        context['titulo'] = "Especialista"  # Título de la vista
        context['cantidad'] = self.get_queryset().count()  # Cantidad de usuarios activos (utilizando el queryset filtrado)
        
        return context


@method_decorator(login_required, name='dispatch')
class RegistrarUsuario(CreateView):
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
    
    
@method_decorator(login_required, name='dispatch')
class DesactivarUsuario(View):
    def post(self, request, *args, **kwargs):
        usuario_id = kwargs.get('pk')
        usuario = get_object_or_404(Usuario, pk=usuario_id)
        
        # Cambiar el estado de 'activo' a False
        usuario.estado_id = 2
        usuario.save()

        # Redirigir a la lista de pacientes u otra página
        return redirect(reverse_lazy('especialista'))
    
    
# METODOS PARA LOS ADMINS

@method_decorator(login_required, name='dispatch')
class ListadoAdmin(ListView):
    model = Usuario
    template_name = "crud/admin.html"
    
    def get_queryset(self):
        # Obtiene los usuarios activos
        return self.model.objects.filter(estado_id=1,usuario_administrador=1)
    
    def get_context_data(self, **kwargs):
        # Obtiene el contexto original de la vista
        context = super().get_context_data(**kwargs)

        # Agregar datos adicionales al contexto
        context['titulo'] = "Administrador"  # Título de la vista
        context['cantidad'] = self.get_queryset().count()  # Cantidad de usuarios activos (utilizando el queryset filtrado)
        
        return context


@method_decorator(login_required, name='dispatch')
class RegistrarUsuarioAdmin(CreateView):
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
    
    
@method_decorator(login_required, name='dispatch')
class DesactivarUsuarioAdmin(View):
    def post(self, request, *args, **kwargs):
        usuario_id = kwargs.get('pk')
        usuario = get_object_or_404(Usuario, pk=usuario_id)
        
        # Cambiar el estado de 'activo' a False
        usuario.estado_id = 2
        usuario.save()

        # Redirigir a la lista de pacientes u otra página
        return redirect(reverse_lazy('administrador'))