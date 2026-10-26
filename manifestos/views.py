from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from openpyxl import Workbook
from openpyxl.styles import Font
from .models import Manifesto, ItemManifesto
from .services import (
    importar_chassis_em_manifesto,
    extrair_dados_do_pdf,
    criar_chassis_provisorios,
    validar_chassi,
    limpar_chassi,
    listar_chassis_provisorios,
    atualizar_chassis_em_lote,
)
from cargas.models import FielDepositario, ModeloVeiculo, OperadorPortuario, Carga
from core.mixins import GroupRequiredMixin


class ManifestoListView(GroupRequiredMixin, ListView):
    model = Manifesto
    template_name = 'manifestos/manifesto_list.html'
    context_object_name = 'manifestos'
    group_required = ['Administrador', 'Gestor']

    def get_queryset(self):
        return Manifesto.objects.annotate(
            provisorios_count=Count('cargas', filter=Q(cargas__provisorio=True))
        ).order_by('-id')


class ManifestoCreateView(GroupRequiredMixin, CreateView):
    model = Manifesto
    fields = ['viagem', 'operador', 'dono_carga', 'numero_veiculos', 'metragem_total', 'status', 'data_estimada_retirada', 'data_real_retirada']
    template_name = 'manifestos/manifesto_form.html'
    success_url = reverse_lazy('manifesto_list')
    group_required = ['Administrador', 'Gestor']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['donos'] = FielDepositario.objects.all()
        context['operadores'] = OperadorPortuario.objects.all()
        context['modelos'] = ModeloVeiculo.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        bls = self.request.POST.getlist('bl')
        modelos_ids = self.request.POST.getlist('modelo_id')
        quantidades = self.request.POST.getlist('quantidade')
        chassis_lists = self.request.POST.getlist('lista_chassis')

        total_metragem = 0.0
        total_veiculos = 0
        operador = self.object.operador

        for i in range(len(modelos_ids)):
            if modelos_ids[i]:
                modelo = ModeloVeiculo.objects.get(id=int(modelos_ids[i]))
                quantidade = int(quantidades[i]) if quantidades[i] else 1
                bl = bls[i] if i < len(bls) else ''

                lista_limpa = [c.strip() for c in chassis_lists[i].replace(',', '\n').splitlines() if c.strip()]

                total_metragem += float(modelo.metragem_m2) * quantidade
                total_veiculos += quantidade

                ItemManifesto.objects.create(
                    manifesto=self.object,
                    modelo=modelo,
                    quantidade=quantidade,
                    lista_chassis="\n".join(lista_limpa)
                )

                for chassi in lista_limpa:
                    Carga.objects.create(
                        bl=bl, chassi=chassi, manifesto=self.object,
                        operador=operador, dono=self.object.dono_carga,
                        modelo=modelo, metragem_unitaria=modelo.metragem_m2,
                        origem=Carga.Origem.MANUAL,
                    )

        self.object.numero_veiculos = total_veiculos
        self.object.metragem_total = total_metragem
        self.object.save()

        return response


class ManifestoUpdateView(GroupRequiredMixin, UpdateView):
    model = Manifesto
    fields = ['viagem', 'operador', 'dono_carga', 'numero_veiculos', 'metragem_total', 'status', 'data_estimada_retirada', 'data_real_retirada']
    template_name = 'manifestos/manifesto_form.html'
    success_url = reverse_lazy('manifesto_list')
    group_required = ['Administrador', 'Gestor']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['donos'] = FielDepositario.objects.all()
        context['operadores'] = OperadorPortuario.objects.all()
        context['modelos'] = ModeloVeiculo.objects.all()
        return context


class ManifestoDeleteView(GroupRequiredMixin, DeleteView):
    model = Manifesto
    template_name = 'manifestos/confirm_delete.html'
    success_url = reverse_lazy('manifesto_list')
    group_required = ['Administrador', 'Gestor']


