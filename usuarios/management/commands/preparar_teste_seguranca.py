"""
Prepara os dados SINTETICOS usados nos testes de seguranca (pasta seguranca/testes).

Cria (ou reaproveita) dois usuarios de teste, cada um com a sua placa, a sua
viagem em andamento e algumas leituras:

    vendedor-a@teste.local  ->  placa TESTE-A  ->  viagem com lote TESTE-IDOR-A
    vendedor-b@teste.local  ->  placa TESTE-B  ->  viagem com lote TESTE-IDOR-B

Pode rodar quantas vezes quiser: a viagem de cada um volta para "em andamento"
(os testes encerram a viagem do B de proposito).

Com --terceiro, cria tambem o vendedor-c@teste.local, SEM placa e SEM viagem
(alteracao ao vivo: "um usuario novo nao enxerga os dispositivos dos outros";
depois rode  python seguranca/testes/teste_terceiro_usuario.py).

Uso:
    (PowerShell)  $env:TESTE_SENHA = "uma-senha-forte-so-de-teste"
    python manage.py preparar_teste_seguranca

A senha vem da variavel TESTE_SENHA e nunca fica no codigo.

Depois do 2FA: defina tambem TESTE_TOTP_SEGREDO (um segredo base32, ex.: gerado
com  python -c "import pyotp; print(pyotp.random_base32())"). Os dois usuarios
ficam com o 2FA ATIVO usando esse segredo, e os scripts de teste calculam o
codigo com ele. Cadastre o mesmo segredo num autenticador se quiser ver os codigos.
"""

import os
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from dominio.models import Fruit, Location, Vehicle
from iot.models import Device, Reading
from transporte.models import FinalInspection, Shipment, ShipmentItem
from usuarios.dois_fatores import _cifrar
from usuarios.models import CodigoRecuperacao, SegundoFator

# Grupo que os usuarios de teste recebem: Vendedor (cria e comanda as proprias viagens).
GRUPO_TESTE = 'Vendedor'

USUARIOS = [
    # (letra, e-mail, placa, placa do veiculo)
    ('A', 'vendedor-a@teste.local', 'TESTE-A', 'TST0A00'),
    ('B', 'vendedor-b@teste.local', 'TESTE-B', 'TST0B00'),
]
TERCEIRO = ('C', 'vendedor-c@teste.local')  # sem placa e sem viagem


class Command(BaseCommand):
    help = 'Cria os usuarios, placas, viagens e leituras sinteticos dos testes de seguranca.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--terceiro', action='store_true',
            help='Cria tambem o vendedor-c@teste.local, sem placa e sem viagem.',
        )

    def handle(self, *args, **options):
        senha = os.environ.get('TESTE_SENHA', '')
        if len(senha) < 10:
            raise CommandError('Defina a variavel TESTE_SENHA (minimo 10 caracteres) antes de rodar.')

        grupo = Group.objects.filter(name=GRUPO_TESTE).first()
        if grupo is None:
            raise CommandError(f'Grupo "{GRUPO_TESTE}" nao existe. Rode antes: python manage.py criar_grupos')

        fruta = Fruit.objects.filter(is_active=True).order_by('id').first()
        if fruta is None:
            raise CommandError('Nenhuma fruta cadastrada. Rode antes: python manage.py carregar_limites_iniciais')

        with transaction.atomic():
            for letra, email, uid, placa_veiculo in USUARIOS:
                self._preparar(letra, email, uid, placa_veiculo, senha, grupo, fruta)
            if options['terceiro']:
                letra, email = TERCEIRO
                self._usuario(letra, email, senha, grupo)
                self.stdout.write(self.style.SUCCESS(f'Usuario {letra}: {email} | sem placa e sem viagem'))

    def _usuario(self, letra, email, senha, grupo):
        """Usuario de teste: e-mail e o login; senha (e 2FA) redefinidos a cada execucao."""
        usuario, _ = User.objects.get_or_create(
            username=email, defaults={'email': email, 'first_name': f'Vendedor {letra}'},
        )
        usuario.email = email
        usuario.set_password(senha)
        usuario.save()
        usuario.groups.set([grupo])

        # 2FA dos usuarios de teste (so quando TESTE_TOTP_SEGREDO estiver definido).
        segredo = os.environ.get('TESTE_TOTP_SEGREDO', '').strip().upper()
        if segredo:
            SegundoFator.objects.update_or_create(
                usuario=usuario,
                defaults={'segredo_cifrado': _cifrar(segredo), 'ativo': True,
                          'ultimo_passo': None, 'ativado_em': timezone.now()},
            )
            CodigoRecuperacao.objects.filter(usuario=usuario).delete()
        return usuario

    def _preparar(self, letra, email, uid, placa_veiculo, senha, grupo, fruta):
        # 1) Usuario.
        usuario = self._usuario(letra, email, senha, grupo)

        # 2) Placa, locais e veiculo do usuario.
        placa, _ = Device.objects.get_or_create(uid=uid, defaults={'name': f'Placa de teste {letra}'})
        placa.owner = usuario  # a placa de teste e do proprio vendedor
        placa.save(update_fields=['owner'])
        origem, _ = Location.objects.get_or_create(name=f'Fazenda Teste {letra}', defaults={'type': 'farm'})
        destino, _ = Location.objects.get_or_create(
            name=f'CD Teste {letra}', defaults={'type': 'distribution_center'},
        )
        veiculo, _ = Vehicle.objects.get_or_create(plate=placa_veiculo, defaults={'model': 'Teste'})
        # Locais e veiculo tambem sao do usuario (protecao contra IDOR nos cadastros).
        for cadastro in (origem, destino, veiculo):
            cadastro.owner = usuario
            cadastro.save(update_fields=['owner'])

        # 3) Viagem do usuario (created_by = ele), sempre "em andamento".
        viagem = Shipment.objects.filter(device=placa, created_by=usuario).order_by('id').first()
        if viagem is None:
            viagem = Shipment.objects.create(
                origin=origem, destination=destino, vehicle=veiculo, device=placa,
                created_by=usuario, status='planned', started_at=timezone.now(),
            )
        FinalInspection.objects.filter(shipment=viagem).delete()  # desfaz o "encerrar" do teste anterior
        viagem.status = 'active'
        viagem.started_at = timezone.now() - timedelta(hours=1)
        viagem.ended_at = None
        viagem.save()

        ShipmentItem.objects.get_or_create(
            shipment=viagem, fruit=fruta, lot=f'TESTE-IDOR-{letra}',
            defaults={'quantity_kg': Decimal('100')},
        )

        # 4) Cinco leituras sinteticas na viagem (so cria se ainda nao existem).
        if not viagem.readings.exists():
            ultimo = Reading.objects.filter(device=placa).order_by('-sequence').first()
            sequencia = ultimo.sequence if ultimo else 0
            for i in range(5):
                sequencia += 1
                Reading.objects.create(
                    shipment=viagem, device=placa, sequence=sequencia,
                    recorded_at=timezone.now() - timedelta(minutes=50 - i * 10),
                    temperature_c=Decimal('10.5') + i, humidity_pct=Decimal('85'),
                )

        self.stdout.write(self.style.SUCCESS(
            f'Usuario {letra}: {email} | placa {uid} (id {placa.id}) | viagem id {viagem.id} em andamento'
        ))
