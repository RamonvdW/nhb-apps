# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_team_datums(apps, _):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    comp_klas = apps.get_model('Competitie', 'Competitie')

    for comp in comp_klas.objects.all():
        comp.begin_fase_L_teams = comp.begin_fase_L_indiv
        comp.einde_fase_L_teams = comp.einde_fase_L_indiv

        comp.begin_fase_P_teams = comp.begin_fase_P_indiv
        comp.einde_fase_P_teams = comp.einde_fase_P_indiv

        comp.save(update_fields=['begin_fase_L_teams',
                                 'einde_fase_L_teams',
                                 'begin_fase_P_teams',
                                 'einde_fase_P_teams'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0089_rename'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='competitie',
            name='uiterste_datum_lid',
        ),

        migrations.RenameField(
            model_name='competitie',
            old_name='alle_regiocompetities_afgesloten',
            new_name='regiocompetitie_is_afgesloten',
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='begin_aanmeldingen',
            new_name='begin_fase_C',
        ),
        migrations.AlterField(
            model_name='competitie',
            name='begin_fase_C',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.RenameField(
            model_name='regiocompetitie',
            old_name='einde_teams_aanmaken',
            new_name='begin_fase_D',
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='eerste_wedstrijd',
            new_name='begin_fase_F',
        ),
        migrations.AlterField(
            model_name='competitie',
            name='begin_fase_F',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='laatst_mogelijke_wedstrijd',
            new_name='einde_fase_F',
        ),
        migrations.AlterField(
            model_name='competitie',
            name='einde_fase_F',
            field=models.DateField(default='2000-01-01'),
        ),

        # RK
        migrations.RenameField(
            model_name='competitie',
            old_name='rk_eerste_wedstrijd',
            new_name='begin_fase_L_indiv',
        ),
        migrations.AlterField(
            model_name='competitie',
            name='begin_fase_L_indiv',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='rk_laatste_wedstrijd',
            new_name='einde_fase_L_indiv',
        ),
        migrations.AlterField(
            model_name='competitie',
            name='einde_fase_L_indiv',
            field=models.DateField(default='2000-01-01'),
        ),

        migrations.AddField(
            model_name='competitie',
            name='begin_fase_L_teams',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.AddField(
            model_name='competitie',
            name='einde_fase_L_teams',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='alle_rks_afgesloten',
            new_name='rk_indiv_afgesloten',
        ),
        migrations.AddField(
            model_name='competitie',
            name='rk_teams_afgesloten',
            field=models.BooleanField(default=False),
        ),

        # BK
        migrations.AddField(
            model_name='competitie',
            name='bk_indiv_klassen_zijn_samengevoegd',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='competitie',
            name='bk_teams_klassen_zijn_samengevoegd',
            field=models.BooleanField(default=False),
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='bk_eerste_wedstrijd',
            new_name='begin_fase_P_indiv',
        ),
        migrations.AlterField(
            model_name='competitie',
            name='begin_fase_P_indiv',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='bk_laatste_wedstrijd',
            new_name='einde_fase_P_indiv',
        ),
        migrations.AlterField(
            model_name='competitie',
            name='einde_fase_P_indiv',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.AddField(
            model_name='competitie',
            name='begin_fase_P_teams',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.AddField(
            model_name='competitie',
            name='einde_fase_P_teams',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.RenameField(
            model_name='competitie',
            old_name='alle_bks_afgesloten',
            new_name='bk_indiv_afgesloten',
        ),
        migrations.AddField(
            model_name='competitie',
            name='bk_teams_afgesloten',
            field=models.BooleanField(default=False),
        ),

        migrations.RunPython(zet_team_datums, migrations.RunPython.noop),
    ]

# end of file
