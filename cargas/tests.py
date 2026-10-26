from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from cargas.models import Carga, OperadorPortuario, FielDepositario, ModeloVeiculo
from manifestos.models import Manifesto
from navios.models import Navio, Viagem
from setores.models import Setor


class CargaViewsPermissionTests(TestCase):
    def setUp(self):
        self.group_admin, _ = Group.objects.get_or_create(name='Administrador')
        self.group_gestor, _ = Group.objects.get_or_create(name='Gestor')
        self.group_operador, _ = Group.objects.get_or_create(name='Operador')

        self.user_admin = User.objects.create_user(username='admin', password='12345')
        self.user_admin.groups.add(self.group_admin)
        self.user_gestor = User.objects.create_user(username='gestor', password='12345')
        self.user_gestor.groups.add(self.group_gestor)
        self.user_operador = User.objects.create_user(username='operador', password='12345')
        self.user_operador.groups.add(self.group_operador)

        self.navio = Navio.objects.create(nome="Navio Teste")
        self.viagem = Viagem.objects.create(navio=self.navio, numero_viagem="V1", data_prevista_chegada="2026-01-01")
        self.operador = OperadorPortuario.objects.create(nome_empresa="Op1", cnpj="123")
        self.dono = FielDepositario.objects.create(nome_completo="Fiel1", matricula="M1")
        self.modelo = ModeloVeiculo.objects.create(fabricante="Fiat", modelo="Uno", ano=2020, comprimento=3, largura=1.5)
        self.manifesto = Manifesto.objects.create(viagem=self.viagem, operador=self.operador, dono_carga=self.dono, numero_veiculos=1, metragem_total=4.5)
        self.carga = Carga.objects.create(chassi="CH1", manifesto=self.manifesto, operador=self.operador, dono=self.dono, modelo=self.modelo, metragem_unitaria=4.5)

    def test_operador_nao_acessa_lista_de_cargas(self):
        self.client.login(username='operador', password='12345')
        response = self.client.get(reverse('carga_list'))
        self.assertEqual(response.status_code, 403)  # Sem permissão = 403

    def test_gestor_acessa_lista_de_cargas(self):
        self.client.login(username='gestor', password='12345')
        response = self.client.get(reverse('carga_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_acessa_lista_de_cargas(self):
        self.client.login(username='admin', password='12345')
        response = self.client.get(reverse('carga_list'))
        self.assertEqual(response.status_code, 200)

    def test_operador_nao_acessa_detalhe_de_carga(self):
        self.client.login(username='operador', password='12345')
        response = self.client.get(reverse('carga_detail', args=[self.carga.id]))
        self.assertEqual(response.status_code, 403)

    def test_superuser_acessa_tudo(self):
        self.user_admin.is_superuser = True
        self.user_admin.save()
        self.client.login(username='admin', password='12345')
        response = self.client.get(reverse('carga_list'))
        self.assertEqual(response.status_code, 200)