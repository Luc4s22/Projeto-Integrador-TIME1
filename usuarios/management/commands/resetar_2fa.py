"""
Remove o 2FA de um usuario (perdeu o celular e os codigos de recuperacao).
No proximo login ele cadastra o autenticador de novo.

Uso:  python manage.py resetar_2fa pessoa@exemplo.com
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from usuarios.models import CodigoRecuperacao, SegundoFator


class Command(BaseCommand):
    help = 'Apaga o 2FA e os codigos de recuperacao de um usuario.'

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, *args, **options):
        usuario = get_user_model().objects.filter(email__iexact=options['email']).first()
        if usuario is None:
            raise CommandError('Usuario nao encontrado.')
        SegundoFator.objects.filter(usuario=usuario).delete()
        CodigoRecuperacao.objects.filter(usuario=usuario).delete()
        self.stdout.write(self.style.SUCCESS(f'2FA de {usuario.email} removido.'))
