from django.contrib import admin
from .models import Setor

@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'setor_pai', 'capacidade_metragem')
    search_fields = ('codigo', 'nome')