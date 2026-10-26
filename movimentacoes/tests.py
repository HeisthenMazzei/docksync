from django.test import TestCase
from django.db import transaction
from django.core.exceptions import ValidationError
from movimentacoes.models import Movimentacao, TrabalhadorPortuario, registrar_movimentacao
from cargas.models import Carga, OperadorPortuario, FielDepositario, ModeloVeiculo
from manifestos.models import Manifesto
from navios.models import Navio, Viagem
from setores.models import Setor


class RegistrarMovimentacaoTests(TestCase):
    def setUp(self):
        self.navio = Navio.objects.create(nome="Navio Teste")
        self.viagem = Viagem.objects.create(navio=self.navio, numero_viagem="VIA-001", data_prevista_chegada="2026-01-01")
        self.operador = OperadorPortuario.objects.create(nome_empresa="Operadora Teste", cnpj="12345678000100")
        self.dono = FielDepositario.objects.create(nome_completo="Fiel Teste", matricula="MAT001")
        self.modelo = ModeloVeiculo.objects.create(fabricante="Fiat", modelo="Uno", ano=2020, comprimento=3.5, largura=1.6)
        self.manifesto = Manifesto.objects.create(viagem=self.viagem, operador=self.operador, dono_carga=self.dono, numero_veiculos=1, metragem_total=5.6)
        self.carga = Carga.objects.create(chassi="CHASSI001", manifesto=self.manifesto, operador=self.operador, dono=self.dono, modelo=self.modelo, metragem_unitaria=5.6)
        self.setor_a = Setor.objects.create(nome="Pátio A", codigo="PA", capacidade_metragem=1000)
        self.setor_b = Setor.objects.create(nome="Pátio B", codigo="PB", capacidade_metragem=1000)
        self.trabalhador = TrabalhadorPortuario.objects.create(nome_completo="João Silva", matricula="T001")

    def test_chegada_atualiza_setor_atual_e_localizacao(self):
        mov = registrar_movimentacao(carga=self.carga, tipo='CHEGADA', setor_origem=None, setor_destino=self.setor_a, trabalhador=self.trabalhador, localizacao_destino="Docas")
        self.carga.refresh_from_db()
        self.assertEqual(self.carga.setor_atual, self.setor_a)
        self.assertEqual(self.carga.localizacao_aproximada, "Docas")
        self.assertEqual(mov.tipo, 'CHEGADA')

    def test_movimentacao_interna_atualiza_setor_destino(self):
        registrar_movimentacao(carga=self.carga, tipo='CHEGADA', setor_origem=None, setor_destino=self.setor_a, trabalhador=self.trabalhador)
        registrar_movimentacao(carga=self.carga, tipo='INTERNA', setor_origem=self.setor_a, setor_destino=self.setor_b, trabalhador=self.trabalhador)
        self.carga.refresh_from_db()
        self.assertEqual(self.carga.setor_atual, self.setor_b)

    def test_saida_limpa_setor_e_localizacao(self):
        registrar_movimentacao(carga=self.carga, tipo='CHEGADA', setor_origem=None, setor_destino=self.setor_a, trabalhador=self.trabalhador, latitude_destino='-23.5', longitude_destino='-46.6')
        registrar_movimentacao(carga=self.carga, tipo='SAIDA', setor_origem=self.setor_a, setor_destino=None, trabalhador=self.trabalhador)
        self.carga.refresh_from_db()
        self.assertIsNone(self.carga.setor_atual)
        self.assertEqual(self.carga.localizacao_aproximada, '')
        self.assertIsNone(self.carga.latitude)
        self.assertIsNone(self.carga.longitude)

    def test_registro_atomico(self):
        with self.assertRaises(ValidationError):
            registrar_movimentacao(carga=self.carga, tipo='CHEGADA', setor_origem=None, setor_destino=None, trabalhador=self.trabalhador)
        self.carga.refresh_from_db()
        self.assertIsNone(self.carga.setor_atual)

    def test_movimentacao_gera_historico_imutavel(self):
        mov1 = registrar_movimentacao(carga=self.carga, tipo='CHEGADA', setor_origem=None, setor_destino=self.setor_a, trabalhador=self.trabalhador)
        mov2 = registrar_movimentacao(carga=self.carga, tipo='INTERNA', setor_origem=self.setor_a, setor_destino=self.setor_b, trabalhador=self.trabalhador)
        self.assertEqual(Movimentacao.objects.filter(carga=self.carga).count(), 2)
        self.assertEqual(mov1.tipo, 'CHEGADA')
        self.assertEqual(mov2.tipo, 'INTERNA')