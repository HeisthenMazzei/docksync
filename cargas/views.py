from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from openpyxl import Workbook
from openpyxl.styles import Font
from .models import Carga, FielDepositario, ModeloVeiculo, OperadorPortuario
from manifestos.models import Manifesto
from core.mixins import GroupRequiredMixin
import pandas as pd
from datetime import datetime
import os
import qrcode
from io import BytesIO


# ==========================================
# FUNÇÃO AUXILIAR: Formata tempo
# ==========================================
def formatar_tempo(timedelta_obj):
    if not timedelta_obj:
        return "-"
    total_seconds = int(timedelta_obj.total_seconds())
    if total_seconds < 0:
        return "-"
    if total_seconds < 60:
        return f"{total_seconds}s"
    minutos = total_seconds // 60
    if minutos < 60:
        return f"{minutos}min"
    horas = minutos // 60
    if horas < 24:
        mins = minutos % 60
        return f"{horas}h {mins}min" if mins else f"{horas}h"
    dias = horas // 24
    horas_restantes = horas % 24
    return f"{dias}d {horas_restantes}h" if horas_restantes else f"{dias}d"


# ==========================================
# CRUD DE OPERADOR PORTUÁRIO
# ==========================================
class OperadorPortuarioListView(GroupRequiredMixin, ListView):
    model = OperadorPortuario
    template_name = 'cadastro/operador_portuario_list.html'
    context_object_name = 'operadores'
    group_required = ['Administrador', 'Gestor']


class OperadorPortuarioCreateView(GroupRequiredMixin, CreateView):
    model = OperadorPortuario
    fields = ['nome_empresa', 'cnpj', 'telefone', 'responsavel_tecnico', 'numero_registro', 'data_validade', 'situacao']
    template_name = 'cadastro/operador_portuario_form.html'
    success_url = reverse_lazy('operador_portuario_list')
    group_required = ['Administrador', 'Gestor']


class OperadorPortuarioUpdateView(GroupRequiredMixin, UpdateView):
    model = OperadorPortuario
    fields = ['nome_empresa', 'cnpj', 'telefone', 'responsavel_tecnico', 'numero_registro', 'data_validade', 'situacao']
    template_name = 'cadastro/operador_portuario_form.html'
    success_url = reverse_lazy('operador_portuario_list')
    group_required = ['Administrador', 'Gestor']


class OperadorPortuarioDeleteView(GroupRequiredMixin, DeleteView):
    model = OperadorPortuario
    template_name = 'cadastro/confirm_delete.html'
    success_url = reverse_lazy('operador_portuario_list')
    group_required = ['Administrador']


# ==========================================
# CRUD DE FIEL DEPOSITÁRIO
# ==========================================
class FielDepositarioListView(GroupRequiredMixin, ListView):
    model = FielDepositario
    template_name = 'cadastro/fiel_list.html'
    context_object_name = 'fieis'
    group_required = ['Administrador', 'Gestor']


class FielDepositarioCreateView(GroupRequiredMixin, CreateView):
    model = FielDepositario
    fields = ['nome_completo', 'matricula']
    template_name = 'cadastro/fiel_form.html'
    success_url = reverse_lazy('fiel_list')
    group_required = ['Administrador', 'Gestor']


class FielDepositarioUpdateView(GroupRequiredMixin, UpdateView):
    model = FielDepositario
    fields = ['nome_completo', 'matricula']
    template_name = 'cadastro/fiel_form.html'
    success_url = reverse_lazy('fiel_list')
    group_required = ['Administrador', 'Gestor']


class FielDepositarioDeleteView(GroupRequiredMixin, DeleteView):
    model = FielDepositario
    template_name = 'cadastro/confirm_delete.html'
    success_url = reverse_lazy('fiel_list')
    group_required = ['Administrador']


# ==========================================
# CRUD DE MODELOS DE VEÍCULOS
# ==========================================
class ModeloVeiculoListView(GroupRequiredMixin, ListView):
    model = ModeloVeiculo
    template_name = 'cadastro/modelo_list.html'
    context_object_name = 'modelos'
    group_required = ['Administrador', 'Gestor']


