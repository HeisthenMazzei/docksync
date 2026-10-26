from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from setores.views import (
    dashboard, gestao_patio, subpatios_list, mapa_patio,
    SetorListView, SetorCreateView, SetorUpdateView, SetorDeleteView,
    PatioDetailView, gerar_relatorio_pdf
)
from movimentacoes.views import (
    registrar_movimentacao_view, registrar_movimentacao_lote_view,
    MovimentacaoListView,
    TrabalhadorPortuarioListView, TrabalhadorPortuarioCreateView,
    TrabalhadorPortuarioUpdateView, TrabalhadorPortuarioDeleteView,
    carregar_viagens, carregar_manifestos, carregar_cargas, carregar_bls,
    exportar_movimentacoes_excel, buscar_dados_por_chassi
)
from cargas.views import (
    buscar_carga, CargaListView, CargaCreateView, CargaDetailView,
    FielDepositarioListView, FielDepositarioCreateView, FielDepositarioUpdateView, FielDepositarioDeleteView,
    ModeloVeiculoListView, ModeloVeiculoCreateView, ModeloVeiculoUpdateView, ModeloVeiculoDeleteView,
    OperadorPortuarioListView, OperadorPortuarioCreateView, OperadorPortuarioUpdateView, OperadorPortuarioDeleteView,
    BLDetailView, exportar_cargas_excel, importar_operadores_arquivo,
    gerar_qrcode_chassi, ficha_publica_veiculo,
    imprimir_etiqueta_chassi, imprimir_lote_etiquetas
)
from navios.views import (
    NavioListView, NavioCreateView, ViagemListView, ViagemCreateView,
    ViagemUpdateView, ViagemDeleteView, importar_lineup_arquivo
)
from manifestos.views import (
    ManifestoListView, ManifestoCreateView, ManifestoUpdateView,
    ManifestoDeleteView, exportar_manifestos_excel, preview_manifesto,
    importar_chassis_lista, importar_pdf, editar_chassi_provisorio,
    editar_chassis_provisorios
)
from core.views import (
    CustomLoginView, UsuarioListView, UsuarioCreateView,
    UsuarioUpdateView, UsuarioDeleteView, TrocarSenhaView
)
from relatorios.views import (
    relatorio_view, exportar_excel_view, gerar_relatorio_saidas_pdf,
    relatorio_ocupacao_operadores_pdf, relatorio_ranking_modelos_pdf,
    relatorio_prazos_excedentes_pdf
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', dashboard, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('gestao-patio/', gestao_patio, name='gestao_patio'),
    path('gestao-patio/subpatios/', subpatios_list, name='subpatios_list'),
    path('gestao-patio/mapa/', mapa_patio, name='mapa_patio'),
    path('gestao-patio/<int:pk>/', PatioDetailView.as_view(), name='patio_detail'),
    path('busca/', buscar_carga, name='busca_chassi'),

    # MOVIMENTAÇÃO
    path('registrar/', registrar_movimentacao_view, name='registrar_movimentacao'),
    path('registrar-lote/', registrar_movimentacao_lote_view, name='registrar_movimentacao_lote'),

    # FICHA PÚBLICA + QR CODE + IMPRESSÃO
    path('q/<str:chassi>/', ficha_publica_veiculo, name='ficha_publica_veiculo'),
    path('qrcode/<str:chassi>/', gerar_qrcode_chassi, name='gerar_qrcode_chassi'),
    path('imprimir/<str:chassi>/', imprimir_etiqueta_chassi, name='imprimir_etiqueta_chassi'),
    path('imprimir-lote/', imprimir_lote_etiquetas, name='imprimir_lote_etiquetas'),

    # RELATÓRIOS
    path('relatorios/', relatorio_view, name='relatorios'),
    path('relatorios/exportar/', exportar_excel_view, name='exportar_excel'),
    path('relatorios/pdf/', gerar_relatorio_pdf, name='gerar_relatorio_pdf'),
    path('relatorios/pdf/saidas/', gerar_relatorio_saidas_pdf, name='gerar_relatorio_saidas_pdf'),
    path('relatorios/pdf/ocupacao-operadores/', relatorio_ocupacao_operadores_pdf, name='relatorio_ocupacao_operadores_pdf'),
    path('relatorios/pdf/ranking-modelos/', relatorio_ranking_modelos_pdf, name='relatorio_ranking_modelos_pdf'),
    path('relatorios/pdf/prazos-excedentes/', relatorio_prazos_excedentes_pdf, name='relatorio_prazos_excedentes_pdf'),

    # USUÁRIOS
    path('cadastro/usuarios/', UsuarioListView.as_view(), name='usuario_list'),
    path('cadastro/usuarios/novo/', UsuarioCreateView.as_view(), name='usuario_create'),
    path('cadastro/usuarios/<int:pk>/editar/', UsuarioUpdateView.as_view(), name='usuario_update'),
    path('cadastro/usuarios/<int:pk>/excluir/', UsuarioDeleteView.as_view(), name='usuario_delete'),
    path('trocar-senha/', TrocarSenhaView.as_view(), name='trocar_senha'),

    # AJAX
    path('ajax/buscar-chassi/', buscar_dados_por_chassi, name='buscar_dados_por_chassi'),
    path('ajax/viagens/', carregar_viagens, name='carregar_viagens'),
    path('ajax/bls/', carregar_bls, name='carregar_bls'),
    path('ajax/manifestos/', carregar_manifestos, name='carregar_manifestos'),
    path('ajax/cargas/', carregar_cargas, name='carregar_cargas'),

    # CARGAS
    path('gestao/cargas/', CargaListView.as_view(), name='carga_list'),
    path('gestao/cargas/novo/', CargaCreateView.as_view(), name='carga_create'),
    path('gestao/cargas/<int:pk>/', CargaDetailView.as_view(), name='carga_detail'),
    path('gestao/cargas/<int:carga_id>/editar-chassi/', editar_chassi_provisorio, name='editar_chassi_provisorio'),
    path('gestao/bl/<str:bl>/', BLDetailView.as_view(), name='bl_detail'),

    # IMPORTAÇÕES
    path('importar/lineup/arquivo/', importar_lineup_arquivo, name='importar_lineup_arquivo'),
    path('importar/operadores/arquivo/', importar_operadores_arquivo, name='importar_operadores_arquivo'),

    # EXPORTAÇÕES
    path('exportar/manifestos/', exportar_manifestos_excel, name='exportar_manifestos_excel'),
    path('exportar/cargas/', exportar_cargas_excel, name='exportar_cargas_excel'),
    path('exportar/movimentacoes/', exportar_movimentacoes_excel, name='exportar_movimentacoes_excel'),

    # NAVIOS E VIAGENS
    path('gestao/navios/', NavioListView.as_view(), name='navio_list'),
    path('gestao/navios/novo/', NavioCreateView.as_view(), name='navio_create'),
    path('gestao/viagens/', ViagemListView.as_view(), name='viagem_list'),
    path('gestao/viagens/novo/', ViagemCreateView.as_view(), name='viagem_create'),
    path('gestao/viagens/<int:pk>/editar/', ViagemUpdateView.as_view(), name='viagem_update'),
    path('gestao/viagens/<int:pk>/excluir/', ViagemDeleteView.as_view(), name='viagem_delete'),

    # MANIFESTOS
    path('gestao/manifestos/', ManifestoListView.as_view(), name='manifesto_list'),
    path('gestao/manifestos/novo/', ManifestoCreateView.as_view(), name='manifesto_create'),
    path('gestao/manifestos/preview/', preview_manifesto, name='preview_manifesto'),
    path('gestao/manifestos/<int:manifesto_id>/importar-chassis/', importar_chassis_lista, name='importar_chassis_lista'),
    path('gestao/manifestos/<int:manifesto_id>/importar-pdf/', importar_pdf, name='importar_pdf'),
    path('gestao/manifestos/<int:manifesto_id>/editar-provisorios/', editar_chassis_provisorios, name='editar_chassis_provisorios'),
    path('gestao/manifestos/<int:pk>/editar/', ManifestoUpdateView.as_view(), name='manifesto_update'),
    path('gestao/manifestos/<int:pk>/excluir/', ManifestoDeleteView.as_view(), name='manifesto_delete'),

    # MOVIMENTAÇÕES
    path('gestao/movimentacoes/', MovimentacaoListView.as_view(), name='movimentacao_list'),

    # CADASTROS AUXILIARES
    path('cadastro/', FielDepositarioListView.as_view(), name='cadastro_index'),
    path('cadastro/fieis/', FielDepositarioListView.as_view(), name='fiel_list'),
    path('cadastro/fieis/novo/', FielDepositarioCreateView.as_view(), name='fiel_create'),
    path('cadastro/fieis/<int:pk>/editar/', FielDepositarioUpdateView.as_view(), name='fiel_update'),
    path('cadastro/fieis/<int:pk>/excluir/', FielDepositarioDeleteView.as_view(), name='fiel_delete'),
    path('cadastro/modelos/', ModeloVeiculoListView.as_view(), name='modelo_list'),
    path('cadastro/modelos/novo/', ModeloVeiculoCreateView.as_view(), name='modelo_create'),
    path('cadastro/modelos/<int:pk>/editar/', ModeloVeiculoUpdateView.as_view(), name='modelo_update'),
    path('cadastro/modelos/<int:pk>/excluir/', ModeloVeiculoDeleteView.as_view(), name='modelo_delete'),
    path('cadastro/patios/', SetorListView.as_view(), name='setor_list'),
    path('cadastro/patios/novo/', SetorCreateView.as_view(), name='setor_create'),
    path('cadastro/patios/<int:pk>/editar/', SetorUpdateView.as_view(), name='setor_update'),
    path('cadastro/patios/<int:pk>/excluir/', SetorDeleteView.as_view(), name='setor_delete'),
    path('cadastro/operadores/', OperadorPortuarioListView.as_view(), name='operador_portuario_list'),
    path('cadastro/operadores/novo/', OperadorPortuarioCreateView.as_view(), name='operador_portuario_create'),
    path('cadastro/operadores/<int:pk>/editar/', OperadorPortuarioUpdateView.as_view(), name='operador_portuario_update'),
    path('cadastro/operadores/<int:pk>/excluir/', OperadorPortuarioDeleteView.as_view(), name='operador_portuario_delete'),
    path('cadastro/trabalhadores/', TrabalhadorPortuarioListView.as_view(), name='trabalhador_list'),
    path('cadastro/trabalhadores/novo/', TrabalhadorPortuarioCreateView.as_view(), name='trabalhador_create'),
    path('cadastro/trabalhadores/<int:pk>/editar/', TrabalhadorPortuarioUpdateView.as_view(), name='trabalhador_update'),
    path('cadastro/trabalhadores/<int:pk>/excluir/', TrabalhadorPortuarioDeleteView.as_view(), name='trabalhador_delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)