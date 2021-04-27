# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Overig.helpers import maak_unaccented


def zet_unaccented_naam(apps, _):
    """ zet nieuwe veld unaccented_naam """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    account_klas = apps.get_model('Account', 'Account')

    for obj in account_klas.objects.all():                      # pragma: no cover

        if obj.first_name or obj.last_name:
            volledige_naam = " ".join([obj.first_name, obj.last_name])
        else:
            volledige_naam = obj.username
        volledige_naam = volledige_naam.strip()

        obj.unaccented_naam = maak_unaccented(volledige_naam)
        obj.save(update_fields=['unaccented_naam'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0017_accountsessions'),
        ('NhbStructuur', 'm0018_unaccented_naam')
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='account',
            name='unaccented_naam',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.RunPython(zet_unaccented_naam),
    ]

# end of file