@login_required
def preview_manifesto(request):
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)

    bls = request.POST.getlist('bl')
    modelos_ids = request.POST.getlist('modelo_id')
    quantidades = request.POST.getlist('quantidade')
    chassis_lists = request.POST.getlist('lista_chassis')

    itens_preview = []
    total_veiculos = 0
    total_metragem = 0
    chassis_duplicados_form = []
    chassis_todos = []

    for i in range(len(modelos_ids)):
        if not modelos_ids[i]:
            continue

        modelo = ModeloVeiculo.objects.filter(id=int(modelos_ids[i])).first()
        if not modelo:
            continue

        quantidade = int(quantidades[i]) if i < len(quantidades) and quantidades[i] else 1
        bl = bls[i] if i < len(bls) else ''

        lista_limpa = []
        if i < len(chassis_lists):
            lista_limpa = [c.strip() for c in chassis_lists[i].replace(',', '\n').splitlines() if c.strip()]

        metragem_item = float(modelo.metragem_m2) * quantidade
        total_veiculos += quantidade
        total_metragem += metragem_item

        for chassi in lista_limpa:
            if chassi in chassis_todos:
                chassis_duplicados_form.append(chassi)
            chassis_todos.append(chassi)

        itens_preview.append({
            'bl': bl,
            'modelo': f"{modelo.fabricante} {modelo.modelo} ({modelo.ano})",
            'quantidade': quantidade,
            'chassis': lista_limpa,
            'metragem': round(metragem_item, 2),
            'metragem_unit': float(modelo.metragem_m2),
        })

    chassis_existentes = []
    if chassis_todos:
        existentes_qs = Carga.objects.filter(chassi__in=chassis_todos).values_list('chassi', flat=True)
        chassis_existentes = list(existentes_qs)

    return JsonResponse({
        'sucesso': True,
        'itens': itens_preview,
        'total_veiculos': total_veiculos,
        'total_metragem': round(total_metragem, 2),
        'chassis_duplicados_form': chassis_duplicados_form,
        'chassis_existentes': chassis_existentes,
        'tem_erros': bool(chassis_duplicados_form or chassis_existentes),
    })


# ============================================================
# IMPORTAÇÃO DE LISTA (5.1)
# ============================================================
@login_required
def importar_chassis_lista(request, manifesto_id):
    manifesto = get_object_or_404(Manifesto, pk=manifesto_id)

    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            messages.error(request, "❌ Nenhum arquivo enviado.")
            return redirect('importar_chassis_lista', manifesto_id=manifesto_id)

        try:
            resultado = importar_chassis_em_manifesto(manifesto, arquivo)

            msg = f"✅ Importação concluída! {resultado['criados']} chassis cadastrados."
            if resultado['duplicados']:
                msg += f" | {len(resultado['duplicados'])} já existiam."
            messages.success(request, msg)

            if resultado['erros']:
                for err in resultado['erros'][:5]:
                    messages.warning(request, f"⚠️ {err}")

            return redirect('manifesto_list')
        except Exception as e:
            messages.error(request, f"❌ Erro ao processar arquivo: {e}")
            return redirect('importar_chassis_lista', manifesto_id=manifesto_id)

    return render(request, 'manifestos/importar_chassis.html', {
        'manifesto': manifesto,
    })


# ============================================================
# IMPORTAÇÃO DE PDF (5.2)
# ============================================================
@login_required
def importar_pdf(request, manifesto_id):
    manifesto = get_object_or_404(Manifesto, pk=manifesto_id)
    modelos = ModeloVeiculo.objects.all().order_by('fabricante', 'modelo')

    if request.method == 'POST':
        if 'arquivo_pdf' in request.FILES:
            arquivo = request.FILES['arquivo_pdf']
            try:
                dados = extrair_dados_do_pdf(arquivo)
                if not dados['sucesso']:
                    messages.error(request, f"❌ {dados['erro']}")
                    return redirect('importar_pdf', manifesto_id=manifesto_id)

                return render(request, 'manifestos/importar_pdf.html', {
                    'manifesto': manifesto,
                    'modelos': modelos,
                    'dados': dados,
                    'etapa': 'preview',
                })
            except Exception as e:
                messages.error(request, f"❌ Erro ao processar PDF: {e}")
                return redirect('importar_pdf', manifesto_id=manifesto_id)

        elif request.POST.get('acao') == 'confirmar_vin':
            chassis = request.POST.getlist('chassis_selecionados')
            criados = 0
            duplicados = []

            with transaction.atomic():
                for chassi in chassis:
                    chassi_limpo = limpar_chassi(chassi)
                    if not validar_chassi(chassi_limpo):
                        continue
                    if Carga.objects.filter(chassi=chassi_limpo).exists():
                        duplicados.append(chassi_limpo)
                        continue
                    Carga.objects.create(
                        bl=None, chassi=chassi_limpo, manifesto=manifesto,
                        operador=manifesto.operador, dono=manifesto.dono_carga,
                        modelo=None, metragem_unitaria=0,
                        origem=Carga.Origem.PDF, provisorio=False,
                    )
                    criados += 1

                total_cargas = manifesto.cargas.count()
                manifesto.numero_veiculos = total_cargas
                manifesto.save(update_fields=['numero_veiculos'])

            msg = f"✅ {criados} chassis importados do PDF."
            if duplicados:
                msg += f" | {len(duplicados)} já existiam."
            messages.success(request, msg)
            return redirect('manifesto_list')

        elif request.POST.get('acao') == 'criar_provisorios':
            modelo_id = request.POST.get('modelo_id')
            quantidade = int(request.POST.get('quantidade', 0))

            if not modelo_id or quantidade <= 0:
                messages.error(request, "❌ Selecione um modelo e informe a quantidade.")
                return redirect('importar_pdf', manifesto_id=manifesto_id)

            modelo = get_object_or_404(ModeloVeiculo, pk=modelo_id)
            criados = criar_chassis_provisorios(manifesto, modelo, quantidade)
            messages.success(request, f"✅ {len(criados)} chassis provisórios criados. Substitua-os pelos reais depois.")
            return redirect('editar_chassis_provisorios', manifesto_id=manifesto_id)

    return render(request, 'manifestos/importar_pdf.html', {
        'manifesto': manifesto,
        'modelos': modelos,
        'etapa': 'upload',
    })


