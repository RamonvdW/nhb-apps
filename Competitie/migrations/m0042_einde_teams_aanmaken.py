# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_einde_teams_aanmaken(apps, _):
    """ zet het veld 'einde_teams_aanmaken' indien deze nog op de template datum staat """

    deelcomp_klas = apps.get_model('Competitie', 'DeelCompetitie')

    for deelcomp in deelcomp_klas.objects.select_related('competitie').all():      # pragma: no cover

        if deelcomp.einde_teams_aanmaken.year < deelcomp.competitie.begin_jaar:
            deelcomp.einde_teams_aanmaken = deelcomp.competitie.einde_teamvorming
            deelcomp.save(update_fields=['einde_teams_aanmaken'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0041_dagdeel_inschrijving'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(zet_einde_teams_aanmaken),
    ]

# end of file
