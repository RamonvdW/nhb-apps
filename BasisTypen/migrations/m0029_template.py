# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0028_squashed'),
        ('Wedstrijden', 'm0022_migreer_wedstrijden'),
    ]

    # migratie functies
    operations = [
        migrations.RenameModel(
            old_name='IndivWedstrijdklasse',
            new_name='TemplateCompetitieIndivKlasse',
        ),
        migrations.RenameModel(
            old_name='TeamWedstrijdklasse',
            new_name='TemplateCompetitieTeamKlasse',
        ),
        migrations.AlterModelOptions(
            name='kalenderwedstrijdklasse',
            options={'verbose_name': 'Kalender Wedstrijdklasse', 'verbose_name_plural': 'Kalender Wedstrijdklassen'},
        ),
        migrations.AlterModelOptions(
            name='templatecompetitieindivklasse',
            options={'verbose_name': 'Template Competitie Indiv Klasse', 'verbose_name_plural': 'Template Competitie Indiv Klassen'},
        ),
        migrations.AlterModelOptions(
            name='templatecompetitieteamklasse',
            options={'verbose_name': 'Template Competitie Team Klasse', 'verbose_name_plural': 'Template Competitie Team Klassen'},
        ),
        migrations.RemoveIndex(
            model_name='templatecompetitieindivklasse',
            name='BasisTypen__volgord_8e5550_idx',
        ),
        migrations.RemoveIndex(
            model_name='templatecompetitieteamklasse',
            name='BasisTypen__volgord_46891c_idx',
        ),
        migrations.AddIndex(
            model_name='templatecompetitieindivklasse',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_48eb00_idx'),
        ),
        migrations.AddIndex(
            model_name='templatecompetitieteamklasse',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_4d62f0_idx'),
        ),
    ]

# end of file
