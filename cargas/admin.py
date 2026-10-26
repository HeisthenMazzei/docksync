from django.contrib import admin
from .models import Carga

@admin.register(Carga)
class CargaAdmin(admin.ModelAdmin):
    list_display = ('chassi', 'manifesto', 'setor_atual', 'metragem_unitaria')
    search_fields = ('chassi',)
    list_filter = ('setor_atual',)