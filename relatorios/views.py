from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from openpyxl import Workbook
from openpyxl.styles import Font
from manifestos.models import Manifesto
from cargas.models import Carga
from movimentacoes.models import Movimentacao
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from django.db.models import Sum, Count
from django.utils import timezone

# Estilo para quebrar linhas em nomes longos
style_nome = ParagraphStyle(
    'Nome',
    fontSize=8,
    leading=10
)

@login_required
def relatorio_view(request):
    return render(request, 'relatorios/relatorios.html')

@login_required
def exportar_excel_view(request):
    tipo = request.GET.get('tipo', 'movimentacoes')
    data_inicio_str = request.GET.get('data_inicio', '')
    data_fim_str = request.GET.get('data_fim', '')

    if data_inicio_str:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
    else:
        data_inicio = datetime.now().date() - timedelta(days=30)
    
    if data_fim_str:
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    else:
        data_fim = datetime.now().date()

    wb = Workbook()
    ws = wb.active

    if tipo == 'manifestos':
        ws.title = "Manifestos"
        headers = ['ID', 'BL', 'Navio', 'Programação', 'Operador', 'Fiel Depositário', 'Nº Veículos', 'Previsão de Saída', 'Status']
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        manifestos = Manifesto.objects.filter(viagem__data_prevista_chegada__range=[data_inicio, data_fim])
        for m in manifestos:
            bl = m.cargas.first().bl if m.cargas.exists() else ""
            ws.append([
                m.id, bl, m.viagem.navio.nome, m.viagem.numero_viagem,
                m.operador.nome_empresa if m.operador else "",
                m.dono_carga.nome_completo if m.dono_carga else "",
                m.numero_veiculos, m.data_estimada_retirada, m.get_status_display()
            ])

    elif tipo == 'cargas':
        ws.title = "Cargas"
        headers = ['BL', 'Chassi', 'Operador', 'Fiel', 'Modelo', 'Ano', 'Metragem', 'Localização']
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        cargas = Carga.objects.filter(manifesto__viagem__data_prevista_chegada__range=[data_inicio, data_fim])
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

    else:  # Movimentações
        ws.title = "Movimentações"
        headers = ['Data/Hora', 'Chassi', 'Tipo', 'Setor Origem', 'Setor Destino', 'Trabalhador']
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        movimentacoes = Movimentacao.objects.filter(data_hora__date__range=[data_inicio, data_fim])
        for mov in movimentacoes:
            ws.append([
                mov.data_hora.strftime('%d/%m/%Y %H:%M'),
                mov.carga.chassi,
                mov.get_tipo_display(),
                mov.setor_origem.nome if mov.setor_origem else "",
                mov.setor_destino.nome if mov.setor_destino else "",
                mov.trabalhador.nome_completo if mov.trabalhador else ""
            ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="relatorio_{tipo}.xlsx"'
    wb.save(response)
    return response

@login_required
def gerar_relatorio_saidas_pdf(request):
    data_inicio_str = request.GET.get('data_inicio', '')
    data_fim_str = request.GET.get('data_fim', '')

    if data_inicio_str:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
    else:
        data_inicio = datetime.now().date() - timedelta(days=7)
    
    if data_fim_str:
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    else:
        data_fim = datetime.now().date()

    movimentacoes = Movimentacao.objects.filter(tipo='SAIDA', data_hora__date__range=[data_inicio, data_fim]).select_related('carga', 'setor_origem', 'trabalhador').order_by('-data_hora')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_saidas_{data_inicio}_{data_fim}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4), title="Relatório de Saídas")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Relatório de Saídas ({data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')})", styles['Title']))
    elements.append(Spacer(1, 1 * cm))

    data = [['Data/Hora', 'Chassi', 'BL', 'Setor Origem', 'Trabalhador Responsável']]

    for mov in movimentacoes:
        data.append([
            mov.data_hora.strftime('%d/%m/%Y %H:%M'),
            mov.carga.chassi,
            mov.carga.bl or "-",
            mov.setor_origem.nome if mov.setor_origem else "-",
            mov.trabalhador.nome_completo if mov.trabalhador else "-"
        ])

    col_widths = [4*cm, 4*cm, 3*cm, 4*cm, 6*cm]
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B1A2A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
    ]))
    elements.append(table)

    doc.build(elements)
    return response

@login_required
def relatorio_ocupacao_operadores_pdf(request):
    dados = Carga.objects.exclude(operador__isnull=True).values(
        'operador__nome_empresa'
    ).annotate(
        total_cargas=Count('id'),
        total_metragem=Sum('metragem_unitaria')
    ).order_by('-total_metragem')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio_ocupacao_operadores.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4), title="Ocupação por Operador")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Relatório de Ocupação por Operador", styles['Title']))
    elements.append(Spacer(1, 1 * cm))

    data = [['Operador', 'Qtd de Veículos', 'Metragem Ocupada (m²)']]
    for d in dados:
        data.append([
            Paragraph(d['operador__nome_empresa'], style_nome),
            d['total_cargas'],
            f"{d['total_metragem']:.2f}"
        ])

    col_widths = [10*cm, 4*cm, 5*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B1A2A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)

    doc.build(elements)
    return response

@login_required
def relatorio_ranking_modelos_pdf(request):
    dados = Carga.objects.exclude(modelo__isnull=True).values(
        'modelo__fabricante', 'modelo__modelo', 'modelo__ano'
    ).annotate(total=Count('id')).order_by('-total')[:10]

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio_ranking_modelos.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, title="Ranking de Modelos")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Ranking de Modelos de Veículos (Top 10)", styles['Title']))
    elements.append(Spacer(1, 1 * cm))

    data = [['Fabricante', 'Modelo', 'Ano', 'Qtd de Veículos']]
    for d in dados:
        data.append([
            d['modelo__fabricante'],
            d['modelo__modelo'],
            d['modelo__ano'],
            d['total']
        ])

    col_widths = [5*cm, 5*cm, 3*cm, 4*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B1A2A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
    ]))
    elements.append(table)

    doc.build(elements)
    return response

@login_required
def relatorio_prazos_excedentes_pdf(request):
    hoje = timezone.now().date()
    cargas = Carga.objects.filter(
        setor_atual__isnull=False,
        manifesto__data_estimada_retirada__lt=hoje
    ).select_related('manifesto', 'setor_atual', 'operador').order_by('manifesto__data_estimada_retirada')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio_prazos_excedentes.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4), title="Prazos Excedentes")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Lista de Veículos com Prazo de Saída Excedido", styles['Title']))
    elements.append(Spacer(1, 1 * cm))

    data = [['Chassi', 'BL', 'Operador', 'Setor', 'Previsão de Saída']]
    for c in cargas:
        data.append([
            c.chassi,
            c.bl or "-",
            Paragraph(c.operador.nome_empresa if c.operador else "-", style_nome),
            c.setor_atual.nome if c.setor_atual else "-",
            c.manifesto.data_estimada_retirada.strftime('%d/%m/%Y') if c.manifesto.data_estimada_retirada else "-"
        ])

    col_widths = [4*cm, 3*cm, 5*cm, 3*cm, 4*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FEF2F2')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)

    doc.build(elements)
    return response