"""
Cria a tabela do cache no banco (settings.CACHES). E nela que ficam os contadores
do limite de tentativas: assim todos os workers do gunicorn compartilham o mesmo
contador. Rodar o `migrate` (o build.sh do Render ja roda) basta.
"""

from django.core.management import call_command
from django.db import migrations


def criar_tabela(apps, schema_editor):
    call_command('createcachetable', verbosity=0)


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_revogar_tokens_anteriores_ao_2fa'),
    ]

    operations = [
        migrations.RunPython(criar_tabela, migrations.RunPython.noop),
    ]
