"""
Testes do GET /auth/users (lista de compradores e motoristas para o vendedor).
"""

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from rest_framework.test import APITestCase

URL = '/api/v1/auth/users'


def criar_usuario(nome, grupo, **extra):
    usuario = User.objects.create_user(nome, f'{nome}@teste.local', 'senha-de-teste-123', **extra)
    usuario.groups.add(Group.objects.get(name=grupo))
    return usuario


class ListaDeUsuariosTest(APITestCase):

    def setUp(self):
        call_command('criar_grupos', verbosity=0)
        self.vendedor = criar_usuario('vendedor', 'Vendedor')
        self.comprador = criar_usuario('comprador', 'Comprador', first_name='Ana', last_name='Lima')
        self.motorista = criar_usuario('motorista', 'Motorista', first_name='Bruno')
        self.inativo = criar_usuario('comprador-inativo', 'Comprador', is_active=False)

    def listar(self, usuario, **params):
        self.client.force_authenticate(usuario)
        return self.client.get(URL, params)

    def test_vendedor_lista_compradores_so_com_id_e_nome(self):
        resposta = self.listar(self.vendedor, role='buyer')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data, [{'id': self.comprador.id, 'name': 'Ana Lima'}])

    def test_vendedor_lista_motoristas(self):
        resposta = self.listar(self.vendedor, role='driver')
        self.assertEqual([u['id'] for u in resposta.data], [self.motorista.id])

    def test_nao_expoe_email(self):
        resposta = self.listar(self.vendedor, role='buyer')
        self.assertNotIn('@', str(resposta.content))

    def test_busca_por_nome(self):
        self.assertEqual(len(self.listar(self.vendedor, role='buyer', search='ana').data), 1)
        self.assertEqual(len(self.listar(self.vendedor, role='buyer', search='zzz').data), 0)

    def test_papel_invalido_da_400(self):
        self.assertEqual(self.listar(self.vendedor).status_code, 400)
        self.assertEqual(self.listar(self.vendedor, role='admin').status_code, 400)

    def test_comprador_e_motorista_nao_listam_usuarios(self):
        self.assertEqual(self.listar(self.comprador, role='driver').status_code, 403)
        self.assertEqual(self.listar(self.motorista, role='buyer').status_code, 403)

    def test_exige_login(self):
        self.assertEqual(self.client.get(URL, {'role': 'buyer'}).status_code, 401)
