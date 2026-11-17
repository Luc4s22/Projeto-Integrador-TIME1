"""
Invalida os codigos de recuperacao ainda nao usados de um usuario
(ex.: suspeita de que a lista vazou). O 2FA continua ativo.

Uso:  python manage.py invalidar_codigos_recuperacao pessoa@exemplo.com
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from usuarios import dois_fatores


class Command(BaseCommand):
    help = 'Invalida os codigos de recuperacao nao usados de um usuario.'

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, *args, **options):
        usuario = get_user_model().objects.filter(email__iexact=options['email']).first()
        if usuario is None:
            raise CommandError('Usuario nao encontrado.')
        quantidade = dois_fatores.invalidar_codigos_recuperacao(usuario)
        self.stdout.write(self.style.SUCCESS(f'{quantidade} codigos de recuperacao invalidados.'))
