"""
Testes do chat. O Gemini e SIMULADO (mock): os testes nao gastam cota nem
precisam de internet, e da para provocar cada erro (cota, queda, bloqueio).
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from dominio.models import Location, Vehicle
from iot.models import Device
from transporte.models import Shipment


def resposta_gemini(status=200, texto='Sua carga está a 10 °C.', corpo=None):
    simulada = MagicMock(status_code=status, text='')
    simulada.json.return_value = corpo if corpo is not None else {
        'candidates': [{'content': {'parts': [{'text': texto}]}, 'finishReason': 'STOP'}],
    }
    return simulada


@override_settings(GEMINI_API_KEY='chave-de-teste', SECURITY_MISSION_CODE='TST123')
class ChatTest(APITestCase):

    def setUp(self):
        cache.clear()
        call_command('criar_grupos', verbosity=0)
        grupo = Group.objects.get(name='Vendedor')
        self.ana = User.objects.create_user('ana', 'ana@teste.local', 'x')
        self.bia = User.objects.create_user('bia', 'bia@teste.local', 'x')
        self.ana.groups.add(grupo)
        self.bia.groups.add(grupo)
        veiculo = Vehicle.objects.create(plate='ABC1D23')

        def viagem(dono, uid, origem):
            return Shipment.objects.create(
                origin=Location.objects.create(name=origem, type='farm'),
                destination=Location.objects.create(name=f'CD de {origem}', type='distribution_center'),
                vehicle=veiculo, device=Device.objects.create(uid=uid, name=uid, owner=dono),
                created_by=dono, status='active', started_at=timezone.now() - timedelta(hours=1),
            )

        self.viagem_ana = viagem(self.ana, 'PLACA-ANA', 'Fazenda da Ana')
        self.viagem_bia = viagem(self.bia, 'PLACA-BIA', 'Fazenda da Bia')
        self.client.force_authenticate(self.ana)

    def perguntar(self, **corpo):
        return self.client.post('/api/v1/chat', {'message': 'Como está minha carga?', **corpo}, format='json')

    @patch('assistente.gemini.requests.post')
    def test_responde_e_contexto_tem_so_as_viagens_do_usuario(self, chamada):
        chamada.return_value = resposta_gemini()
        resposta = self.perguntar()
        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(resposta.json()['data']['shipments'], [self.viagem_ana.id])
        enviado = str(chamada.call_args.kwargs['json'])
        self.assertIn('Fazenda da Ana', enviado)
        self.assertNotIn('Fazenda da Bia', enviado)       # nada do outro usuario vai para o Gemini
        self.assertNotIn('ana@teste.local', enviado)      # LGPD: sem e-mail
        self.assertEqual(chamada.call_args.kwargs['headers']['x-goog-api-key'], 'chave-de-teste')

    @patch('assistente.gemini.requests.post')
    def test_viagem_de_outro_usuario_da_404(self, chamada):
        resposta = self.perguntar(shipment_id=self.viagem_bia.id)
        self.assertEqual(resposta.status_code, 404)
        chamada.assert_not_called()

    @patch('assistente.gemini.requests.post')
    def test_cota_esgotada_vira_429_com_mensagem_clara(self, chamada):
        chamada.return_value = resposta_gemini(status=429)
        resposta = self.perguntar()
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(resposta.json()['code'], 'assistant_quota_exceeded')

    @patch('assistente.gemini.requests.post', side_effect=requests.Timeout)
    def test_gemini_demorando_vira_503(self, _chamada):
        resposta = self.perguntar()
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(resposta.json()['code'], 'assistant_unavailable')

    @patch('assistente.gemini.requests.post')
    def test_chave_invalida_vira_503_sem_expor_detalhes(self, chamada):
        chamada.return_value = resposta_gemini(status=400)
        resposta = self.perguntar()
        self.assertEqual(resposta.status_code, 503)
        self.assertNotIn('chave-de-teste', resposta.content.decode())

    @override_settings(GEMINI_API_KEY='')
    def test_sem_chave_configurada_vira_503(self):
        self.assertEqual(self.perguntar().status_code, 503)

    @patch('assistente.gemini.requests.post')
    def test_resposta_bloqueada_vira_mensagem_educada(self, chamada):
        chamada.return_value = resposta_gemini(corpo={'promptFeedback': {'blockReason': 'SAFETY'}})
        resposta = self.perguntar()
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('Não posso responder', resposta.json()['data']['answer'])

    def test_mensagem_vazia_ou_longa_e_recusada(self):
        self.assertEqual(self.perguntar(message='').status_code, 400)
        self.assertEqual(self.perguntar(message='x' * 1001).status_code, 400)

    @patch('assistente.gemini.requests.post')
    def test_limite_de_mensagens_por_usuario(self, chamada):
        chamada.return_value = resposta_gemini()
        for _ in range(5):
            self.perguntar()
        resposta = self.perguntar()
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(chamada.call_count, 5)  # a 6a nem chegou ao Gemini

    def test_exige_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.perguntar().status_code, 401)
