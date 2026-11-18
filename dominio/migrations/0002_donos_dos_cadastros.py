"""
Locais e veiculos ganham dono (protecao contra IDOR).

Os cadastros que ja existem recebem como dono o vendedor das viagens que os
usam -- quando TODAS as viagens que usam aquele local/veiculo sao do mesmo
vendedor. Se mais de um vendedor usa (ex.: um centro de distribuicao comum),
se quem criou as viagens e a plataforma (superusuario/Administrador),
ou se nenhuma viagem usa, fica sem dono = cadastro compartilhado (todos usam,
so a plataforma altera). Assim ninguem perde o acesso ao que ja usava.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def definir_donos(apps, schema_editor):
    Shipment = apps.get_model('transporte', 'Shipment')
    Location = apps.get_model('dominio', 'Location')
    Vehicle = apps.get_model('dominio', 'Vehicle')

    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    plataforma = set(
        User.objects.filter(is_superuser=True).values_list('pk', flat=True)
    ) | set(User.objects.filter(groups__name='Administrador').values_list('pk', flat=True))

    def dono_unico(viagens):
        donos = set(viagens.exclude(created_by=None).values_list('created_by', flat=True).distinct())
        if len(donos) == 1:
            dono = donos.pop()
            return None if dono in plataforma else dono  # cadastro da plataforma = compartilhado
        return None

    for local in Location.objects.filter(owner=None):
        dono = dono_unico(Shipment.objects.filter(origin=local) | Shipment.objects.filter(destination=local))
        if dono:
            Location.objects.filter(pk=local.pk).update(owner_id=dono)

    for veiculo in Vehicle.objects.filter(owner=None):
        dono = dono_unico(Shipment.objects.filter(vehicle=veiculo))
        if dono:
            Vehicle.objects.filter(pk=veiculo.pk).update(owner_id=dono)


class Migration(migrations.Migration):

    dependencies = [
        ("dominio", "0001_initial"),
        ("transporte", "0004_donos_e_entrega"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="location",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                help_text="Quem cadastrou o local (vazio = compartilhado).",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="locations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                help_text="Vendedor dono do veiculo (vazio = compartilhado).",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vehicles",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(definir_donos, migrations.RunPython.noop),
    ]
