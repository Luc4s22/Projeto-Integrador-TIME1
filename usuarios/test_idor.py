"""
Testes automatizados da protecao contra IDOR.

Cenario: dois vendedores (A e B), cada um com a sua placa e a sua viagem.
A viagem do B tem um comprador e um motorista. O vendedor A tenta usar
os IDs do B em todas as rotas; o B, o comprador e o motorista usam normalmente.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from alertas.models import Alert
from dominio.models import Fruit, FruitParameter, Location, Vehicle
from iot.models import Device, Reading
from transporte.models import Shipment, ShipmentItem


def ids(resposta):
    """IDs de uma listagem (com ou sem paginacao)."""
    dados = resposta.data['data'] if isinstance(resposta.data, dict) else resposta.data
    return [item['id'] for item in dados]


def criar_usuario(nome, grupo):
    usuario = User.objects.create_user(nome, f'{nome}@teste.local', 'senha-de-teste-123')
    usuario.groups.add(Group.objects.get(name=grupo))
    return usuario


@override_settings(SECURITY_MISSION_CODE='TST123')
class ProtecaoIdorTest(APITestCase):

    def setUp(self):
        call_command('criar_grupos', verbosity=0)
        self.vendedor_a = criar_usuario('vendedor-a', 'Vendedor')
        self.vendedor_b = criar_usuario('vendedor-b', 'Vendedor')
        self.comprador_b = criar_usuario('comprador-b', 'Comprador')
        self.motorista_b = criar_usuario('motorista-b', 'Motorista')

        fruta = Fruit.objects.create(name='Manga')
        FruitParameter.objects.create(
            fruit=fruta, temperature_min_c=Decimal('8'), temperature_max_c=Decimal('12'),
            humidity_min_pct=Decimal('80'), humidity_max_pct=Decimal('90'), impact_max_g=Decimal('2.5'),
        )
        self.fruta = fruta
        origem = Location.objects.create(name='Fazenda', type='farm')
        destino = Location.objects.create(name='CD', type='distribution_center')
        veiculo = Vehicle.objects.create(plate='ABC1D23')

        self.placa_a = Device.objects.create(uid='A', name='Placa A', owner=self.vendedor_a)
        self.placa_b = Device.objects.create(uid='B', name='Placa B', owner=self.vendedor_b)

        def viagem(vendedor, placa, **extra):
            return Shipment.objects.create(
                origin=origem, destination=destino, vehicle=veiculo, device=placa,
                created_by=vendedor, status='active', started_at=timezone.now() - timedelta(hours=1), **extra,
            )

        self.viagem_a = viagem(self.vendedor_a, self.placa_a)
        self.viagem_b = viagem(self.vendedor_b, self.placa_b, buyer=self.comprador_b, driver=self.motorista_b)
        self.item_b = ShipmentItem.objects.create(shipment=self.viagem_b, fruit=fruta, lot='L1', quantity_kg=10)
        self.leitura_b = Reading.objects.create(
            shipment=self.viagem_b, device=self.placa_b, sequence=1, recorded_at=timezone.now(),
            temperature_c=Decimal('15'), humidity_pct=Decimal('85'),
        )
        self.alerta_b = Alert.objects.create(
            shipment=self.viagem_b, reading=self.leitura_b, type='temperature', severity='warning',
            message='teste', measured_value=Decimal('15'), violated_limit=Decimal('12'),
        )

    def como(self, usuario):
        self.client.force_authenticate(usuario)

    # --- O usuario A NAO alcanca nada do B -------------------------------------

    def test_a_nao_le_nada_do_b(self):
        self.como(self.vendedor_a)
        vb = self.viagem_b.id
        for rota in [
            f'/api/v1/shipments/{vb}', f'/api/v1/shipments/{vb}/summary',
            f'/api/v1/shipments/{vb}/readings', f'/api/v1/shipments/{vb}/shocks',
            f'/api/v1/shipments/{vb}/alerts', f'/api/v1/devices/{self.placa_b.id}',
            f'/api/v1/readings/{self.leitura_b.id}', f'/api/v1/alerts/{self.alerta_b.id}',
            f'/api/v1/shipment-items/{self.item_b.id}',
        ]:
            with self.subTest(rota=rota):
                self.assertEqual(self.client.get(rota).status_code, 404)

    def test_a_nao_altera_nem_comanda_nada_do_b(self):
        self.como(self.vendedor_a)
        vb = self.viagem_b.id
        self.assertEqual(self.client.patch(f'/api/v1/shipments/{vb}', {}, format='json').status_code, 404)
        # Apagar: o papel Vendedor nem tem permissao de apagar viagem (403 antes de olhar o dono).
        self.assertIn(self.client.delete(f'/api/v1/shipments/{vb}').status_code, (403, 404))
        self.assertEqual(self.client.post(f'/api/v1/shipments/{vb}/finish').status_code, 404)
        self.assertEqual(self.client.post(f'/api/v1/shipments/{vb}/start').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/v1/devices/{self.placa_b.id}', {'name': 'x'}, format='json').status_code, 404)
        self.assertEqual(self.client.post(f'/api/v1/alerts/{self.alerta_b.id}/ack').status_code, 404)
        self.viagem_b.refresh_from_db()
        self.assertEqual(self.viagem_b.status, 'active')  # nada mudou

    def test_listas_e_filtros_nao_vazam(self):
        self.como(self.vendedor_a)
        self.assertEqual(ids(self.client.get('/api/v1/shipments')), [self.viagem_a.id])
        self.assertEqual(ids(self.client.get('/api/v1/readings', {'shipment': self.viagem_b.id})), [])
        self.assertEqual(ids(self.client.get('/api/v1/alerts', {'shipment': self.viagem_b.id})), [])
        self.assertEqual(ids(self.client.get('/api/v1/devices')), [self.placa_a.id])

    def test_a_nao_usa_placa_nem_viagem_do_b_pelo_corpo(self):
        """Contorno: mandar o ID do B no CORPO da requisicao, e nao na URL."""
        self.como(self.vendedor_a)
        dados = {
            'origin': self.viagem_a.origin_id, 'destination': self.viagem_a.destination_id,
            'vehicle': self.viagem_a.vehicle_id, 'device': self.placa_b.id,
            'started_at': timezone.now().isoformat(),
        }
        self.assertEqual(self.client.post('/api/v1/shipments', dados, format='json').status_code, 403)
        item = {'shipment': self.viagem_b.id, 'fruit': self.fruta.id, 'lot': 'X', 'quantity_kg': '5'}
        self.assertEqual(self.client.post('/api/v1/shipment-items', item, format='json').status_code, 403)

    def test_bloqueio_vai_para_o_log_com_codigo_de_missao(self):
        self.como(self.vendedor_a)
        with self.assertLogs('seguranca', level='WARNING') as log:
            self.client.get(f'/api/v1/shipments/{self.viagem_b.id}')
        self.assertIn('[TST123] IDOR bloqueado', log.output[0])
        self.assertIn('vendedor-a@teste.local', log.output[0])

    # --- Os participantes da viagem do B continuam usando --------------------

    def test_dono_usa_normalmente(self):
        self.como(self.vendedor_b)
        self.assertEqual(self.client.get(f'/api/v1/shipments/{self.viagem_b.id}/readings').status_code, 200)
        self.assertEqual(self.client.get(f'/api/v1/devices/{self.placa_b.id}').status_code, 200)

    def test_motorista_ve_e_finaliza_mas_nao_altera_a_viagem(self):
        self.como(self.motorista_b)
        self.assertEqual(self.client.get(f'/api/v1/shipments/{self.viagem_b.id}').status_code, 200)
        self.assertEqual(self.client.patch(f'/api/v1/shipments/{self.viagem_b.id}', {}, format='json').status_code, 403)
        self.assertEqual(self.client.get(f'/api/v1/devices/{self.placa_b.id}').status_code, 404)
        self.assertEqual(self.client.post(f'/api/v1/shipments/{self.viagem_b.id}/finish').status_code, 200)
        self.assertEqual(ids(self.client.get('/api/v1/shipments/current')), [self.viagem_b.id])

    def test_comprador_ve_e_confirma_mas_nao_comanda(self):
        self.como(self.comprador_b)
        self.assertEqual(self.client.get(f'/api/v1/shipments/{self.viagem_b.id}/summary').status_code, 200)
        self.assertEqual(self.client.post(f'/api/v1/shipments/{self.viagem_b.id}/finish').status_code, 403)
        Shipment.objects.filter(pk=self.viagem_b.id).update(status='delivered')
        resposta = self.client.post(f'/api/v1/shipments/{self.viagem_b.id}/confirm', {'condition': 'good'}, format='json')
        self.assertEqual(resposta.status_code, 200, resposta.data)

    def test_terceiro_usuario_novo_nao_enxerga_nada(self):
        """Exemplo de alteracao ao vivo do professor: um usuario novo nao ve nada dos outros."""
        self.como(criar_usuario('novo', 'Vendedor'))
        self.assertEqual(ids(self.client.get('/api/v1/shipments')), [])
        self.assertEqual(ids(self.client.get('/api/v1/devices')), [])
        self.assertEqual(self.client.get(f'/api/v1/shipments/{self.viagem_a.id}').status_code, 404)

    def test_plataforma_ve_tudo(self):
        self.como(User.objects.create_superuser('plataforma', 'p@teste.local', 'senha-de-teste-123'))
        self.assertEqual(len(ids(self.client.get('/api/v1/shipments'))), 2)
