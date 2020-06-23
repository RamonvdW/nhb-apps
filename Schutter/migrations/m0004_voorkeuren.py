# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migreer_dt(apps, _):

    """ Migreer de voorkeur_dutchtarget_18m instelling
        van SchutterBoog naar SchutterVoorkeuren
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    voorkeuren_klas = apps.get_model('Schutter', 'SchutterVoorkeuren')
    schutterboog_klas = apps.get_model('Schutter', 'SchutterBoog')

    bulk_voorkeuren = list()

    for obj in (schutterboog_klas
                .objects
                .filter(voorkeur_dutchtarget_18m=True)
                .distinct('nhblid')):

        # maak een SchutterVoorkeuren object aan voor dit NhbLid
        voorkeuren = voorkeuren_klas(nhblid=obj.nhblid,
                                     voorkeur_dutchtarget_18m=True)
        bulk_voorkeuren.append(voorkeuren)
    # for

    voorkeuren_klas.objects.bulk_create(bulk_voorkeuren)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('NhbStructuur', 'm0013_admin_blank_fields'),
        ('Schutter', 'm0003_add_nhblid'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SchutterVoorkeuren',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voorkeur_dutchtarget_18m', models.BooleanField(default=False)),
                ('voorkeur_meedoen_competitie', models.BooleanField(default=True)),
                ('voorkeur_team_schieten', models.BooleanField(default=False)),
                ('account', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('nhblid', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='NhbStructuur.NhbLid')),
            ],
            options={
                'verbose_name': 'Schutter voorkeuren',
                'verbose_name_plural': 'Schutter voorkeuren',
            },
        ),
        migrations.RunPython(migreer_dt),
        migrations.RemoveField(
            model_name='schutterboog',
            name='voorkeur_dutchtarget_18m',
        ),
    ]

# end of file