# ============================================================
# EDIÇÃO DE UM CHASSI PROVISÓRIO (individual)
# ============================================================
@login_required
def editar_chassi_provisorio(request, carga_id):
    carga = get_object_or_404(Carga, pk=carga_id)

    if request.method == 'POST':
        novo_chassi = limpar_chassi(request.POST.get('novo_chassi', ''))
        if not validar_chassi(novo_chassi):
            messages.error(request, "❌ Chassi inválido.")
        elif Carga.objects.filter(chassi=novo_chassi).exclude(pk=carga.id).exists():
            messages.error(request, f"❌ Já existe uma carga com o chassi {novo_chassi}.")
        else:
            carga.chassi = novo_chassi
            carga.provisorio = False
            carga.origem = Carga.Origem.MANUAL
            carga.save(update_fields=['chassi', 'provisorio', 'origem'])
            messages.success(request, f"✅ Chassi atualizado para {novo_chassi}.")
            return redirect('manifesto_list')
        return redirect('editar_chassi_provisorio', carga_id=carga.id)

    return render(request, 'manifestos/editar_chassi.html', {'carga': carga})


# ============================================================
# EDIÇÃO EM MASSA (5.3)
# ============================================================
@login_required
def editar_chassis_provisorios(request, manifesto_id):
    manifesto = get_object_or_404(Manifesto, pk=manifesto_id)
    provisorios = list(listar_chassis_provisorios(manifesto))

    if request.method == 'POST':
        modo = request.POST.get('modo', 'individual')

        if modo == 'colar':
            lista_colada = request.POST.get('lista_colada', '')
            novos = [limpar_chassi(l) for l in lista_colada.replace(',', '\n').splitlines() if l.strip()]

            chassis_dict = {}
            for i, carga in enumerate(provisorios):
                if i < len(novos):
                    chassis_dict[carga.id] = novos[i]

            resultado = atualizar_chassis_em_lote(chassis_dict)

            msg = f"✅ {resultado['atualizados']} chassi(s) atualizados via lista."
            if len(novos) < len(provisorios):
                msg += f" | {len(novos)} de {len(provisorios)} informados."
            messages.success(request, msg)

            if resultado['erros']:
                for err in resultado['erros'][:8]:
                    messages.warning(request, f"⚠️ {err}")

            return redirect('editar_chassis_provisorios', manifesto_id=manifesto_id)

        else:
            chassis_dict = {}
            for key, value in request.POST.items():
                if key.startswith('chassi_') and key != 'chassi_':
                    carga_id_str = key.replace('chassi_', '')
                    try:
                        chassis_dict[int(carga_id_str)] = value
                    except ValueError:
                        pass

            resultado = atualizar_chassis_em_lote(chassis_dict)

            msg = f"✅ {resultado['atualizados']} chassi(s) atualizados."
            if resultado['vazios']:
                msg += f" | {resultado['vazios']} em branco."
            if resultado['iguais']:
                msg += f" | {resultado['iguais']} sem alteração."
            messages.success(request, msg)

            if resultado['erros']:
                for err in resultado['erros'][:8]:
                    messages.warning(request, f"⚠️ {err}")

            return redirect('editar_chassis_provisorios', manifesto_id=manifesto_id)

    return render(request, 'manifestos/editar_provisorios.html', {
        'manifesto': manifesto,
        'provisorios': provisorios,
        'total': len(provisorios),
    })


def exportar_manifestos_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Manifestos"

    headers = ['ID', 'BL', 'Navio', 'Programação', 'Operador Portuário', 'Fiel Depositário', 'Nº Veículos', 'Previsão de Saída', 'Status']
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    manifestos = Manifesto.objects.select_related('viagem__navio', 'operador', 'dono_carga').all()
    for m in manifestos:
        bl = m.cargas.first().bl if m.cargas.exists() else ""
        ws.append([
            m.id, bl, m.viagem.navio.nome, m.viagem.numero_viagem,
            m.operador.nome_empresa if m.operador else "",
            m.dono_carga.nome_completo if m.dono_carga else "",
            m.numero_veiculos, m.data_estimada_retirada, m.get_status_display()
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="manifestos.xlsx"'
    wb.save(response)
    return response