class ModeloVeiculoCreateView(GroupRequiredMixin, CreateView):
    model = ModeloVeiculo
    fields = ['fabricante', 'modelo', 'abreviado', 'ano', 'comprimento', 'largura']
    template_name = 'cadastro/modelo_form.html'
    success_url = reverse_lazy('modelo_list')
    group_required = ['Administrador', 'Gestor']


class ModeloVeiculoUpdateView(GroupRequiredMixin, UpdateView):
    model = ModeloVeiculo
    fields = ['fabricante', 'modelo', 'abreviado', 'ano', 'comprimento', 'largura']
    template_name = 'cadastro/modelo_form.html'
    success_url = reverse_lazy('modelo_list')
    group_required = ['Administrador', 'Gestor']


class ModeloVeiculoDeleteView(GroupRequiredMixin, DeleteView):
    model = ModeloVeiculo
    template_name = 'cadastro/confirm_delete.html'
    success_url = reverse_lazy('modelo_list')
    group_required = ['Administrador']


# ==========================================
# BUSCA DE CARGA
# ==========================================
def buscar_carga(request):
    chassi = request.GET.get('chassi')
    carga = None
    historico = None

    if chassi:
        try:
            carga = Carga.objects.select_related(
                'manifesto__viagem__navio', 'setor_atual', 'dono', 'modelo', 'operador'
            ).prefetch_related('movimentacoes__setor_origem', 'movimentacoes__setor_destino').get(chassi=chassi)

            historico = carga.movimentacoes.all().order_by('-data_hora')
        except Carga.DoesNotExist:
            carga = None

    return render(request, 'busca.html', {'carga': carga, 'historico': historico, 'chassi_busca': chassi})


# ==========================================
# GESTÃO DE CARGAS
# ==========================================
class CargaListView(GroupRequiredMixin, ListView):
    model = Carga
    template_name = 'cargas/carga_list.html'
    context_object_name = 'cargas'
    group_required = ['Administrador', 'Gestor']
    ordering = ['bl', 'chassi']
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'operador', 'dono', 'modelo', 'setor_atual', 'manifesto__viagem__navio'
        )

        chassi = self.request.GET.get('chassi')
        if chassi:
            queryset = queryset.filter(chassi__icontains=chassi)
        bl = self.request.GET.get('bl')
        if bl:
            queryset = queryset.filter(bl__icontains=bl)
        operador = self.request.GET.get('operador')
        if operador:
            queryset = queryset.filter(operador__nome_empresa__icontains=operador)
        setor = self.request.GET.get('setor')
        if setor:
            queryset = queryset.filter(setor_atual__nome__icontains=setor)
        modelo = self.request.GET.get('modelo')
        if modelo:
            queryset = queryset.filter(modelo__modelo__icontains=modelo)

        ordenar_por = self.request.GET.get('ordenar_por', 'bl')
        campo = ordenar_por.lstrip('-') if ordenar_por.startswith('-') else ordenar_por
        campos_permitidos = ['chassi', 'bl', 'operador__nome_empresa', 'dono__nome_completo', 'modelo__fabricante', 'metragem_unitaria', 'setor_atual__nome']
        if campo not in campos_permitidos:
            campo = 'bl'
        if ordenar_por.startswith('-'):
            return queryset.order_by(f'-{campo}')
        return queryset.order_by(campo)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtro_chassi'] = self.request.GET.get('chassi', '')
        context['filtro_bl'] = self.request.GET.get('bl', '')
        context['filtro_operador'] = self.request.GET.get('operador', '')
        context['filtro_setor'] = self.request.GET.get('setor', '')
        context['filtro_modelo'] = self.request.GET.get('modelo', '')
        return context


class CargaCreateView(GroupRequiredMixin, CreateView):
    model = Carga
    fields = ['bl', 'chassi', 'manifesto', 'operador', 'dono', 'modelo', 'metragem_unitaria']
    template_name = 'cargas/carga_form.html'
    success_url = reverse_lazy('carga_list')
    group_required = ['Administrador', 'Gestor']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manifestos'] = Manifesto.objects.all()
        context['donos'] = FielDepositario.objects.all()
        context['modelos'] = ModeloVeiculo.objects.all()
        context['operadores'] = OperadorPortuario.objects.all()
        return context


