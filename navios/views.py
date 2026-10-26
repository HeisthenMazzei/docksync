from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from .models import Navio, Viagem
from cargas.models import OperadorPortuario
from core.mixins import GroupRequiredMixin
import pandas as pd
from datetime import datetime
import os


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


# ==========================================
# NAVIOS
# ==========================================
class NavioListView(GroupRequiredMixin, ListView):
    model = Navio
    template_name = 'navios/navio_list.html'
    context_object_name = 'navios'
    group_required = ['Administrador', 'Gestor']

    def get_queryset(self):
        return Navio.objects.annotate(
            total_viagens=Count('viagens', distinct=True),
            total_cadastrado=Count('viagens__manifestos__cargas', distinct=True),
            total_previsto=Sum('viagens__quantidade_prevista'),
            total_carga=Count(
                'viagens__manifestos__cargas',
                filter=Q(viagens__sentido='CARGA'),
                distinct=True
            ),
            total_descarga=Count(
                'viagens__manifestos__cargas',
                filter=Q(viagens__sentido='DESCARGA'),
                distinct=True
            ),
        ).order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calcula a diferença para cada navio
        for navio in context['navios']:
            previsto = navio.total_previsto or 0
            cadastrado = navio.total_cadastrado or 0
            navio.diferenca = previsto - cadastrado
            navio.abs_diferenca = abs(navio.diferenca)

        return context


class NavioCreateView(GroupRequiredMixin, CreateView):
    model = Navio
    fields = ['nome', 'imo', 'mmsi']
    template_name = 'navios/navio_form.html'
    success_url = reverse_lazy('navio_list')
    group_required = ['Administrador', 'Gestor']


# ==========================================
# PROGRAMAÇÃO DE NAVIOS
# ==========================================
class ViagemListView(GroupRequiredMixin, ListView):
    model = Viagem
    template_name = 'navios/viagem_list.html'
    context_object_name = 'viagens'
    group_required = ['Administrador', 'Gestor']

    def get_queryset(self):
        atualizar_status_por_data()
        qs = super().get_queryset().select_related('navio', 'operador_portuario')

        filtro = self.request.GET.get('status', 'todos')

        if filtro == 'atracados':
            qs = qs.filter(status__in=['ATRACADO', 'DESCARREGANDO', 'CARREGANDO'])
        elif filtro == 'fundeados':
            qs = qs.filter(status='FUNDEADO')
        elif filtro == 'esperados':
            qs = qs.filter(status='AGUARDANDO_CHEGADA')
        elif filtro == 'finalizados':
            qs = qs.filter(status='FINALIZADO')

        return qs.order_by('data_prevista_chegada')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtro_status'] = self.request.GET.get('status', 'todos')

        viagens = context['viagens']
        for v in viagens:
            v.qtd_cadastrada = v.manifestos.aggregate(
                total=Count('cargas', distinct=True)
            )['total'] or 0
            v.diferenca = (v.quantidade_prevista or 0) - v.qtd_cadastrada

        return context


class ViagemCreateView(GroupRequiredMixin, CreateView):
    model = Viagem
    fields = ['navio', 'numero_viagem', 'operador_portuario', 'sentido', 'quantidade_prevista', 'psp', 'data_prevista_chegada', 'data_chegada_real', 'data_desatracacao', 'bercario_atracacao', 'agencia', 'status']
    template_name = 'navios/viagem_form.html'
    success_url = reverse_lazy('viagem_list')
    group_required = ['Administrador', 'Gestor']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['operadores'] = OperadorPortuario.objects.all()
        return context


class ViagemUpdateView(GroupRequiredMixin, UpdateView):
    model = Viagem
    fields = ['navio', 'numero_viagem', 'operador_portuario', 'sentido', 'quantidade_prevista', 'psp', 'data_prevista_chegada', 'data_chegada_real', 'data_desatracacao', 'bercario_atracacao', 'agencia', 'status']
    template_name = 'navios/viagem_form.html'
    success_url = reverse_lazy('viagem_list')
    group_required = ['Administrador', 'Gestor']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['operadores'] = OperadorPortuario.objects.all()
        return context


