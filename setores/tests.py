from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from setores.models import Setor


class SetorViewPermissionTests(TestCase):
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

        self.setor = Setor.objects.create(nome="Pátio A", codigo="PA", capacidade_metragem=100)

    def test_admin_lista_setores(self):
        self.client.login(username='admin', password='12345')
        response = self.client.get(reverse('setor_list'))
        self.assertEqual(response.status_code, 200)

    def test_gestor_nao_acessa_cadastro_de_setor(self):
        self.client.login(username='gestor', password='12345')
        response = self.client.get(reverse('setor_create'))
        self.assertEqual(response.status_code, 403)

    def test_operador_nao_acessa_nada_de_setores(self):
        self.client.login(username='operador', password='12345')
        response = self.client.get(reverse('setor_list'))
        self.assertEqual(response.status_code, 403)