"""
POST /api/v1/chat

Corpo:  {"message": "Como esta a temperatura da minha carga?",
         "shipment_id": 13,                     (opcional: foca numa viagem)
         "history": [{"role": "user"|"model", "text": "..."}]}   (opcional, curto)

Resposta 200: {"answer": "...", "shipments": [13]}
Erros (sempre com "detail" em portugues e um "code" para o front):
    400 invalid_message            mensagem vazia ou longa demais
    404                            viagem que nao existe ou nao e do usuario (IDOR)
    429 (sem code)                 o usuario mandou mensagens demais (limite nosso; ver Retry-After)
    429 assistant_quota_exceeded   acabou a cota gratuita do Gemini
    503 assistant_unavailable      Gemini fora do ar / demorou / sem chave configurada
"""

from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, Throttled
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from transporte.models import Shipment
from usuarios.acesso import registrar_bloqueio

from .contexto import montar_contexto, viagens_do_contexto
from .gemini import ErroAssistente, perguntar

MENSAGENS = {
    'cota': (status.HTTP_429_TOO_MANY_REQUESTS, 'assistant_quota_exceeded',
             'O limite gratuito do assistente foi atingido por agora. Tente novamente mais tarde.'),
    'sem_chave': (status.HTTP_503_SERVICE_UNAVAILABLE, 'assistant_unavailable',
                  'O assistente não está disponível no momento.'),
    'configuracao': (status.HTTP_503_SERVICE_UNAVAILABLE, 'assistant_unavailable',
                     'O assistente não está disponível no momento.'),
    'indisponivel': (status.HTTP_503_SERVICE_UNAVAILABLE, 'assistant_unavailable',
                     'O assistente demorou para responder. Tente de novo em instantes.'),
}


class Historico(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'model'])
    text = serializers.CharField(max_length=1000)


class ChatInput(serializers.Serializer):
    message = serializers.CharField(max_length=1000, trim_whitespace=True)
    shipment_id = serializers.IntegerField(required=False, min_value=1)
    history = Historico(many=True, required=False)

    def validate_history(self, valor):
        return valor[-6:]  # so as ultimas trocas: contexto curto, menos tokens


class ChatView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chat'

    def throttled(self, request, wait):
        # Limite NOSSO (por usuario). O cabecalho Retry-After diz quantos segundos esperar.
        raise Throttled(wait, detail='Você enviou muitas mensagens seguidas. Aguarde um pouco.')

    @extend_schema(request=ChatInput, responses=inline_serializer('ChatResposta', {
        'answer': serializers.CharField(), 'shipments': serializers.ListField(child=serializers.IntegerField()),
    }))
    def post(self, request):
        entrada = ChatInput(data=request.data)
        if not entrada.is_valid():
            return Response({'detail': 'Escreva uma mensagem de até 1000 caracteres.', 'code': 'invalid_message'},
                            status=status.HTTP_400_BAD_REQUEST)
        dados = entrada.validated_data

        viagem_id = dados.get('shipment_id')
        viagens = viagens_do_contexto(request.user, viagem_id)
        if viagem_id is not None and not viagens:
            # Mesma regra do IDOR: viagem de outro usuario "nao existe" para quem pede.
            if Shipment.objects.filter(pk=viagem_id).exists():
                registrar_bloqueio(request, 'shipment', viagem_id, motivo='chat pediu viagem de outro usuario')
            raise NotFound('Viagem não encontrada.')

        try:
            resposta = perguntar(
                montar_contexto(request.user, viagens), dados['message'], dados.get('history', []),
            )
        except ErroAssistente as erro:
            if erro.codigo == 'bloqueado':
                resposta = 'Não posso responder a essa pergunta. Pergunte sobre as suas viagens e cargas.'
            else:
                codigo_http, codigo, texto = MENSAGENS[erro.codigo]
                return Response({'detail': texto, 'code': codigo}, status=codigo_http)

        return Response({'answer': resposta, 'shipments': [viagem.id for viagem in viagens]})