class CargaDetailView(GroupRequiredMixin, DetailView):
    model = Carga
    template_name = 'cargas/carga_detail.html'
    context_object_name = 'carga'
    group_required = ['Administrador', 'Gestor']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carga = self.object
        context['historico'] = carga.movimentacoes.all().order_by('-data_hora')
        chegada = carga.movimentacoes.filter(tipo='CHEGADA').order_by('data_hora').first()
        saida = carga.movimentacoes.filter(tipo='SAIDA').order_by('-data_hora').first()
        if chegada:
            if saida:
                tempo_permanencia = saida.data_hora - chegada.data_hora
            else:
                tempo_permanencia = timezone.now() - chegada.data_hora
            context['tempo_permanencia'] = formatar_tempo(tempo_permanencia)
        else:
            context['tempo_permanencia'] = "-"
        if carga.manifesto.data_estimada_retirada:
            context['prazo_excedido'] = carga.manifesto.data_estimada_retirada < timezone.now().date()
        else:
            context['prazo_excedido'] = False
        return context


# ==========================================
# DETALHES DO BL
# ==========================================
class BLDetailView(ListView):
    model = Carga
    template_name = 'cargas/bl_detail.html'
    context_object_name = 'cargas'

    def get_queryset(self):
        self.bl = self.kwargs['bl']
        return Carga.objects.filter(bl=self.bl).select_related('modelo').order_by('chassi')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bl'] = self.bl
        primeira_carga = self.get_queryset().first()
        if primeira_carga:
            context['operador'] = primeira_carga.operador
            context['dono'] = primeira_carga.dono
            context['manifesto'] = primeira_carga.manifesto
            context['previsao_saida'] = primeira_carga.manifesto.data_estimada_retirada
            total_metragem = self.get_queryset().aggregate(total=Sum('metragem_unitaria'))['total']
            context['total_metragem'] = total_metragem or 0
            context['total_cargas'] = self.get_queryset().count()
        else:
            context['operador'] = None
            context['dono'] = None
            context['manifesto'] = None
            context['previsao_saida'] = None
            context['total_metragem'] = 0
            context['total_cargas'] = 0
        return context


# ==========================================
# IMPORTAÇÃO DE OPERADORES VIA EXCEL
# ==========================================
def importar_operadores_arquivo(request):
    if request.method == 'POST' and request.FILES.get('arquivo_operadores'):
        arquivo = request.FILES['arquivo_operadores']
        try:
            if arquivo.name.endswith('.xls') or arquivo.name.endswith('.xlsx'):
                df = pd.read_excel(arquivo, header=0)
            else:
                messages.error(request, "Formato inválido. Envie um arquivo .xls ou .xlsx.")
                return redirect('operador_portuario_list')

            criados = 0
            atualizados = 0
            for index, row in df.iterrows():
                try:
                    nome = str(row.get('Nome Empresa', '')).strip()
                    cnpj = str(row.get('CNPJ', '')).strip()
                    telefone = str(row.get('Telefone', '')).strip()
                    responsavel = str(row.get('Responsável Técnico', row.get('Responsavel Tecnico', ''))).strip()
                    numero = str(row.get('Número', row.get('Numero', ''))).strip()
                    data_validade = row.get('Data Validade', '')
                    situacao = str(row.get('Situação', row.get('Situacao', ''))).strip()

                    try:
                        if isinstance(data_validade, datetime):
                            data_val = data_validade.date()
                        else:
                            data_str = str(data_validade).split(' ')[0]
                            data_val = datetime.strptime(data_str, '%d/%m/%Y').date()
                    except:
                        data_val = None

                    if not nome:
                        continue

                    operador = None
                    if cnpj:
                        operador = OperadorPortuario.objects.filter(cnpj=cnpj).first()

                    if not operador:
                        operador = OperadorPortuario.objects.filter(nome_empresa=nome).first()

                    if operador:
                        operador.nome_empresa = nome
                        operador.cnpj = cnpj
                        operador.telefone = telefone
                        operador.responsavel_tecnico = responsavel
                        operador.numero_registro = numero
                        operador.data_validade = data_val
                        operador.situacao = situacao
                        operador.save()
                        atualizados += 1
                    else:
                        OperadorPortuario.objects.create(
                            nome_empresa=nome,
                            cnpj=cnpj,
                            telefone=telefone,
                            responsavel_tecnico=responsavel,
                            numero_registro=numero,
                            data_validade=data_val,
                            situacao=situacao
                        )
                        criados += 1
                except Exception as e:
                    continue

            messages.success(request, f"Importação concluída! {criados} criados, {atualizados} atualizados.")
        except Exception as e:
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")
            return redirect('operador_portuario_list')

        return redirect('operador_portuario_list')
    return redirect('operador_portuario_list')


