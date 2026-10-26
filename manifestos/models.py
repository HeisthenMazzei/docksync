from django.db import models
from navios.models import Viagem
from core.models import TimestampedModel


class Manifesto(TimestampedModel):
    class Status(models.TextChoices):
        AGUARDANDO = 'AGUARDANDO', 'Aguardando'
        EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em Andamento'
        CONCLUIDO = 'CONCLUIDO', 'Concluído'

    viagem = models.ForeignKey(Viagem, on_delete=models.PROTECT, related_name='manifestos')
    operador = models.ForeignKey('cargas.OperadorPortuario', on_delete=models.PROTECT, null=True, blank=True, related_name='manifestos', verbose_name="Operador Portuário")
    dono_carga = models.ForeignKey('cargas.FielDepositario', on_delete=models.PROTECT, related_name='manifestos', verbose_name="Fiel Depositário")
    numero_veiculos = models.IntegerField()
    metragem_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AGUARDANDO)
    data_estimada_retirada = models.DateField(null=True, blank=True, verbose_name="Previsão de Saída")
    data_real_retirada = models.DateField(null=True, blank=True, verbose_name="Data Real de Saída")

    def __str__(self):
        return f"Manifesto {self.id} - {self.viagem}"


class ItemManifesto(models.Model):
    manifesto = models.ForeignKey(Manifesto, on_delete=models.CASCADE, related_name='itens')
    modelo = models.ForeignKey('cargas.ModeloVeiculo', on_delete=models.PROTECT)
    quantidade = models.IntegerField()
    lista_chassis = models.TextField(help_text="Cole os chassis separados por vírgula ou quebra de linha")

    def __str__(self):
        return f"{self.modelo} - {self.quantidade} un."