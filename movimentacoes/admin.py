from django.contrib import admin
from .models import Movimentacao, TrabalhadorPortuario

@admin.register(TrabalhadorPortuario)
class TrabalhadorPortuarioAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'matricula')
    search_fields = ('nome_completo', 'matricula')

@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('carga', 'tipo', 'setor_destino', 'trabalhador', 'data_hora')
    list_filter = ('tipo', 'data_hora')
    search_fields = ('carga__chassi', 'trabalhador__nome_completo')