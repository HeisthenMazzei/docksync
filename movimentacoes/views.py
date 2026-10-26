from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
import json

from .models import Movimentacao, TrabalhadorPortuario, registrar_movimentacao
from cargas.models import Carga
from setores.models import Setor
from navios.models import Navio, Viagem
from manifestos.models import Manifesto
from core.mixins import GroupRequiredMixin


# ==========================================
# TRABALHADOR PORTUÁRIO — CRUD
# ==========================================
class TrabalhadorPortuarioListView(GroupRequiredMixin, ListView):
    model = TrabalhadorPortuario
    template_name = 'cadastro/trabalhador_list.html'
    context_object_name = 'trabalhadores'
    group_required = ['Administrador']


class TrabalhadorPortuarioCreateView(GroupRequiredMixin, CreateView):
    model = TrabalhadorPortuario
    fields = ['nome_completo', 'matricula']
    template_name = 'cadastro/trabalhador_form.html'
    success_url = reverse_lazy('trabalhador_list')
    group_required = ['Administrador']


class TrabalhadorPortuarioUpdateView(GroupRequiredMixin, UpdateView):
    model = TrabalhadorPortuario
    fields = ['nome_completo', 'matricula']
    template_name = 'cadastro/trabalhador_form.html'
    success_url = reverse_lazy('trabalhador_list')
    group_required = ['Administrador']


class TrabalhadorPortuarioDeleteView(GroupRequiredMixin, DeleteView):
    model = TrabalhadorPortuario
    template_name = 'cadastro/confirm_delete.html'
    success_url = reverse_lazy('trabalhador_list')
    group_required = ['Administrador']


# ==========================================
# MOVIMENTAÇÃO INDIVIDUAL
# ==========================================
def registrar_movimentacao_view(request):
    if request.method == 'POST':
        chassi = request.POST.get('chassi')
        tipo = request.POST.get('tipo')
        setor_destino_id = request.POST.get('setor_destino')
        setor_origem_id = request.POST.get('setor_origem')
        trabalhador_id = request.POST.get('trabalhador_id')

        latitude_origem = request.POST.get('latitude_origem', '')
        longitude_origem = request.POST.get('longitude_origem', '')
        latitude_destino = request.POST.get('latitude_destino', '')
        longitude_destino = request.POST.get('longitude_destino', '')

        latitude_origem = float(latitude_origem) if latitude_origem else None
        longitude_origem = float(longitude_origem) if longitude_origem else None
        latitude_destino = float(latitude_destino) if latitude_destino else None
        longitude_destino = float(longitude_destino) if longitude_destino else None

        try:
            carga = Carga.objects.get(chassi=chassi)
            trabalhador = TrabalhadorPortuario.objects.get(id=trabalhador_id)
            setor_origem = Setor.objects.get(id=setor_origem_id) if setor_origem_id else None
            setor_destino = Setor.objects.get(id=setor_destino_id) if setor_destino_id else None
            foto = request.FILES.get('fotografia_chassi')

            # Anti-duplicidade: mesmo chassi nos últimos 30 min pelo mesmo trabalhador
            agora = timezone.now()
            janela = agora - timedelta(minutes=30)

            mov_recente = Movimentacao.objects.filter(
                carga=carga,
                data_hora__gte=janela,
                trabalhador=trabalhador,
            ).exists()

            if mov_recente:
                messages.warning(
                    request,
                    f"⚠️ O veículo {chassi} já foi movimentado nos últimos 30 minutos "
                    f"por {trabalhador.nome_completo}. Registrando mesmo assim."
                )

            registrar_movimentacao(
                carga=carga,
                tipo=tipo,
                setor_origem=setor_origem,
                setor_destino=setor_destino,
                trabalhador=trabalhador,
                fotografia_chassi=foto,
                latitude_origem=latitude_origem,
                longitude_origem=longitude_origem,
                latitude_destino=latitude_destino,
                longitude_destino=longitude_destino,
                localizacao_destino=request.POST.get('localizacao_destino', '')
            )
            messages.success(request, f"✅ Movimentação registrada com sucesso para o chassi {chassi}!")

        except Carga.DoesNotExist:
            messages.error(request, "❌ Chassi não encontrado. Verifique o código.")
        except TrabalhadorPortuario.DoesNotExist:
            messages.error(request, "❌ Selecione um trabalhador portuário válido.")
        except DjangoValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)
            messages.error(request, f"⚠️ {msg}")
        except Exception as e:
            messages.error(request, f"❌ Erro no sistema: {e}")

        return redirect('registrar_movimentacao')

    navios = Navio.objects.all()
    setores = Setor.objects.all()
    trabalhadores = TrabalhadorPortuario.objects.all()
    return render(request, 'registrar_movimentacao.html', {
        'navios': navios,
        'setores': setores,
        'trabalhadores': trabalhadores
    })


