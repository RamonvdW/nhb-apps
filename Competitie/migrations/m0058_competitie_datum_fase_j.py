# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_nieuwe_datum(apps, _):
    comp_klas = apps.get_model('Competitie', 'Competitie')
    for comp in comp_klas.objects.all():            # pragma: no cover
        if comp.afstand == '18':
            # maandag week 2 = 10 januari 2022
            comp.datum_klassegrenzen_rk_bk_teams = '2022-01-10'
        else:
            # maandag week 14 = 4 april 2022
            comp.datum_klassegrenzen_rk_bk_teams = '2022-04-04'

        comp.save(update_fields=['datum_klassegrenzen_rk_bk_teams'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0057_competitieklasse_voor_rk_bk_teams'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitie',
            name='datum_klassegrenzen_rk_bk_teams',
            field=models.DateField(default='2000-01-01'),
            preserve_default=False,
        ),
        migrations.RunPython(zet_nieuwe_datum, reverse_code=migrations.RunPython.noop),
    ]

# end of file
