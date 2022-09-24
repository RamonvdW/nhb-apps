# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def vervang_boogtype_volgorde(apps, _):
    """ Vervang de volgorde van elk boogtype
        Voorheen was dit een teken en er was overlap tussen IFAA en WA bogen.
        Nu een getal en netjes gescheiden.
    """

    # boog typen volgens spec v2.2, tabel 3.2

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    afkorting2volgorde = {
        # WA:
        'R': 10,
        'C': 11,
        'BB': 12,
        'TR': 13,
        'LB': 14,
        # IFAA:
        'BBR': 20,
        'BBC': 21,
        'FSR': 22,
        'FSC': 23,
        'FU': 24,
        'BHR': 25,
        'BHC': 26,
        'BHU': 27,
        'BHL': 28,
        'ITR': 29,
        'ILB': 30,
        'IHB': 31,
    }

    for boogtype in boogtype_klas.objects.all():
        boogtype.volgorde = afkorting2volgorde[boogtype.afkorting]
        boogtype.save(update_fields=['volgorde'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0047_ifaa_open_klasse'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveIndex(
            model_name='boogtype',
            name='BasisTypen__volgord_81dcc1_idx',
        ),
        migrations.RemoveField(
            model_name='boogtype',
            name='volgorde',
        ),
        migrations.AddField(
            model_name='boogtype',
            name='volgorde',
            field=models.PositiveSmallIntegerField(default=0),
        ),

        migrations.RunPython(vervang_boogtype_volgorde),

        migrations.AlterModelOptions(
            name='boogtype',
            options={'ordering': ['volgorde'], 'verbose_name': 'Boog type', 'verbose_name_plural': 'Boog typen'},
        ),
        migrations.AlterModelOptions(
            name='kalenderwedstrijdklasse',
            options={'ordering': ['volgorde'], 'verbose_name': 'Kalender Wedstrijdklasse', 'verbose_name_plural': 'Kalender Wedstrijdklassen'},
        ),
        migrations.AlterModelOptions(
            name='leeftijdsklasse',
            options={'ordering': ['volgorde'], 'verbose_name': 'Leeftijdsklasse', 'verbose_name_plural': 'Leeftijdsklassen'},
        ),
        migrations.AlterModelOptions(
            name='teamtype',
            options={'ordering': ['volgorde'], 'verbose_name': 'Team type', 'verbose_name_plural': 'Team typen'},
        ),
        migrations.AlterModelOptions(
            name='templatecompetitieindivklasse',
            options={'ordering': ['volgorde'], 'verbose_name': 'Template Competitie Indiv Klasse', 'verbose_name_plural': 'Template Competitie Indiv Klassen'},
        ),
        migrations.AlterModelOptions(
            name='templatecompetitieteamklasse',
            options={'ordering': ['volgorde'], 'verbose_name': 'Template Competitie Team Klasse', 'verbose_name_plural': 'Template Competitie Team Klassen'},
        ),
    ]

# end of file