class ViagemDeleteView(GroupRequiredMixin, DeleteView):
    model = Viagem
    template_name = 'navios/confirm_delete.html'
    success_url = reverse_lazy('viagem_list')
    group_required = ['Administrador', 'Gestor']


# ==========================================
# IMPORTAÇÃO DE LINEUP
# ==========================================
def converter_data(valor):
    if pd.isna(valor) or str(valor).strip() == '':
        return None
    try:
        if hasattr(valor, 'to_pydatetime'):
            return valor.to_pydatetime().date()
        if isinstance(valor, datetime):
            return valor.date()
        text = str(valor).strip()
        for fmt in ['%d/%m/%Y', '%d/%m/%Y %H:%M', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y', '%d/%m/%Y %H:%M:%S']:
            try:
                return datetime.strptime(text.split(' ')[0], fmt).date()
            except ValueError:
                continue
    except:
        pass
    return None


def limpar_valor(valor):
    if pd.isna(valor):
        return ''
    return str(valor).strip()


def encontrar_coluna(df, *nomes):
    for col in df.columns:
        col_limpa = str(col).strip().lower()
        for nome in nomes:
            if nome.lower() in col_limpa:
                return col
    return None


def importar_lineup_arquivo(request):
    if request.method == 'POST' and request.FILES.get('arquivo_lineup'):
        arquivo = request.FILES['arquivo_lineup']
        try:
            pasta_destino = '/app/lineup/'
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            caminho_arquivo = os.path.join(pasta_destino, 'Lineup.xlsx')
            with open(caminho_arquivo, 'wb+') as destination:
                for chunk in arquivo.chunks():
                    destination.write(chunk)

            df = pd.read_excel(caminho_arquivo, header=0)

            idx_programacao = encontrar_coluna(df, 'programação', 'programacao')
            idx_berco = encontrar_coluna(df, 'berço', 'berco')
            idx_navio = encontrar_coluna(df, 'navio')
            idx_psp = encontrar_coluna(df, 'psp')
            idx_eta = encontrar_coluna(df, 'fundeio', 'eta')
            idx_etb = encontrar_coluna(df, 'atracação', 'etb')
            idx_ets = encontrar_coluna(df, 'desatracação', 'ets')
            idx_agencia = encontrar_coluna(df, 'agência', 'agencia')

            criados = 0
            atualizados = 0

            for index, row in df.iterrows():
                try:
                    navio_nome = limpar_valor(row.get(idx_navio)) if idx_navio else ''
                    if not navio_nome:
                        continue

                    programacao = limpar_valor(row.get(idx_programacao)) if idx_programacao else ''
                    berco = limpar_valor(row.get(idx_berco)) if idx_berco else ''
                    psp = limpar_valor(row.get(idx_psp)) if idx_psp else ''
                    agencia = limpar_valor(row.get(idx_agencia)) if idx_agencia else ''

                    data_eta = converter_data(row.get(idx_eta)) if idx_eta else None
                    data_etb = converter_data(row.get(idx_etb)) if idx_etb else None
                    data_ets = converter_data(row.get(idx_ets)) if idx_ets else None

                    navio, _ = Navio.objects.get_or_create(nome=navio_nome)

                    operador = None
                    if agencia:
                        operador = OperadorPortuario.objects.filter(nome_empresa=agencia).first()

                    viagem, criado = Viagem.objects.update_or_create(
                        navio=navio,
                        numero_viagem=programacao,
                        defaults={
                            'operador_portuario': operador,
                            'psp': psp,
                            'data_prevista_chegada': data_eta,
                            'data_chegada_real': data_etb,
                            'data_desatracacao': data_ets,
                            'bercario_atracacao': berco,
                            'agencia': agencia,
                        }
                    )
                    if criado:
                        criados += 1
                    else:
                        atualizados += 1
                except Exception:
                    continue

            messages.success(request, f"Importação concluída! {criados} criados, {atualizados} atualizados.")
            
        except Exception as e:
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")
            return redirect('viagem_list')
        
        return redirect('viagem_list')
    
    return redirect('viagem_list')