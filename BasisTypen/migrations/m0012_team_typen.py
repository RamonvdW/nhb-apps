# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def maak_team_typen_2020(apps, _):
    """ Boog typen jaar 2020, volgens spec v2.0, tabel 2.3 """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    boog_type_klas = apps.get_model('BasisTypen', 'BoogType')

    boog_r = boog_type_klas.objects.get(afkorting='R')
    boog_c = boog_type_klas.objects.get(afkorting='C')
    boog_bb = boog_type_klas.objects.get(afkorting='BB')
    boog_ib = boog_type_klas.objects.get(afkorting='IB')
    boog_lb = boog_type_klas.objects.get(afkorting='LB')

    # maak de standaard team typen aan
    team = team_type_klas(afkorting='R',  volgorde='1', beschrijving='Recurve team')
    team.save()
    team.boog_typen.add(boog_r, boog_bb, boog_ib, boog_lb)

    team = team_type_klas(afkorting='C',  volgorde='2', beschrijving='Compound team')
    team.save()
    team.boog_typen.add(boog_c)

    team = team_type_klas(afkorting='BB', volgorde='3', beschrijving='Barebow team')
    team.save()
    team.boog_typen.add(boog_bb, boog_ib, boog_lb)

    team = team_type_klas(afkorting='IB', volgorde='4', beschrijving='Instinctive Bow team')
    team.save()
    team.boog_typen.add(boog_ib, boog_lb)

    team = team_type_klas(afkorting='LB', volgorde='5', beschrijving='Longbow team')
    team.save()
    team.boog_typen.add(boog_lb)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0011_onbekend_niet_rk_bk'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='TeamType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=50)),
                ('afkorting', models.CharField(max_length=2)),
                ('volgorde', models.CharField(default='?', max_length=1)),
                ('boog_typen', models.ManyToManyField(to='BasisTypen.BoogType')),
            ],
            options={
                'verbose_name': 'Team type',
                'verbose_name_plural': 'Team typen',
            },
        ),
        migrations.RunPython(maak_team_typen_2020),
    ]

# end of file
