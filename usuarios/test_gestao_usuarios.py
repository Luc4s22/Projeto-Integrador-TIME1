"""
Gestao de usuarios pela plataforma (tela "Usuarios" do front, sem o /admin).
"""

from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APITestCase

from usuarios.models import SegundoFator

URL = '/api/v1/auth/users'
FRONT = 'http://localhost:5173/redefinir-senha'


def criar_usuario(nome, grupo=None, **extra):
    usuario = User.objects.create_user(nome, f'{nome}@teste.local', 'senha-de-teste-123', **extra)
    if grupo:
        usuario.groups.add(Group.objects.get(name=grupo))
    return usuario


@override_settings(PASSWORD_RESET_URL=FRONT, RESEND_API_KEY='', RESEND_FROM_EMAIL='', SECURITY_MISSION_CODE='TST123')
class GestaoDeUsuariosTest(APITestCase):

    def setUp(self):
        cache.clear()
        call_command('criar_grupos', verbosity=0)
        self.plataforma = User.objects.create_superuser('plataforma', 'plataforma@teste.local', 'senha-de-teste-123')
        self.vendedor = criar_usuario('vendedor', 'Vendedor')

    def como(self, usuario):
        self.client.force_authenticate(usuario)

    def novo(self, **extra):
        dados = {'email': 'Novo.Motorista@Teste.local', 'name': 'Novo Motorista', 'role': 'driver', **extra}
        return self.client.post(URL, dados, format='json')

    # --- Criar ---------------------------------------------------------------

    def test_plataforma_cria_usuario_sem_senha_e_com_papel(self):
        self.como(self.plataforma)
        with self.assertLogs('seguranca', level='WARNING') as log:
            resposta = self.novo()
        self.assertEqual(resposta.status_code, 201, resposta.data)
        usuario = User.objects.get(email='novo.motorista@teste.local')  # e-mail normalizado
        self.assertEqual(usuario.username, 'novo.motorista@teste.local')
        self.assertEqual((usuario.first_name, usuario.last_name), ('Novo', 'Motorista'))
        self.assertEqual(list(usuario.groups.values_list('name', flat=True)), ['Motorista'])
        self.assertFalse(usuario.has_usable_password())  # ninguem escolheu a senha dele
        self.assertEqual(resposta.data['user']['role'], 'driver')
        self.assertFalse(resposta.data['user']['has_password'])
        self.assertIn('[TST123] Gestao de usuarios: criou (driver)', log.output[0])

    def test_sem_email_configurado_devolve_o_link_para_a_plataforma(self):
        self.como(self.plataforma)
        resposta = self.novo()
        self.assertFalse(resposta.data['invite_sent'])
        self.assertTrue(resposta.data['password_setup_link'].startswith(FRONT + '?uid='))

    @override_settings(RESEND_API_KEY='chave-ficticia', RESEND_FROM_EMAIL='nao-responda@teste.local')
    @patch('usuarios.convite.urlopen')
    def test_com_email_configurado_manda_convite_e_nao_devolve_o_link(self, mock_urlopen):
        self.como(self.plataforma)
        resposta = self.novo()
        self.assertTrue(resposta.data['invite_sent'])
        self.assertIsNone(resposta.data['password_setup_link'])
        mock_urlopen.assert_called_once()

    def test_convidado_define_a_senha_e_cai_no_cadastro_do_2fa(self):
        self.como(self.plataforma)
        link = self.novo().data['password_setup_link']
        parametros = {k: v[0] for k, v in parse_qs(urlparse(link).query).items()}
        self.client.force_authenticate(None)

        resposta = self.client.post('/api/v1/auth/password-reset/confirm',
                                    {**parametros, 'password': 'SenhaNovaForte123!'}, format='json')
        self.assertEqual(resposta.status_code, 200, resposta.data)
        # O link e de uso unico: depois de usado, nao vale de novo.
        de_novo = self.client.post('/api/v1/auth/password-reset/confirm',
                                   {**parametros, 'password': 'OutraSenhaForte123!'}, format='json')
        self.assertEqual(de_novo.status_code, 400)

        login = self.client.post('/api/v1/auth/login',
                                 {'email': 'novo.motorista@teste.local', 'password': 'SenhaNovaForte123!'},
                                 format='json')
        self.assertEqual(login.status_code, 200)
        self.assertTrue(login.data['mfa_setup_required'])  # primeiro acesso: tela do QR Code

    def test_email_repetido_e_recusado(self):
        self.como(self.plataforma)
        resposta = self.client.post(URL, {'email': 'VENDEDOR@teste.local', 'name': 'X', 'role': 'seller'},
                                    format='json')
        self.assertEqual(resposta.status_code, 400)

    def test_so_superusuario_cria_administrador(self):
        admin_comum = criar_usuario('admin-comum', 'Administrador')
        self.como(admin_comum)
        self.assertEqual(self.novo(role='admin').status_code, 403)
        self.assertEqual(self.novo(role='seller').status_code, 201)

    # --- Quem NAO e plataforma -----------------------------------------------

    def test_vendedor_nao_cria_nem_lista_nem_altera(self):
        self.como(self.vendedor)
        self.assertEqual(self.novo().status_code, 403)
        self.assertEqual(self.client.get(URL).status_code, 400)  # sem ?role= a lista completa e so da plataforma
        alvo = criar_usuario('outro', 'Comprador')
        self.assertEqual(self.client.patch(f'{URL}/{alvo.id}', {'is_active': False}, format='json').status_code, 403)
        self.assertEqual(self.client.post(f'{URL}/{alvo.id}/reset-2fa').status_code, 403)
        self.assertEqual(self.client.post(f'{URL}/{alvo.id}/invite').status_code, 403)
        alvo.refresh_from_db()
        self.assertTrue(alvo.is_active)

    def test_comprador_e_motorista_nao_acessam(self):
        for grupo in ('Comprador', 'Motorista'):
            with self.subTest(grupo=grupo):
                self.como(criar_usuario(f'u-{grupo}', grupo))
                self.assertEqual(self.client.get(URL).status_code, 403)
                self.assertEqual(self.novo(email=f'x-{grupo}@teste.local').status_code, 403)

    def test_sem_login_401(self):
        self.assertEqual(self.client.get(URL).status_code, 401)
        self.assertEqual(self.novo().status_code, 401)

    # --- Listar e alterar ------------------------------------------------------

    def test_plataforma_lista_todos_com_situacao(self):
        self.como(self.plataforma)
        resposta = self.client.get(URL)
        self.assertEqual(resposta.status_code, 200)
        linha = next(u for u in resposta.data if u['id'] == self.vendedor.id)
        self.assertEqual(linha['role'], 'seller')
        self.assertTrue(linha['has_password'])
        self.assertFalse(linha['has_2fa'])
        self.assertEqual(linha['email'], 'vendedor@teste.local')

    def test_lista_de_motoristas_do_formulario_continua_igual(self):
        self.como(self.vendedor)
        resposta = self.client.get(URL, {'role': 'driver'})
        self.assertEqual(resposta.status_code, 200)

    def test_plataforma_troca_papel_e_desativa(self):
        alvo = criar_usuario('alvo', 'Comprador')
        self.como(self.plataforma)
        resposta = self.client.patch(f'{URL}/{alvo.id}', {'role': 'seller', 'name': 'Alvo Silva'}, format='json')
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['role'], 'seller')
        self.assertEqual(resposta.data['name'], 'Alvo Silva')
        resposta = self.client.patch(f'{URL}/{alvo.id}', {'is_active': False}, format='json')
        self.assertFalse(resposta.data['is_active'])
        # Desativado nao entra mais.
        self.client.force_authenticate(None)
        login = self.client.post('/api/v1/auth/login', {'email': 'alvo@teste.local', 'password': 'senha-de-teste-123'},
                                 format='json')
        self.assertEqual(login.status_code, 400)

    def test_plataforma_nao_se_desativa_nem_se_rebaixa(self):
        self.como(self.plataforma)
        self.assertEqual(
            self.client.patch(f'{URL}/{self.plataforma.id}', {'is_active': False}, format='json').status_code, 400,
        )
        self.assertEqual(
            self.client.patch(f'{URL}/{self.plataforma.id}', {'role': 'seller'}, format='json').status_code, 400,
        )

    def test_admin_comum_nao_mexe_em_superusuario(self):
        self.como(criar_usuario('admin-comum', 'Administrador'))
        resposta = self.client.patch(f'{URL}/{self.plataforma.id}', {'is_active': False}, format='json')
        self.assertEqual(resposta.status_code, 403)

    def test_resetar_2fa_e_reenviar_convite(self):
        alvo = criar_usuario('celular-perdido', 'Vendedor')
        SegundoFator.objects.create(usuario=alvo, segredo_cifrado='x', ativo=True)
        self.como(self.plataforma)
        self.assertEqual(self.client.post(f'{URL}/{alvo.id}/reset-2fa').status_code, 200)
        self.assertFalse(SegundoFator.objects.filter(usuario=alvo).exists())
        convite = self.client.post(f'{URL}/{alvo.id}/invite')
        self.assertEqual(convite.status_code, 200)
        self.assertIn('?uid=', convite.data['password_setup_link'])

    @override_settings(RESEND_API_KEY='chave-ficticia', RESEND_FROM_EMAIL='nao-responda@teste.local')
    @patch('usuarios.convite.urlopen')
    def test_convidado_pode_pedir_link_novo_pela_recuperacao(self, mock_urlopen):
        """O convite vence em 3 dias; quem ainda nao tem senha pede outro link em 'Esqueci minha senha'."""
        self.como(self.plataforma)
        self.novo()
        mock_urlopen.reset_mock()
        self.client.force_authenticate(None)
        self.client.post('/api/v1/auth/password-reset', {'email': 'novo.motorista@teste.local'}, format='json')
        mock_urlopen.assert_called_once()
