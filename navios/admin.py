from django.contrib import admin
from .models import Navio, Viagem

@admin.register(Navio)
class NavioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'imo', 'mmsi', 'criado_em')
    search_fields = ('nome', 'imo', 'mmsi')

@admin.register(Viagem)
class ViagemAdmin(admin.ModelAdmin):
    list_display = ('numero_viagem', 'navio', 'status', 'data_prevista_chegada', 'bercario_atracacao')
    list_filter = ('status', 'navio', 'data_prevista_chegada')
    search_fields = ('numero_viagem', 'navio__nome')