
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase

from dominio.models import Fruit, FruitParameter
from piADS04.tests_utils import montar_cenario

from .models import Shipment, ShipmentItem, FinalInspection
from .services import IncompatibleCargo, fruit_range, fruit_range_for


class FruitRangeTest(TestCase):

    def setUp(self):
        self.c = montar_cenario()

    def test_uma_fruta_usa_a_propria_faixa(self):
        faixa = fruit_range(self.c['viagem'])

        self.assertEqual(
            (faixa.temperature_min_c, faixa.temperature_max_c),
            (Decimal('8'), Decimal('12'))
        )

        self.assertEqual(
            faixa.impact_max_g,
            Decimal('2.5')
        )

    def test_carga_mista_usa_a_intersecao_e_o_mais_rigoroso(self):
        uva = Fruit.objects.create(name='Uva')

        FruitParameter.objects.create(
            fruit=uva,
            temperature_min_c=Decimal('10'),
            temperature_max_c=Decimal('14'),
            humidity_min_pct=Decimal('85'),
            humidity_max_pct=Decimal('95'),
            temperature_critical_margin_c=Decimal('2'),
            impact_max_g=Decimal('1.5'),
        )

        faixa = fruit_range_for([
            self.c['fruta'].id,
            uva.id
        ])

        self.assertEqual(
            (faixa.temperature_min_c, faixa.temperature_max_c),
            (Decimal('10'), Decimal('12'))
        )

        self.assertEqual(
            (faixa.humidity_min_pct, faixa.humidity_max_pct),
            (Decimal('85'), Decimal('90'))
        )

        self.assertEqual(
            faixa.temperature_critical_margin_c,
            Decimal('2')
        )

        self.assertEqual(
            faixa.impact_max_g,
            Decimal('1.5')
        )

    def test_frutas_sem_faixa_em_comum_levantam_erro(self):
        gelada = Fruit.objects.create(
            name='Fruta gelada'
        )

        FruitParameter.objects.create(
            fruit=gelada,
            temperature_min_c=Decimal('0'),
            temperature_max_c=Decimal('4'),
            humidity_min_pct=Decimal('90'),
            humidity_max_pct=Decimal('95'),
        )

        with self.assertRaises(IncompatibleCargo):
            fruit_range_for([
                self.c['fruta'].id,
                gelada.id
            ])

    def test_sem_parametros_ativos_devolve_none(self):
        outra = Fruit.objects.create(
            name='Sem limite'
        )

        self.assertIsNone(
            fruit_range_for([outra.id])
        )


class ShipmentLifecycleTest(APITestCase):

    def setUp(self):
        self.c = montar_cenario(status='planned')

        self.client.force_authenticate(
            User.objects.create_superuser(
                'root',
                'root@example.com',
                'x'
            )
        )

    def test_iniciar_e_encerrar(self):
        url = f"/api/v1/shipments/{self.c['viagem'].id}"

        # Iniciar viagem
        resposta_inicio = self.client.post(
            f'{url}/start'
        )

        self.assertEqual(
            resposta_inicio.status_code,
            200
        )

        self.assertEqual(
            resposta_inicio.data['status'],
            'active'
        )

        # Motorista finaliza: a viagem fica "entregue, aguardando confirmação"
        resposta_fim = self.client.post(f'{url}/finish')
        self.assertEqual(resposta_fim.status_code, 200, resposta_fim.data)
        self.assertEqual(resposta_fim.data['status'], 'delivered')

        # Comprador confirma o recebimento com a avaliação
        resposta_confirmacao = self.client.post(
            f'{url}/confirm',
            {
                'condition': 'good',
                'notes': 'Frutas entregues em boas condições.'
            },
            format='json'
        )

        self.assertEqual(
            resposta_confirmacao.status_code,
            200,
            resposta_confirmacao.data
        )

        # Conferir o estado atualizado no banco
        viagem = Shipment.objects.get(
            pk=self.c['viagem'].id
        )

        self.assertEqual(
            viagem.status,
            'completed'
        )

        self.assertIsNotNone(
            viagem.ended_at
        )

        # Conferir a inspeção final registrada
        avaliacao = FinalInspection.objects.get(
            shipment=viagem
        )

        self.assertEqual(
            avaliacao.condition,
            'good'
        )

        self.assertEqual(
            avaliacao.notes,
            'Frutas entregues em boas condições.'
        )

    def test_dispositivo_nao_fica_em_duas_viagens_ativas(self):
        outra = Shipment.objects.create(
            origin=self.c['fazenda'],
            destination=self.c['centro'],
            vehicle=self.c['veiculo'],
            device=self.c['dispositivo'],
            started_at=self.c['inicio'],
        )

        ShipmentItem.objects.create(
            shipment=outra,
            fruit=self.c['fruta'],
            lot='L2',
            quantity_kg=Decimal('10')
        )

        self.assertEqual(
            self.client.post(
                f"/api/v1/shipments/{self.c['viagem'].id}/start"
            ).status_code,
            200
        )

        resposta = self.client.post(
            f'/api/v1/shipments/{outra.id}/start'
        )

        self.assertEqual(
            resposta.status_code,
            400
        )

        self.assertIn(
            'outra viagem',
            resposta.data['detail']
        )

    def test_quem_cria_a_viagem_fica_registrado(self):
        resposta = self.client.post(
            '/api/v1/shipments',
            {
                'origin': self.c['fazenda'].id,
                'destination': self.c['centro'].id,
                'vehicle': self.c['veiculo'].id,
                'device': self.c['dispositivo'].id,
                'started_at': '2026-11-01T10:00:00Z',
            }
        )

        self.assertEqual(
            resposta.status_code,
            201
        )

        self.assertEqual(
            Shipment.objects.get(
                pk=resposta.data['id']
            ).created_by.username,
            'root'
        )


