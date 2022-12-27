# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def update_25m1pijl_klassen(apps, _):
    """ Kleine aanpassing op de defaults: de 25m1pijl heeft geen Compound A teams klasse """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_klas = apps.get_model('BasisTypen', 'TemplateCompetitieTeamKlasse')

    klasse = team_klas.objects.get(volgorde=21)      # 21 = Compound klasse A
    klasse.gebruik_25m = False
    klasse.save(update_fields=['gebruik_25m'])


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0050_gemengd'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='templatecompetitieteamklasse',
            old_name='blazoen1_18m_rk_bk',
            new_name='blazoen_18m_rk_bk',
        ),
        migrations.RemoveField(
            model_name='templatecompetitieindivklasse',
            name='buiten_gebruik',
        ),
        migrations.RemoveField(
            model_name='templatecompetitieteamklasse',
            name='blazoen2_18m_rk_bk',
        ),
        migrations.RemoveField(
            model_name='templatecompetitieteamklasse',
            name='buiten_gebruik',
        ),
        migrations.AddField(
            model_name='templatecompetitieindivklasse',
            name='gebruik_18m',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='templatecompetitieindivklasse',
            name='gebruik_25m',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='templatecompetitieteamklasse',
            name='gebruik_18m',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='templatecompetitieteamklasse',
            name='gebruik_25m',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(update_25m1pijl_klassen),
    ]

# end of file
