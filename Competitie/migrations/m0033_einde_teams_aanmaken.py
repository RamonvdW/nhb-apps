# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_einde_teams_aanmaken(apps, _):
    """ zet het nieuwe veld 'einde_teams_aanmaken' voor elke deelcompetitie """

    deelcomp_klas = apps.get_model('Competitie', 'DeelCompetitie')

    for deelcomp in deelcomp_klas.objects.all():      # pragma: no cover

        deelcomp.einde_teams_aanmaken = deelcomp.competitie.einde_teamvorming
        deelcomp.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0032_rename_cleanup'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='deelcompetitie',
            name='einde_teams_aanmaken',
            field=models.DateField(default='2001-01-01'),
        ),
        migrations.RunPython(zet_einde_teams_aanmaken),
    ]

# end of file
