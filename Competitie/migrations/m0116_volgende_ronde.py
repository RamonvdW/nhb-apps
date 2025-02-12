# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_indiv_volgende(apps, _):
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kamp_klas = apps.get_model('Competitie', 'KampioenschapSporterBoog')

    for kamp in kamp_klas.objects.order_by('indiv_klasse').distinct('indiv_klasse'):
        indiv_klasse = kamp.indiv_klasse
        kamp_klas.objects.filter(indiv_klasse=indiv_klasse).update(indiv_klasse_volgende_ronde=indiv_klasse)
    # for


def zet_team_volgende(apps, _):
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_klas = apps.get_model('Competitie', 'KampioenschapTeam')

    for team in team_klas.objects.order_by('team_klasse').distinct('team_klasse'):
        team_klasse = team.team_klasse
        team_klas.objects.filter(team_klasse=team_klasse).update(team_klasse_volgende_ronde=team_klasse)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0115_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapsporterboog',
            name='indiv_klasse_volgende_ronde',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                    related_name='indiv_klasse_volgende_ronde', to='Competitie.competitieindivklasse'),
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='team_klasse_volgende_ronde',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                    related_name='team_klasse_volgende_ronde', to='Competitie.competitieteamklasse'),
        ),
        migrations.RunPython(zet_indiv_volgende),
        migrations.RunPython(zet_team_volgende),
    ]

# end of file
