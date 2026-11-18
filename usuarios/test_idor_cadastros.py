"""
Protecao contra IDOR nos CADASTROS: locais (fazendas, CDs) e veiculos.

Cenario: os vendedores A e B tem cada um a sua fazenda, o seu CD e o seu
veiculo. Existe tambem um CD compartilhado (sem dono, cadastrado pela plataforma).
A viagem do B tem um comprador.
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from dominio.models import Location, Vehicle
from iot.models import Device
from transporte.models import Shipment


def ids(resposta):
    dados = resposta.data['data'] if isinstance(resposta.data, dict) else resposta.data
    return sorted(item['id'] for item in dados)


def criar_usuario(nome, grupo):
    usuario = User.objects.create_user(nome, f'{nome}@teste.local', 'senha-de-teste-123')
    usuario.groups.add(Group.objects.get(name=grupo))
    return usuario


@override_settings(SECURITY_MISSION_CODE='TST123')
class ProtecaoIdorCadastrosTest(APITestCase):

    def setUp(self):
        call_command('criar_grupos', verbosity=0)
        self.vendedor_a = criar_usuario('vendedor-a', 'Vendedor')
        self.vendedor_b = criar_usuario('vendedor-b', 'Vendedor')
        self.comprador_b = criar_usuario('comprador-b', 'Comprador')

        self.fazenda_a = Location.objects.create(name='Fazenda A', type='farm', owner=self.vendedor_a)
        self.fazenda_b = Location.objects.create(name='Fazenda B', type='farm', owner=self.vendedor_b)
        self.cd_comum = Location.objects.create(name='CD comum', type='distribution_center')  # sem dono
        self.veiculo_a = Vehicle.objects.create(plate='AAA1A11', owner=self.vendedor_a)
        self.veiculo_b = Vehicle.objects.create(plate='BBB2B22', owner=self.vendedor_b)

        self.placa_a = Device.objects.create(uid='A', name='Placa A', owner=self.vendedor_a)
        self.placa_b = Device.objects.create(uid='B', name='Placa B', owner=self.vendedor_b)
        self.viagem_b = Shipment.objects.create(
            origin=self.fazenda_b, destination=self.cd_comum, vehicle=self.veiculo_b, device=self.placa_b,
            created_by=self.vendedor_b, buyer=self.comprador_b, status='planned', started_at=timezone.now(),
        )

    def como(self, usuario):
        self.client.force_authenticate(usuario)

    def dados_viagem(self, **extra):
        return {
            'origin': self.fazenda_a.id, 'destination': self.cd_comum.id, 'vehicle': self.veiculo_a.id,
            'device': self.placa_a.id, 'started_at': (timezone.now() + timedelta(hours=1)).isoformat(), **extra,
        }

    # --- Ver -----------------------------------------------------------------

    def test_cada_um_ve_os_seus_e_os_compartilhados(self):
        self.como(self.vendedor_a)
        self.assertEqual(ids(self.client.get('/api/v1/locations')), sorted([self.fazenda_a.id, self.cd_comum.id]))
        self.assertEqual(ids(self.client.get('/api/v1/vehicles')), [self.veiculo_a.id])

    def test_a_nao_le_os_cadastros_do_b(self):
        self.como(self.vendedor_a)
        self.assertEqual(self.client.get(f'/api/v1/locations/{self.fazenda_b.id}').status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/vehicles/{self.veiculo_b.id}').status_code, 404)

    def test_comprador_ve_a_origem_e_o_veiculo_da_compra_dele(self):
        self.como(self.comprador_b)
        self.assertEqual(self.client.get(f'/api/v1/locations/{self.fazenda_b.id}').status_code, 200)
        self.assertEqual(self.client.get(f'/api/v1/vehicles/{self.veiculo_b.id}').status_code, 200)

    # --- Alterar -------------------------------------------------------------

    def test_a_nao_altera_os_cadastros_do_b(self):
        self.como(self.vendedor_a)
        with self.assertLogs('seguranca', level='WARNING') as log:
            resposta = self.client.patch(f'/api/v1/vehicles/{self.veiculo_b.id}', {'model': 'x'}, format='json')
        self.assertEqual(resposta.status_code, 404)
        self.assertIn('[TST123] IDOR bloqueado', log.output[0])
        self.assertEqual(
            self.client.patch(f'/api/v1/locations/{self.fazenda_b.id}', {'name': 'x'}, format='json').status_code, 404,
        )
        self.veiculo_b.refresh_from_db()
        self.assertEqual(self.veiculo_b.model, '')  # nada mudou

    def test_quem_so_ve_nao_altera(self):
        """O comprador VE a fazenda do vendedor (pela viagem), mas nao altera: 403."""
        self.como(self.comprador_b)
        resposta = self.client.patch(f'/api/v1/locations/{self.fazenda_b.id}', {'name': 'x'}, format='json')
        self.assertEqual(resposta.status_code, 403)

    def test_compartilhado_so_a_plataforma_altera(self):
        self.como(self.vendedor_a)
        self.assertEqual(
            self.client.patch(f'/api/v1/locations/{self.cd_comum.id}', {'name': 'x'}, format='json').status_code, 403,
        )
        self.como(User.objects.create_superuser('plataforma', 'p@teste.local', 'senha-de-teste-123'))
        self.assertEqual(
            self.client.patch(f'/api/v1/locations/{self.cd_comum.id}', {'name': 'CD'}, format='json').status_code, 200,
        )

    def test_dono_altera_e_o_dono_vem_do_token(self):
        self.como(self.vendedor_a)
        resposta = self.client.patch(f'/api/v1/vehicles/{self.veiculo_a.id}', {'model': 'Truck'}, format='json')
        self.assertEqual(resposta.status_code, 200)
        # Criar mandando owner de outro: o campo e ignorado, o dono e quem esta logado.
        resposta = self.client.post('/api/v1/vehicles', {'plate': 'CCC3C33', 'owner': self.vendedor_b.id}, format='json')
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(Vehicle.objects.get(plate='CCC3C33').owner, self.vendedor_a)

    # --- Usar na viagem (ID no corpo) ------------------------------------------

    def test_viagem_com_os_proprios_cadastros_e_os_compartilhados(self):
        self.como(self.vendedor_a)
        resposta = self.client.post('/api/v1/shipments', self.dados_viagem(), format='json')
        self.assertEqual(resposta.status_code, 201, resposta.data)

    def test_viagem_com_cadastro_do_b_pelo_corpo_e_recusada(self):
        """Contorno: usar a fazenda ou o veiculo do B mandando o ID no corpo."""
        self.como(self.vendedor_a)
        for campo, valor in (('origin', self.fazenda_b.id), ('vehicle', self.veiculo_b.id)):
            with self.subTest(campo=campo):
                resposta = self.client.post('/api/v1/shipments', self.dados_viagem(**{campo: valor}), format='json')
                self.assertEqual(resposta.status_code, 403)
        self.assertEqual(Shipment.objects.filter(created_by=self.vendedor_a).count(), 0)

    def test_editar_viagem_trocando_para_cadastro_do_b_e_recusado(self):
        self.como(self.vendedor_a)
        viagem = self.client.post('/api/v1/shipments', self.dados_viagem(), format='json').data['id']
        resposta = self.client.patch(f'/api/v1/shipments/{viagem}', {'vehicle': self.veiculo_b.id}, format='json')
        self.assertEqual(resposta.status_code, 403)
