from django.db import models
from django.core.exceptions import ValidationError
from cargas.models import Carga
from setores.models import Setor
from core.models import TimestampedModel
from django.db import transaction


class TrabalhadorPortuario(TimestampedModel):
    nome_completo = models.CharField(max_length=255)
    matricula = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.nome_completo} (Mat: {self.matricula})"


class Movimentacao(TimestampedModel):
    class Tipo(models.TextChoices):
        CHEGADA = 'CHEGADA', 'Chegada (Entrada no Porto)'
        INTERNA = 'INTERNA', 'Movimentação Interna'
        SAIDA = 'SAIDA', 'Saída (Retirada do Porto)'

    carga = models.ForeignKey(Carga, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    setor_origem = models.ForeignKey(Setor, on_delete=models.PROTECT, null=True, blank=True, related_name='mov_origem')
    setor_destino = models.ForeignKey(Setor, on_delete=models.PROTECT, null=True, blank=True, related_name='mov_destino')
    localizacao_origem = models.CharField(max_length=200, blank=True)
    localizacao_destino = models.CharField(max_length=200, blank=True)
    latitude_origem = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude_origem = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    latitude_destino = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude_destino = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)

    trabalhador = models.ForeignKey(TrabalhadorPortuario, on_delete=models.PROTECT, null=True, blank=True, related_name='movimentacoes')
    fotografia_chassi = models.ImageField(upload_to='movimentacoes/%Y/%m/%d/', blank=True, null=True)

    def __str__(self):
        return f"{self.carga.chassi} - {self.tipo}"


def registrar_movimentacao(carga, tipo, setor_origem=None, setor_destino=None, trabalhador=None, **kwargs):
    """
    Registra uma movimentação de carga e atualiza a localização atual da carga
    de forma atômica.

    Regras de negócio validadas:
    - CHEGADA: só é permitida se a carga NÃO está no pátio (setor_atual nulo)
    - SAIDA: só é permitida se a carga ESTÁ no pátio (setor_atual preenchido)
    - INTERNA: só é permitida se a carga ESTÁ no pátio
    """
    with transaction.atomic():

        # ==================================================
        # VALIDAÇÕES DE ESTADO ATUAL DA CARGA
        # ==================================================
        if tipo == 'CHEGADA' and carga.setor_atual is not None:
            raise ValidationError(
                f"O veículo {carga.chassi} já está no porto (setor {carga.setor_atual.nome}). "
                f"Registre uma movimentação INTERNA ou de SAÍDA."
            )

        if tipo == 'SAIDA' and carga.setor_atual is None:
            raise ValidationError(
                f"O veículo {carga.chassi} não está no porto. "
                f"Não é possível registrar uma saída."
            )

        if tipo == 'INTERNA' and carga.setor_atual is None:
            raise ValidationError(
                f"O veículo {carga.chassi} ainda não chegou ao porto. "
                f"Registre primeiro uma CHEGADA."
            )

        # ==================================================
        # VALIDAÇÕES DE CAMPOS OBRIGATÓRIOS
        # ==================================================
        if tipo in ['CHEGADA', 'INTERNA'] and not setor_destino:
            raise ValidationError(
                "O setor de destino é obrigatório para movimentações de Chegada e Interna."
            )

        if tipo == 'SAIDA' and not setor_origem:
            raise ValidationError(
                "O setor de origem é obrigatório para movimentações de Saída."
            )

        # ==================================================
        # CRIA A MOVIMENTAÇÃO
        # ==================================================
        mov = Movimentacao.objects.create(
            carga=carga,
            tipo=tipo,
            setor_origem=setor_origem,
            setor_destino=setor_destino,
            trabalhador=trabalhador,
            **kwargs
        )

        # ==================================================
        # ATUALIZA A LOCALIZAÇÃO ATUAL DA CARGA
        # ==================================================
        if tipo == 'SAIDA':
            carga.setor_atual = None
            carga.localizacao_aproximada = ''
            carga.latitude = None
            carga.longitude = None
        else:
            carga.setor_atual = setor_destino
            if kwargs.get('latitude_destino'):
                carga.latitude = kwargs.get('latitude_destino')
                carga.longitude = kwargs.get('longitude_destino')
                carga.localizacao_aproximada = f"GPS: {kwargs.get('latitude_destino')}, {kwargs.get('longitude_destino')}"
            else:
                carga.localizacao_aproximada = kwargs.get('localizacao_destino', '')
                carga.latitude = kwargs.get('latitude_destino', None)
                carga.longitude = kwargs.get('longitude_destino', None)

        carga.save(update_fields=['setor_atual', 'localizacao_aproximada', 'latitude', 'longitude', 'atualizado_em'])
        return mov