# ==========================================
# MOVIMENTAÇÃO EM SÉRIE (LOTE)
# ==========================================
def registrar_movimentacao_lote_view(request):
    """
    Tela de registro em série. Aceita:
    - GET: renderiza o formulário
    - POST: processa a lista de chassis (recebida via JSON no campo 'chassis')
    """
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        setor_destino_id = request.POST.get('setor_destino')
        setor_origem_id = request.POST.get('setor_origem')
        trabalhador_id = request.POST.get('trabalhador_id')
        chassis_json = request.POST.get('chassis', '[]')

        # Parse da lista de chassis
        try:
            chassis_lista = json.loads(chassis_json)
            if not isinstance(chassis_lista, list):
                raise ValueError('Lista deve ser um array')
        except Exception as e:
            return JsonResponse({'sucesso': False, 'erro': f'Lista de chassis inválida: {e}'})

        # Valida o trabalhador
        trabalhador = TrabalhadorPortuario.objects.filter(id=trabalhador_id).first()
        if not trabalhador:
            return JsonResponse({'sucesso': False, 'erro': 'Trabalhador portuário inválido'})

        # Setores
        setor_origem = Setor.objects.filter(id=setor_origem_id).first() if setor_origem_id else None
        setor_destino = Setor.objects.filter(id=setor_destino_id).first() if setor_destino_id else None

        # Processa cada chassi
        resultados = []
        for chassi_original in chassis_lista:
            chassi = str(chassi_original).strip().upper()
            resultado = {
                'chassi': chassi,
                'sucesso': False,
                'mensagem': '',
            }

            try:
                carga = Carga.objects.get(chassi=chassi)
                registrar_movimentacao(
                    carga=carga,
                    tipo=tipo,
                    setor_origem=setor_origem,
                    setor_destino=setor_destino,
                    trabalhador=trabalhador,
                    localizacao_destino=f"Registro em série — {timezone.now().strftime('%d/%m/%Y %H:%M')}"
                )
                resultado['sucesso'] = True
                resultado['mensagem'] = 'Movimentação registrada'
            except Carga.DoesNotExist:
                resultado['mensagem'] = 'Chassi não encontrado no sistema'
            except DjangoValidationError as e:
                msg = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)
                resultado['mensagem'] = msg
            except Exception as e:
                resultado['mensagem'] = f'Erro: {e}'

            resultados.append(resultado)

        sucessos = sum(1 for r in resultados if r['sucesso'])
        erros = len(resultados) - sucessos

        return JsonResponse({
            'sucesso': True,
            'resultados': resultados,
            'total': len(resultados),
            'sucessos': sucessos,
            'erros': erros,
        })

    # GET — Renderiza o formulário
    navios = Navio.objects.all()
    setores = Setor.objects.all()
    trabalhadores = TrabalhadorPortuario.objects.all()
    return render(request, 'registrar_movimentacao_lote.html', {
        'navios': navios,
        'setores': setores,
        'trabalhadores': trabalhadores,
    })


