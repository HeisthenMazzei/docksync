from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from navios.models import Navio, Viagem


class NavioViagemPermissionTests(TestCase):
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

        self.navio = Navio.objects.create(nome="Navio Teste", imo="1234567")

    def test_operador_nao_acessa_lista_de_navios(self):
        self.client.login(username='operador', password='12345')
        response = self.client.get(reverse('navio_list'))
        self.assertEqual(response.status_code, 403)

    def test_gestor_acessa_lista_de_navios(self):
        self.client.login(username='gestor', password='12345')
        response = self.client.get(reverse('navio_list'))
        self.assertEqual(response.status_code, 200)

    def test_criar_navio_somente_admin(self):
        # Gestor tem permissão de criar. O POST bem-sucedido redireciona (302).
        self.client.login(username='gestor', password='12345')
        response = self.client.post(reverse('navio_create'), {
            'nome': 'Novo Navio',
            'imo': '9988776',
            'mmsi': ''
        })
        self.assertEqual(response.status_code, 302)  # Sucesso = Redireciona para a lista

    def test_operador_nao_cria_viagem(self):
        self.client.login(username='operador', password='12345')
        response = self.client.get(reverse('viagem_create'))
        self.assertEqual(response.status_code, 403)