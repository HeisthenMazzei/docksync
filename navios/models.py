from django.db import models
from core.models import TimestampedModel
from cargas.models import OperadorPortuario


class Navio(TimestampedModel):
    nome = models.CharField(max_length=200)
    imo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número IMO")
    mmsi = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código MMSI")

    def __str__(self):
        return self.nome


class Viagem(TimestampedModel):
    class StatusViagem(models.TextChoices):
        AGUARDANDO_CHEGADA = 'AGUARDANDO_CHEGADA', 'Esperado'
        FUNDEADO = 'FUNDEADO', 'Fundeado'
        ATRACADO = 'ATRACADO', 'Atracado / Operando'
        DESCARREGANDO = 'DESCARREGANDO', 'Descarregando'
        CARREGANDO = 'CARREGANDO', 'Carregando'
        FINALIZADO = 'FINALIZADO', 'Finalizado'

    class Sentido(models.TextChoices):
        DESCARGA = 'DESCARGA', 'Descarga (Importação)'
        CARGA = 'CARGA', 'Carga (Exportação)'

    navio = models.ForeignKey(Navio, on_delete=models.PROTECT, related_name='viagens')
    numero_viagem = models.CharField(max_length=50)

    operador_portuario = models.ForeignKey(
        OperadorPortuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='viagens_operador'
    )

    sentido = models.CharField(
        max_length=20,
        choices=Sentido.choices,
        default=Sentido.DESCARGA,
        verbose_name="Sentido"
    )

    quantidade_prevista = models.IntegerField(
        default=0,
        verbose_name="Quantidade Prevista",
        help_text="Quantidade de veículos declarada no BL/manifesto"
    )

    psp = models.CharField(max_length=20, blank=True, null=True, verbose_name="PSP")
    data_prevista_chegada = models.DateField(verbose_name="Fundeio / ETA")
    data_chegada_real = models.DateField(null=True, blank=True, verbose_name="Atracação / ETB")
    data_desatracacao = models.DateField(null=True, blank=True, verbose_name="Desatracação / ETS")

    bercario_atracacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Berço de Atracação")
    agencia = models.CharField(max_length=255, null=True, blank=True, verbose_name="Agência")
    status = models.CharField(
        max_length=50,
        choices=StatusViagem.choices,
        default=StatusViagem.AGUARDANDO_CHEGADA,
        verbose_name="Status da Viagem"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['navio', 'numero_viagem'], name='unique_viagem_por_navio')
        ]
        verbose_name_plural = 'Viagens'

    def __str__(self):
        return f"{self.navio.nome} - {self.numero_viagem}"

    def quantidade_cadastrada(self):
        """Quantidade de cargas efetivamente cadastradas nesta viagem."""
        return self.manifestos.aggregate(
            total=models.Count('cargas', distinct=True)
        )['total'] or 0