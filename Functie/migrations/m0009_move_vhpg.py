# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def take_over_vhpg(apps, _):
    # need de VHPG data over uit de Account applicatie

    # haal de klassen op die van toepassing zijn op het moment van migratie
    hpg_klas = apps.get_model('Account', 'HanterenPersoonsgegevens')
    vhpg_klas = apps.get_model('Functie', 'VerklaringHanterenPersoonsgegevens')

    bulk = list()
    for obj in hpg_klas.objects.all():      # pragma: no cover
        vhpg = vhpg_klas(account=obj.account,
                         acceptatie_datum=obj.acceptatie_datum)
        bulk.append(vhpg)
    # for

    vhpg_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0015_longer_otp_code'),
        ('Functie', 'm0008_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='VerklaringHanterenPersoonsgegevens',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acceptatie_datum', models.DateTimeField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vhpg', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Verklaring Hanteren Persoonsgegevens',
                'verbose_name_plural': 'Verklaring Hanteren Persoonsgegevens',
            },
        ),
        migrations.RunPython(take_over_vhpg),
    ]

# end of file