class ShipmentCreateWithItemsTest(APITestCase):

    def setUp(self):
        self.c = montar_cenario(status='planned')

        self.client.force_authenticate(
            User.objects.create_superuser(
                'admin_teste',
                'admin_teste@example.com',
                'senha-teste'
            )
        )

    def test_criar_viagem_com_itens(self):
        quantidade_antes = Shipment.objects.count()

        resposta = self.client.post(
            '/api/v1/shipments',
            {
                'origin': self.c['fazenda'].id,
                'destination': self.c['centro'].id,
                'vehicle': self.c['veiculo'].id,
                'device': self.c['dispositivo'].id,
                'started_at': '2026-11-15T10:00:00Z',
                'items': [
                    {
                        'fruit': self.c['fruta'].id,
                        'lot': 'LOTE-001',
                        'quantity_kg': '500.00'
                    }
                ]
            },
            format='json'
        )

        self.assertEqual(
            resposta.status_code,
            201,
            resposta.data
        )

        self.assertEqual(
            Shipment.objects.count(),
            quantidade_antes + 1
        )

        viagem = Shipment.objects.get(
            pk=resposta.data['id']
        )

        self.assertEqual(
            viagem.items.count(),
            1
        )

        self.assertEqual(
            viagem.items.first().lot,
            'LOTE-001'
        )

    def test_rejeitar_lote_duplicado(self):
        quantidade_antes = Shipment.objects.count()

        resposta = self.client.post(
            '/api/v1/shipments',
            {
                'origin': self.c['fazenda'].id,
                'destination': self.c['centro'].id,
                'vehicle': self.c['veiculo'].id,
                'device': self.c['dispositivo'].id,
                'started_at': '2026-11-15T10:00:00Z',
                'items': [
                    {
                        'fruit': self.c['fruta'].id,
                        'lot': 'LOTE-001',
                        'quantity_kg': '100.00'
                    },
                    {
                        'fruit': self.c['fruta'].id,
                        'lot': 'LOTE-001',
                        'quantity_kg': '200.00'
                    }
                ]
            },
            format='json'
        )

        self.assertEqual(
            resposta.status_code,
            400
        )

        self.assertEqual(
            Shipment.objects.count(),
            quantidade_antes
        )


class FluxoEntregaTest(APITestCase):
    """
    Fluxo novo: o motorista finaliza (active -> delivered) e o comprador
    confirma o recebimento (delivered -> completed).
    """

    def setUp(self):
        from django.core.management import call_command
        call_command('criar_grupos', verbosity=0)
        self.c = montar_cenario()
        self.url = f"/api/v1/shipments/{self.c['viagem'].id}"
        self.motorista = self._usuario('motorista', 'Motorista')
        self.comprador = self._usuario('comprador', 'Comprador')
        Shipment.objects.filter(pk=self.c['viagem'].id).update(driver=self.motorista, buyer=self.comprador)

    def _usuario(self, nome, grupo):
        from django.contrib.auth.models import Group
        usuario = User.objects.create_user(nome, f'{nome}@teste.local', 'senha-de-teste-123')
        usuario.groups.add(Group.objects.get(name=grupo))
        return usuario

    def test_motorista_finaliza_e_viagem_fica_entregue(self):
        self.client.force_authenticate(self.motorista)
        resposta = self.client.post(f'{self.url}/finish')
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['status'], 'delivered')
        self.assertIsNotNone(Shipment.objects.get(pk=self.c['viagem'].id).ended_at)

    def test_motorista_nao_confirma_recebimento(self):
        self.client.force_authenticate(self.motorista)
        self.client.post(f'{self.url}/finish')
        resposta = self.client.post(f'{self.url}/confirm', {'condition': 'good'}, format='json')
        self.assertEqual(resposta.status_code, 403)

    def test_comprador_confirma_e_viagem_conclui(self):
        Shipment.objects.filter(pk=self.c['viagem'].id).update(status='delivered')
        self.client.force_authenticate(self.comprador)
        resposta = self.client.post(f'{self.url}/confirm', {'condition': 'good'}, format='json')
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(Shipment.objects.get(pk=self.c['viagem'].id).status, 'completed')
        self.assertTrue(FinalInspection.objects.filter(shipment=self.c['viagem']).exists())

    def test_avaria_sem_foto_e_recusada(self):
        Shipment.objects.filter(pk=self.c['viagem'].id).update(status='delivered')
        self.client.force_authenticate(self.comprador)
        resposta = self.client.post(f'{self.url}/confirm', {'condition': 'damaged'}, format='json')
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(Shipment.objects.get(pk=self.c['viagem'].id).status, 'delivered')

    def test_nao_confirma_viagem_ainda_em_andamento(self):
        self.client.force_authenticate(self.comprador)
        resposta = self.client.post(f'{self.url}/confirm', {'condition': 'good'}, format='json')
        self.assertEqual(resposta.status_code, 400)

    def test_motorista_da_viagem_precisa_ter_papel_motorista(self):
        admin = User.objects.create_superuser('plataforma', 'plataforma@teste.local', 'senha-de-teste-123')
        self.client.force_authenticate(admin)
        resposta = self.client.patch(self.url, {'driver': self.comprador.id}, format='json')
        self.assertEqual(resposta.status_code, 400)
        resposta = self.client.patch(self.url, {'driver': self.motorista.id, 'buyer': self.comprador.id}, format='json')
        self.assertEqual(resposta.status_code, 200, resposta.data)