# ==========================================
# EXPORTAÇÃO DE CARGAS PARA EXCEL
# ==========================================
def exportar_cargas_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Cargas"
    headers = ['BL', 'Chassi', 'Operador', 'Fiel Depositário', 'Modelo', 'Ano', 'Metragem (m²)', 'Localização']
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    cargas = Carga.objects.select_related('operador', 'dono', 'modelo', 'setor_atual').all().order_by('bl', 'chassi')
    for c in cargas:
        ws.append([
            c.bl, c.chassi,
            c.operador.nome_empresa if c.operador else "",
            c.dono.nome_completo if c.dono else "",
            f"{c.modelo.fabricante} {c.modelo.modelo}" if c.modelo else "",
            c.modelo.ano if c.modelo else "",
            c.metragem_unitaria,
            c.setor_atual.nome if c.setor_atual else ""
        ])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="cargas.xlsx"'
    wb.save(response)
    return response


# ==========================================
# GERADOR DE QR CODE POR CHASSI
# ==========================================
def gerar_qrcode_chassi(request, chassi):
    Carga.objects.filter(chassi=chassi).exists()
    url = request.build_absolute_uri(reverse('ficha_publica_veiculo', args=[chassi]))

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0B1A2A", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')

    return HttpResponse(buffer.getvalue(), content_type='image/png')


# ==========================================
# FICHA PÚBLICA
# ==========================================
def ficha_publica_veiculo(request, chassi):
    carga = get_object_or_404(
        Carga.objects.select_related('dono', 'operador', 'modelo', 'manifesto__viagem__navio'),
        chassi=chassi
    )

    chegada = carga.movimentacoes.filter(tipo='CHEGADA').order_by('data_hora').first()
    saida = carga.movimentacoes.filter(tipo='SAIDA').order_by('-data_hora').first()

    context = {
        'carga': carga,
        'data_entrada': chegada.data_hora if chegada else None,
        'data_saida': saida.data_hora if saida else None,
        'fiel_depositario': carga.dono,
        'operador_logistico': carga.operador,
        'setor_atual': carga.setor_atual,
    }
    return render(request, 'ficha_publica.html', context)


# ==========================================
# IMPRESSÃO DE ETIQUETA INDIVIDUAL
# ==========================================
def imprimir_etiqueta_chassi(request, chassi):
    carga = get_object_or_404(
        Carga.objects.select_related('dono', 'operador', 'modelo', 'manifesto__viagem__navio'),
        chassi=chassi
    )
    return render(request, 'imprimir_etiqueta.html', {'carga': carga})


# ==========================================
# IMPRESSÃO EM LOTE
# ==========================================
def imprimir_lote_etiquetas(request):
    cargas = Carga.objects.none()
    titulo = "Etiquetas"

    bl = request.GET.get('bl')
    setor_id = request.GET.get('setor')

    if bl:
        cargas = list(
            Carga.objects.filter(bl=bl)
            .select_related('modelo', 'dono', 'operador')
            .order_by('chassi')
        )
        titulo = f"Etiquetas — {bl}"
    elif setor_id:
        from setores.models import Setor
        setor = Setor.objects.filter(id=setor_id).first()
        cargas = list(
            Carga.objects.filter(setor_atual_id=setor_id)
            .select_related('modelo', 'dono', 'operador')
            .order_by('chassi')
        )
        if setor:
            titulo = f"Etiquetas — {setor.nome}"

    context = {
        'cargas': cargas,
        'cargas_paginadas': paginar_em_blocos(cargas, 8),
        'titulo': titulo,
    }
    return render(request, 'imprimir_lote.html', context)


def paginar_em_blocos(lista, tamanho=8):
    return [lista[i:i + tamanho] for i in range(0, len(lista), tamanho)]