from django.db import models
from setores.models import Setor
from core.models import TimestampedModel


class OperadorPortuario(TimestampedModel):
    nome_empresa = models.CharField(max_length=255, verbose_name="Nome da Empresa")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    telefone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefone")
    responsavel_tecnico = models.CharField(max_length=255, null=True, blank=True, verbose_name="Responsável Técnico")
    numero_registro = models.CharField(max_length=50, null=True, blank=True, verbose_name="Número do Registro")
    data_validade = models.DateField(null=True, blank=True, verbose_name="Data Validade")
    situacao = models.CharField(max_length=20, null=True, blank=True, verbose_name="Situação")

    def __str__(self):
        return self.nome_empresa


class FielDepositario(TimestampedModel):
    nome_completo = models.CharField(max_length=255)
    matricula = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.nome_completo} (Mat: {self.matricula})"


class ModeloVeiculo(TimestampedModel):
    fabricante = models.CharField(max_length=100, null=True, blank=True)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    abreviado = models.CharField(max_length=50, null=True, blank=True, verbose_name="Nome Abreviado")
    ano = models.IntegerField(null=True, blank=True)
    comprimento = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    largura = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    metragem_m2 = models.DecimalField(max_digits=6, decimal_places=2, blank=True, editable=False, default=0)

    def save(self, *args, **kwargs):
        if self.comprimento and self.largura:
            self.metragem_m2 = self.comprimento * self.largura
        super().save(*args, **kwargs)

    def __str__(self):
        if self.abreviado:
            return self.abreviado
        return f"{self.fabricante} {self.modelo} ({self.ano})"

    def nome_completo(self):
        return f"{self.fabricante} {self.modelo} ({self.ano})"


class Carga(TimestampedModel):
    class Origem(models.TextChoices):
        MANUAL = 'MANUAL', 'Cadastro Manual'
        LISTA = 'LISTA', 'Importação de Lista'
        PDF = 'PDF', 'Importação de PDF'

    bl = models.CharField(max_length=50, null=True, blank=True, db_index=True, verbose_name="BL (Conhecimento de Embarque)")
    chassi = models.CharField(max_length=50, unique=True, db_index=True)
    manifesto = models.ForeignKey('manifestos.Manifesto', on_delete=models.CASCADE, related_name='cargas')
    operador = models.ForeignKey(OperadorPortuario, on_delete=models.PROTECT, null=True, blank=True, related_name='cargas', verbose_name="Operador Portuário")
    dono = models.ForeignKey(FielDepositario, on_delete=models.PROTECT, null=True, blank=True, related_name='cargas', verbose_name="Fiel Depositário")
    modelo = models.ForeignKey(ModeloVeiculo, on_delete=models.PROTECT, null=True, blank=True, related_name='cargas')
    metragem_unitaria = models.DecimalField(max_digits=10, decimal_places=2)
    setor_atual = models.ForeignKey(Setor, on_delete=models.PROTECT, null=True, blank=True, related_name='cargas_presentes')
    localizacao_aproximada = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # NOVOS CAMPOS
    provisorio = models.BooleanField(
        default=False,
        verbose_name="Chassi Provisório",
        help_text="Chassi gerado automaticamente (deve ser substituído pelo real)"
    )
    origem = models.CharField(
        max_length=20,
        choices=Origem.choices,
        default=Origem.MANUAL,
        verbose_name="Origem do Cadastro"
    )

    def __str__(self):
        return self.chassi