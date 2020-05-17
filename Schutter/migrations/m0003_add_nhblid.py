# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def zet_nhblid(apps, _):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    schutterboog_klas = apps.get_model('Schutter', 'SchutterBoog')

    # zoek voor elke SchutterBoog met het NhbLid dat bij het Account past
    for obj in schutterboog_klas.objects.all():              # pragma: no cover
        if obj.account.nhblid_set.count() > 0:
            obj.nhblid = obj.account.nhblid_set.all()[0]
            obj.account = None
            obj.save()
        else:
            obj.delete()
    # for


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0009_migrate_nhblid_account'),
        ('Schutter', 'm0002_metadata'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='schutterboog',
            name='nhblid',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='NhbStructuur.NhbLid'),
        ),
        migrations.AlterField(
            model_name='schutterboog',
            name='account',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(zet_nhblid),
    ]

# end of file
