from django.contrib import admin
from .models import Manifesto

@admin.register(Manifesto)
class ManifestoAdmin(admin.ModelAdmin):
    list_display = ('id', 'viagem', 'dono_carga', 'status', 'numero_veiculos')
    list_filter = ('status', 'viagem__navio')