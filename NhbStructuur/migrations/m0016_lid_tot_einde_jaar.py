# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.utils import timezone


def zet_lid_tot_einde_jaar(apps, _):
    """ zet het nieuwe veld op alle NhbLid objecten """
    # haal de klassen op die van toepassing zijn vóór de migratie

    year_now = timezone.now().year

    nhblid_klas = apps.get_model('NhbStructuur', 'NhbLid')
    for lid in nhblid_klas.objects.all():       # pragma: no cover
        lid.lid_tot_einde_jaar = year_now
    # for


class Migration(migrations.Migration):

    dependencies = [
        ('NhbStructuur', 'm0015_squashed'),
    ]

    operations = [
        migrations.AddField(
            model_name='nhblid',
            name='lid_tot_einde_jaar',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.RunPython(zet_lid_tot_einde_jaar),
    ]
