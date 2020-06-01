# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def init_administratieve_regios(apps, _):
    """ geef de nodig regios de nieuwe administratieve vlag """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')

    obj = regio_klas.objects.get(regio_nr=100)
    obj.is_administratief = True
    obj.save()


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0009_migrate_nhblid_account'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='nhbregio',
            name='is_administratief',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(init_administratieve_regios)
    ]

# end of file
