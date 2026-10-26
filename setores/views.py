from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from .models import Setor
from navios.models import Viagem
from movimentacoes.models import Movimentacao
from cargas.models import Carga
from core.mixins import GroupRequiredMixin


def atualizar_status_por_data():
    hoje = timezone.now().date()
    for viagem in Viagem.objects.all():
        if viagem.data_desatracacao and hoje >= viagem.data_desatracacao:
            if viagem.status != 'FINALIZADO':
                viagem.status = 'FINALIZADO'
                viagem.save(update_fields=['status'])
        elif viagem.data_chegada_real and hoje >= viagem.data_chegada_real:
            if viagem.status != 'ATRACADO':
                viagem.status = 'ATRACADO'
                viagem.save(update_fields=['status'])
        elif viagem.data_prevista_chegada and hoje >= viagem.data_prevista_chegada:
            if viagem.status != 'FUNDEADO':
                viagem.status = 'FUNDEADO'
                viagem.save(update_fields=['status'])
        else:
            if viagem.status != 'AGUARDANDO_CHEGADA':
                viagem.status = 'AGUARDANDO_CHEGADA'
                viagem.save(update_fields=['status'])


def extrair_numero_codigo(codigo):
    try:
        return int(''.join(filter(str.isdigit, codigo)))
    except (ValueError, TypeError):
        return 999


def definir_status_ocupacao(percentual):
    if percentual >= 95:
        return 'critico'
    elif percentual >= 80:
        return 'alerta'
    elif percentual >= 50:
        return 'atencao'
    else:
        return 'livre'


def _preparar_subpatios():
    subpatios_qs = list(
        Setor.objects.filter(setor_pai__isnull=False)
        .annotate(
            total_cargas=Count('cargas_presentes'),
            total_metragem=Sum('cargas_presentes__metragem_unitaria')
        )
    )

    for setor in subpatios_qs:
        capacidade = float(setor.capacidade_metragem or 0)
        ocupado = float(setor.total_metragem or 0)
        percentual = round((ocupado / capacidade) * 100, 1) if capacidade > 0 else 0
        setor.quantidade_cargas = setor.total_cargas
        setor.metragem_ocupada = ocupado
        setor.percentual_ocupacao = percentual
        setor.status_ocupacao = definir_status_ocupacao(percentual)

    numerico = sorted(subpatios_qs, key=lambda x: extrair_numero_codigo(x.codigo))

    total = len(numerico)
    visual = []
    if total > 0:
        cols = 4
        rows = (total + cols - 1) // cols
        for r in range(rows):
            for c in range(cols):
                index = c * rows + r
                if index < total:
                    visual.append(numerico[index])

    return visual, numerico