# ==========================================
# AJAX / ENDPOINTS DE APOIO
# ==========================================
def buscar_dados_por_chassi(request):
    chassi = request.GET.get('chassi', '').strip()
    if not chassi:
        return JsonResponse({'erro': 'Chassi não informado'}, status=400)

    try:
        carga = Carga.objects.select_related(
            'manifesto__viagem__navio', 'manifesto__viagem', 'setor_atual', 'operador'
        ).get(chassi=chassi)
    except Carga.DoesNotExist:
        return JsonResponse({'erro': 'Chassi não encontrado'}, status=404)

    esta_no_patio = carga.setor_atual is not None
    tipos_permitidos = ['INTERNA', 'SAIDA'] if esta_no_patio else ['CHEGADA']

    return JsonResponse({
        'id': carga.id,
        'chassi': carga.chassi,
        'bl': carga.bl or "",
        'navio_id': carga.manifesto.viagem.navio.id,
        'navio_nome': carga.manifesto.viagem.navio.nome,
        'viagem_id': carga.manifesto.viagem.id,
        'viagem_numero': carga.manifesto.viagem.numero_viagem,
        'manifesto_id': carga.manifesto.id,
        'setor_origem_id': carga.setor_atual.id if carga.setor_atual else None,
        'setor_origem_nome': carga.setor_atual.nome if carga.setor_atual else "Fora do Porto",
        'operador_nome': carga.operador.nome_empresa if carga.operador else "",
        'esta_no_patio': esta_no_patio,
        'tipos_permitidos': tipos_permitidos,
    })


class MovimentacaoListView(GroupRequiredMixin, ListView):
    model = Movimentacao
    template_name = 'movimentacoes/movimentacao_list.html'
    context_object_name = 'movimentacoes'
    group_required = ['Administrador', 'Gestor']


def carregar_viagens(request):
    navio_id = request.GET.get('navio_id')
    viagens = Viagem.objects.filter(navio_id=navio_id).order_by('-data_prevista_chegada')
    options = "".join([f'<option value="{v.id}">{v.numero_viagem}</option>' for v in viagens])
    return HttpResponse(options)


def carregar_bls(request):
    viagem_id = request.GET.get('viagem_id')
    bls = Carga.objects.filter(manifesto__viagem_id=viagem_id).exclude(bl__isnull=True).exclude(bl='').values_list('bl', flat=True).distinct()
    options = "".join([f'<option value="{bl}">{bl}</option>' for bl in bls])
    return HttpResponse(options)


def carregar_manifestos(request):
    viagem_id = request.GET.get('viagem_id')
    manifestos = Manifesto.objects.filter(viagem_id=viagem_id)
    options = "".join([f'<option value="{m.id}">Manifesto {m.id}</option>' for m in manifestos])
    return HttpResponse(options)


def carregar_cargas(request):
    bl = request.GET.get('bl')
    cargas = Carga.objects.filter(bl=bl)
    options = "".join([f'<option value="{c.chassi}">{c.chassi}</option>' for c in cargas])
    return HttpResponse(options)


def exportar_movimentacoes_excel(request):
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Movimentações"
    headers = ['Data/Hora', 'Chassi', 'Tipo', 'Setor Origem', 'Setor Destino', 'Trabalhador Portuário', 'Foto']
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    movimentacoes = Movimentacao.objects.select_related('carga', 'setor_origem', 'setor_destino', 'trabalhador').all()
    for mov in movimentacoes:
        ws.append([
            mov.data_hora.strftime('%d/%m/%Y %H:%M'),
            mov.carga.chassi,
            mov.get_tipo_display(),
            mov.setor_origem.nome if mov.setor_origem else "",
            mov.setor_destino.nome if mov.setor_destino else "",
            mov.trabalhador.nome_completo if mov.trabalhador else "",
            "Sim" if mov.fotografia_chassi else "Não"
        ])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="movimentacoes.xlsx"'
    wb.save(response)
    return response