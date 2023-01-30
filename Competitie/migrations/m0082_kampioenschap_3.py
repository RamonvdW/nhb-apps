# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

# old
LAAG_RK = 'RK'
LAAG_BK = 'BK'


def verwijder_oude_deelcompetities(apps, _):
    """ Verwijder de deelcompetities voor RK en BK """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    deelcomp_klas = apps.get_model('Competitie', 'DeelCompetitie')

    for deelcomp in deelcomp_klas.objects.filter(laag__in=(LAAG_RK, LAAG_BK)):      # pragma: no cover
        deelcomp.rk_bk_matches.clear()
        deelcomp.delete()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0081_kampioenschap_2'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='kampioenschapindivklasselimiet',
            name='deelcompetitie',
            field=models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie'),
        ),
        migrations.AlterField(
            model_name='kampioenschapindivklasselimiet',
            name='kampioenschap',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelkampioenschap'),
        ),
        migrations.AlterField(
            model_name='kampioenschapsporterboog',
            name='deelcompetitie',
            field=models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie'),
        ),
        migrations.AlterField(
            model_name='kampioenschapsporterboog',
            name='kampioenschap',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelkampioenschap'),
        ),
        migrations.AlterField(
            model_name='kampioenschapteam',
            name='deelcompetitie',
            field=models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie'),
        ),
        migrations.AlterField(
            model_name='kampioenschapteam',
            name='kampioenschap',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelkampioenschap'),
        ),
        migrations.AlterField(
            model_name='kampioenschapteamklasselimiet',
            name='deelcompetitie',
            field=models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie'),
        ),
        migrations.AlterField(
            model_name='kampioenschapteamklasselimiet',
            name='kampioenschap',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelkampioenschap'),
        ),
        migrations.RemoveField(
            model_name='deelkampioenschap',
            name='old_deelcomp',
        ),
        migrations.RemoveField(
            model_name='kampioenschapindivklasselimiet',
            name='deelcompetitie',
        ),
        migrations.RemoveField(
            model_name='kampioenschapsporterboog',
            name='deelcompetitie',
        ),
        migrations.RemoveField(
            model_name='kampioenschapteam',
            name='deelcompetitie',
        ),
        migrations.RemoveField(
            model_name='kampioenschapteamklasselimiet',
            name='deelcompetitie',
        ),
        migrations.RunPython(verwijder_oude_deelcompetities)
    ]

# end of file
