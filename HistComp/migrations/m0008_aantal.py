# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_aantal_beste_scores(apps, _):
    """ zet de uitzondering voor het veld aantal_beste_scores """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    histcomp_klas = apps.get_model('HistComp', 'HistCompetitie')

    # in 2021/2022 werd 5 gebruikt voor de Indoor (in verband met corona)
    for histcomp in histcomp_klas.objects.filter(seizoen='2021/2022', comp_type='18'):      # pragma: no cover
        histcomp.aantal_beste_scores = 5
        histcomp.save(update_fields=['aantal_beste_scores'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0007_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='histcompetitie',
            old_name='klasse',
            new_name='boog_str',
        ),
        migrations.RenameField(
            model_name='histcompetitieindividueel',
            old_name='schutter_nr',
            new_name='sporter_lid_nr',
        ),
        migrations.RenameField(
            model_name='histcompetitieindividueel',
            old_name='schutter_naam',
            new_name='sporter_naam',
        ),
        migrations.AddField(
            model_name='histcompetitie',
            name='aantal_beste_scores',
            field=models.PositiveSmallIntegerField(default=6),
        ),
        migrations.RunPython(code=zet_aantal_beste_scores,
                             reverse_code=migrations.RunPython.noop)
    ]

# end of file
