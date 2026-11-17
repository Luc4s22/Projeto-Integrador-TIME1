"""
Revoga os refresh tokens emitidos ANTES do 2FA existir.

Sem isto, quem tinha feito login so com a senha (inclusive um atacante) seguiria
renovando o acesso pelo /auth/refresh por ate 1 dia, sem nunca passar pelo codigo.
Depois do deploy, todo mundo entra de novo, ja com o segundo fator.
"""

from django.db import migrations


def revogar(apps, schema_editor):
    OutstandingToken = apps.get_model('token_blacklist', 'OutstandingToken')
    BlacklistedToken = apps.get_model('token_blacklist', 'BlacklistedToken')
    ja_revogados = set(BlacklistedToken.objects.values_list('token_id', flat=True))
    BlacklistedToken.objects.bulk_create([
        BlacklistedToken(token_id=token_id)
        for token_id in OutstandingToken.objects.values_list('id', flat=True)
        if token_id not in ja_revogados
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_segundo_fator'),
        ('token_blacklist', '0013_alter_blacklistedtoken_options_and_more'),
    ]

    operations = [
        migrations.RunPython(revogar, migrations.RunPython.noop),
    ]
