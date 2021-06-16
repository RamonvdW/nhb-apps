# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def verwijder_import_rondes(apps, _):
    """ Ruim de rondes op die aangemaakt waren voor het importeren vanuit de oude sites
    """
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    ronde_klas = apps.get_model('Competitie', 'DeelcompetitieRonde')

    # vind all rondes met de beschrijving "Ronde # oude programma"
    pks = list()
    for ronde in ronde_klas.objects.all():      # pragma: no cover
        if ronde.beschrijving[:6] == 'Ronde ' and ronde.beschrijving[-15:] == ' oude programma':
            pks.append(ronde.pk)
    # for

    ronde_klas.objects.filter(pk__in=pks).delete()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0044_squashed'),
    ]

    # migratie functions
    operations = [
        migrations.RunPython(verwijder_import_rondes),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_score1'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_score2'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_score3'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_score4'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_score5'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_score6'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_score7'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_totaal'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_aantal_scores'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_gemiddelde'),
        migrations.RemoveField(model_name='regiocompetitieschutterboog', name='alt_laagste_score_nr'),
    ]

# end of file
