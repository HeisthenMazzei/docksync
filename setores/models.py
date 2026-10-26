from django.db import models
from core.models import TimestampedModel

class Setor(TimestampedModel):
    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True, db_index=True)
    setor_pai = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    capacidade_metragem = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nome