@login_required
def dashboard(request):
    atualizar_status_por_data()
    try:
        dias = int(request.GET.get('dias', 7))
        if dias < 1:
            dias = 7
    except:
        dias = 7

    hoje = timezone.now().date()
    inicio_periodo = hoje - timedelta(days=dias - 1)
    fim_periodo = hoje

    # ==========================================
    # MOVIMENTAÇÕES REALIZADAS (usa data_hora = DateTime)
    # ==========================================
    movs_periodo = Movimentacao.objects.filter(data_hora__date__gte=inicio_periodo)
    movs_agrupadas = (
        movs_periodo
        .annotate(dia=TruncDate('data_hora'))
        .values('dia', 'tipo')
        .annotate(total=Count('id'))
    )
    movs_dict = {(m['dia'], m['tipo']): m['total'] for m in movs_agrupadas}

    # ==========================================
    # ENTRADAS ESPERADAS
    # Agrupa direto pelo DateField (sem TruncDate!)
    # ==========================================
    entradas_esperadas_qs = (
        Carga.objects
        .filter(
            setor_atual__isnull=True,
            manifesto__viagem__data_prevista_chegada__gte=inicio_periodo,
            manifesto__viagem__data_prevista_chegada__lte=fim_periodo,
        )
        .values('manifesto__viagem__data_prevista_chegada')
        .annotate(total=Count('id'))
    )
    entradas_esperadas_dict = {
        e['manifesto__viagem__data_prevista_chegada']: e['total']
        for e in entradas_esperadas_qs
    }

    # ==========================================
    # SAÍDAS ESPERADAS
    # ==========================================
    saidas_esperadas_qs = (
        Carga.objects
        .filter(
            setor_atual__isnull=False,
            manifesto__data_estimada_retirada__gte=inicio_periodo,
            manifesto__data_estimada_retirada__lte=fim_periodo,
        )
        .values('manifesto__data_estimada_retirada')
        .annotate(total=Count('id'))
    )
    saidas_esperadas_dict = {
        s['manifesto__data_estimada_retirada']: s['total']
        for s in saidas_esperadas_qs
    }

    # ==========================================
    # MONTA AS LISTAS
    # ==========================================
    dias_labels, entradas, saidas, entradas_esperadas, saidas_esperadas = [], [], [], [], []
    for i in range(dias):
        dia = inicio_periodo + timedelta(days=i)
        dias_labels.append(dia.strftime('%d/%m'))
        entradas.append(movs_dict.get((dia, 'CHEGADA'), 0))
        saidas.append(movs_dict.get((dia, 'SAIDA'), 0))
        entradas_esperadas.append(entradas_esperadas_dict.get(dia, 0))
        saidas_esperadas.append(saidas_esperadas_dict.get(dia, 0))

    # ==========================================
    # TEMPO MÉDIO DE PERMANÊNCIA
    # ==========================================
    tempo_medio_str = "0h 0m"
    cargas_saida = Carga.objects.filter(movimentacoes__tipo='SAIDA', movimentacoes__data_hora__date__gte=inicio_periodo).distinct()
    if cargas_saida.exists():
        total_segundos = 0
        count = 0
        for carga in cargas_saida:
            chegada = carga.movimentacoes.filter(tipo='CHEGADA').order_by('data_hora').first()
            saida = carga.movimentacoes.filter(tipo='SAIDA').order_by('-data_hora').first()
            if chegada and saida:
                diff = saida.data_hora - chegada.data_hora
                total_segundos += diff.total_seconds()
                count += 1
        if count > 0:
            media_segundos = total_segundos / count
            horas = int(media_segundos // 3600)
            minutos = int((media_segundos % 3600) // 60)
            tempo_medio_str = f"{horas}h {minutos}m"

    # ==========================================
    # INDICADORES
    # ==========================================
    total_cargas_armazenadas = Carga.objects.filter(setor_atual__isnull=False).count()

    cargas_previstas = Carga.objects.filter(
        setor_atual__isnull=True,
        manifesto__viagem__status__in=['AGUARDANDO_CHEGADA', 'FUNDEADO']
    ).count()

    # ==========================================
    # OCUPAÇÃO
    # ==========================================
    total_capacidade = float(Setor.objects.filter(setor_pai__isnull=False).aggregate(Sum('capacidade_metragem'))['capacidade_metragem__sum'] or 0)
    total_metragem_patio = float(
        Carga.objects.filter(setor_atual__isnull=False).aggregate(Sum('metragem_unitaria'))['metragem_unitaria__sum'] or 0
    )
    metragem_prevista = float(
        Carga.objects.filter(
            setor_atual__isnull=True,
            manifesto__viagem__status__in=['AGUARDANDO_CHEGADA', 'FUNDEADO']
        ).aggregate(Sum('metragem_unitaria'))['metragem_unitaria__sum'] or 0
    )

    # ==========================================
    # TOP OPERADORES E PIZZA
    # ==========================================
    top_operadores = list(Carga.objects.exclude(operador__isnull=True).values('operador__nome_empresa').annotate(total=Count('id')).order_by('-total')[:5])
    pizza_operadores = list(Carga.objects.exclude(operador__isnull=True).values('operador__nome_empresa').annotate(total=Count('id')).order_by('-total'))

    saidas_periodo = sum(v for k, v in movs_dict.items() if k[1] == 'SAIDA')

    navios_stats = {
        'aguardando': Viagem.objects.filter(status='AGUARDANDO_CHEGADA').count(),
        'atracados': Viagem.objects.filter(status__in=['ATRACADO', 'DESCARREGANDO', 'CARREGANDO']).count(),
        'carregando': Viagem.objects.filter(status='CARREGANDO').count(),
        'finalizados': Viagem.objects.filter(status='FINALIZADO').count(),
    }

    ultimas_movimentacoes = Movimentacao.objects.select_related('carga', 'setor_destino', 'setor_origem', 'trabalhador').order_by('-data_hora')[:10]

    ocupacao_comparativo = {
        'no_patio': total_cargas_armazenadas,
        'previstos': cargas_previstas,
        'metragem_no_patio': round(total_metragem_patio, 1),
        'metragem_prevista': round(metragem_prevista, 1),
        'capacidade_total': round(total_capacidade, 1),
    }

    return render(request, 'dashboard.html', {
        'navios_stats': navios_stats,
        'dias_labels': dias_labels,
        'entradas': entradas,
        'saidas': saidas,
        'entradas_esperadas': entradas_esperadas,
        'saidas_esperadas': saidas_esperadas,
        'tempo_medio': tempo_medio_str,
        'top_operadores': top_operadores,
        'pizza_operadores': pizza_operadores,
        'saidas_periodo': saidas_periodo,
        'dias': dias,
        'total_cargas_armazenadas': total_cargas_armazenadas,
        'cargas_previstas': cargas_previstas,
        'ocupacao_comparativo': ocupacao_comparativo,
        'ultimas_movimentacoes': ultimas_movimentacoes,
    })


@login_required
def gestao_patio(request):
    patio_modelo = Setor.objects.filter(setor_pai__isnull=True).first()
    hoje = timezone.now().date()

    subpatios_agg = (
        Setor.objects.filter(setor_pai__isnull=False)
        .annotate(
            total_cargas=Count('cargas_presentes'),
            total_metragem=Sum('cargas_presentes__metragem_unitaria')
        )
    )

    total_cargas_patio = sum(s.total_cargas for s in subpatios_agg)
    total_metragem_patio = float(sum(s.total_metragem for s in subpatios_agg if s.total_metragem) or 0)
    capacidade_patio = float(patio_modelo.capacidade_metragem or 0) if patio_modelo else 0
    percentual_patio = round((total_metragem_patio / capacidade_patio) * 100, 1) if capacidade_patio > 0 else 0

    def calcular_prazo_excedido(setor):
        if not setor:
            return 0
        cargas_diretas = setor.cargas_presentes.filter(manifesto__data_estimada_retirada__lt=hoje).count()
        if setor.setor_pai is None:
            filhos = Setor.objects.filter(setor_pai=setor)
            for filho in filhos:
                cargas_diretas += filho.cargas_presentes.filter(manifesto__data_estimada_retirada__lt=hoje).count()
        return cargas_diretas

    if patio_modelo:
        patio_modelo.quantidade_cargas = total_cargas_patio
        patio_modelo.metragem_ocupada = total_metragem_patio
        patio_modelo.percentual = percentual_patio
        patio_modelo.prazo_excedido = calcular_prazo_excedido(patio_modelo)

    return render(request, 'gestao_patio.html', {'patio_modelo': patio_modelo})


@login_required
def subpatios_list(request):
    patio_modelo = Setor.objects.filter(setor_pai__isnull=True).first()
    visual, numerico = _preparar_subpatios()
    return render(request, 'subpatios.html', {
        'patio_modelo': patio_modelo,
        'subpatios': visual,
        'subpatios_numerico': numerico,
    })


@login_required
def mapa_patio(request):
    patio_modelo = Setor.objects.filter(setor_pai__isnull=True).first()
    visual, numerico = _preparar_subpatios()

    total_cargas = sum(s.quantidade_cargas for s in numerico)
    total_metragem = sum(s.metragem_ocupada for s in numerico)
    capacidade_total = float(patio_modelo.capacidade_metragem or 0) if patio_modelo else 0
    percentual_total = round((total_metragem / capacidade_total) * 100, 1) if capacidade_total > 0 else 0

    context = {
        'patio_modelo': patio_modelo,
        'subpatios': visual,
        'subpatios_numerico': numerico,
        'total_cargas': total_cargas,
        'total_metragem': total_metragem,
        'percentual_total': percentual_total,
        'status_patio': definir_status_ocupacao(percentual_total),
    }
    return render(request, 'mapa_patio.html', context)


class PatioDetailView(GroupRequiredMixin, ListView):
    model = Carga
    template_name = 'setores/patio_detail.html'
    context_object_name = 'cargas'
    group_required = ['Administrador', 'Gestor']

    def get_queryset(self):
        self.patio = Setor.objects.get(pk=self.kwargs['pk'])
        return Carga.objects.filter(setor_atual=self.patio).exclude(movimentacoes__tipo='SAIDA').distinct().order_by('chassi')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patio'] = self.patio

        total_metragem = self.get_queryset().aggregate(total=Sum('metragem_unitaria'))['total'] or 0
        context['total_metragem'] = total_metragem

        capacidade = float(self.patio.capacidade_metragem or 0)
        context['percentual_ocupacao'] = round((float(total_metragem) / capacidade) * 100, 1) if capacidade > 0 else 0

        hoje = timezone.now().date()
        context['prazo_excedido'] = self.get_queryset().filter(manifesto__data_estimada_retirada__lt=hoje).count()

        return context


@login_required
def gerar_relatorio_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio_ocupacao_patio.pdf"'

    patio_modelo = Setor.objects.filter(setor_pai__isnull=True).first()
    subpatios_qs = list(Setor.objects.filter(setor_pai__isnull=False))
    subpatios = sorted(subpatios_qs, key=lambda x: extrair_numero_codigo(x.codigo))
    hoje = timezone.now().date()

    def calcular_dados(setor):
        cargas_diretas = setor.cargas_presentes.count()
        metragem_direta = setor.cargas_presentes.aggregate(total=Sum('metragem_unitaria'))['total'] or 0
        if setor.setor_pai is None:
            filhos = Setor.objects.filter(setor_pai=setor)
            for filho in filhos:
                cargas_diretas += filho.cargas_presentes.count()
                metragem_direta += filho.cargas_presentes.aggregate(total=Sum('metragem_unitaria'))['total'] or 0
        capacidade = float(setor.capacidade_metragem or 0)
        ocupado = float(metragem_direta or 0)
        percentual = round((ocupado / capacidade) * 100, 1) if capacidade > 0 else 0
        return cargas_diretas, ocupado, percentual

    def calcular_prazo_excedido(setor):
        if not setor:
            return 0
        cargas_diretas = setor.cargas_presentes.filter(manifesto__data_estimada_retirada__lt=hoje).count()
        if setor.setor_pai is None:
            filhos = Setor.objects.filter(setor_pai=setor)
            for filho in filhos:
                cargas_diretas += filho.cargas_presentes.filter(manifesto__data_estimada_retirada__lt=hoje).count()
        return cargas_diretas

    dados_patio = calcular_dados(patio_modelo) if patio_modelo else (0, 0, 0)
    prazo_excedido_patio = calcular_prazo_excedido(patio_modelo) if patio_modelo else 0

    doc = SimpleDocTemplate(response, pagesize=A4, title="Relatório de Ocupação")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Relatório de Ocupação do Pátio", styles['Title']))
    elements.append(Spacer(1, 1 * cm))

    if patio_modelo:
        data_modelo = [['Nome', 'Código', 'Carros', 'Ocupado (m²)', 'Capacidade (m²)', '% Ocupação', 'Prazo Excedido'],
                       [patio_modelo.nome, patio_modelo.codigo, dados_patio[0], f"{dados_patio[1]:.1f}", f"{patio_modelo.capacidade_metragem:.1f}", f"{dados_patio[2]:.1f}%", prazo_excedido_patio]]
        table_modelo = Table(data_modelo, colWidths=[3.5*cm, 2.5*cm, 1.5*cm, 2.5*cm, 2.5*cm, 2*cm, 3*cm])
        table_modelo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B1A2A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ]))
        elements.append(table_modelo)
        elements.append(Spacer(1, 1 * cm))

    elements.append(Paragraph("Ocupação por Subpátio", styles['Heading2']))
    data_sub = [['Código', 'Nome', 'Carros', 'Ocupado (m²)', 'Capacidade (m²)', '% Ocupação']]
    for sub in subpatios:
        carros, ocupado, perc = calcular_dados(sub)
        data_sub.append([sub.codigo, sub.nome, carros, f"{ocupado:.1f}", f"{sub.capacidade_metragem:.1f}", f"{perc:.1f}%"])

    table_sub = Table(data_sub, colWidths=[2*cm, 4*cm, 2*cm, 3.5*cm, 3*cm, 2.5*cm])
    table_sub.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B1A2A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
    ]))
    elements.append(table_sub)

    doc.build(elements)
    return response


class SetorListView(GroupRequiredMixin, ListView):
    model = Setor
    template_name = 'setores/setor_list.html'
    context_object_name = 'setores'
    group_required = ['Administrador']

class SetorCreateView(GroupRequiredMixin, CreateView):
    model = Setor
    fields = ['nome', 'codigo', 'setor_pai', 'capacidade_metragem']
    template_name = 'setores/setor_form.html'
    success_url = reverse_lazy('setor_list')
    group_required = ['Administrador']

class SetorUpdateView(GroupRequiredMixin, UpdateView):
    model = Setor
    fields = ['nome', 'codigo', 'setor_pai', 'capacidade_metragem']
    template_name = 'setores/setor_form.html'
    success_url = reverse_lazy('setor_list')
    group_required = ['Administrador']

class SetorDeleteView(GroupRequiredMixin, DeleteView):
    model = Setor
    template_name = 'setores/confirm_delete.html'
    success_url = reverse_lazy('setor_list')
    group_required = ['Administrador']