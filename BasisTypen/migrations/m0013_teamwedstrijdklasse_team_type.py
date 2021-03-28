# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


# individuele wedstrijdklassen jaar 2020 volgens spec v1.3, tabel 2.4   # TODO: update spec revisie
WKL_TEAM = (
    (10, 'Recurve klasse ERE',         'R'),
    (11, 'Recurve klasse A',           'R'),
    (12, 'Recurve klasse B',           'R'),
    (13, 'Recurve klasse C',           'R'),
    (14, 'Recurve klasse D',           'R'),

    (20, 'Compound klasse ERE',        'C'),
    (21, 'Compound klasse A',          'C'),

    (30, 'Barebow klasse ERE',         'BB'),

    (40, 'Instinctive Bow klasse ERE', 'IB'),

    (50, 'Longbow klasse ERE',         'LB'),
)


def koppel_team_type(apps, _):
    """ Team Type invullen in de team wedstrijdklassen """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    team_wkl_klas = apps.get_model('BasisTypen', 'TeamWedstrijdklasse')

    afkorting2teamtype = dict()
    for team_type in team_type_klas.objects.all():
        afkorting2teamtype[team_type.afkorting] = team_type
    # for

    volgorde2wkl = dict()
    for wkl in team_wkl_klas.objects.all():
        volgorde2wkl[wkl.volgorde] = wkl
    # for

    for volgorde, beschrijving, afkorting in WKL_TEAM:
        wkl = volgorde2wkl[volgorde]
        wkl.beschrijving = beschrijving
        wkl.team_type = afkorting2teamtype[afkorting]
        wkl.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0012_team_typen'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='teamwedstrijdklasse',
            name='team_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.teamtype'),
        ),
        migrations.RunPython(koppel_team_type),
    ]

# end of file
