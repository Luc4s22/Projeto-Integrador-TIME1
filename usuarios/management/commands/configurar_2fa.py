"""
Configura o 2FA de um usuario PELO TERMINAL (uso da plataforma).

Serve para o primeiro superusuario (que precisa do codigo para entrar no /admin/)
e para quando alguem troca de celular.

Uso:  python manage.py configurar_2fa voce@exemplo.com
      1. escaneie o QR Code que aparece no terminal com o aplicativo autenticador;
      2. digite o codigo de 6 digitos que o aplicativo mostrar;
      3. guarde os 10 codigos de recuperacao (eles nao aparecem de novo).
"""

import qrcode
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from usuarios import dois_fatores


class Command(BaseCommand):
    help = 'Cadastra (ou recadastra) o autenticador 2FA de um usuario pelo terminal.'

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, *args, **options):
        usuario = get_user_model().objects.filter(email__iexact=options['email']).first()
        if usuario is None:
            raise CommandError('Usuario nao encontrado.')

        dados = dois_fatores.iniciar_cadastro(usuario)  # segredo novo; o anterior deixa de valer
        qr = qrcode.QRCode(border=1)
        qr.add_data(dados['otpauth_uri'])
        qr.print_ascii(invert=True)
        self.stdout.write(f'Ou digite no aplicativo a chave: {dados["secret"]}')

        codigo = input('Codigo de 6 digitos que o aplicativo mostra: ')
        codigos = dois_fatores.ativar(usuario, codigo)
        if codigos is None:
            raise CommandError('Codigo invalido. Rode o comando de novo.')

        self.stdout.write(self.style.SUCCESS('2FA ativado. Codigos de recuperacao (guarde, uso unico):'))
        for item in codigos:
            self.stdout.write(f'  {item}')
