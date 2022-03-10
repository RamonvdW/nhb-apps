# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_uitslag(apps, _):

    uitslag_klas = apps.get_model('Score', 'Uitslag')
    old_klas = apps.get_model('Wedstrijden', 'CompetitieWedstrijdUitslag')

    for old in old_klas.objects.prefetch_related('scores').all():       # pragma: no cover
        score_pks = list(old.scores.values_list('pk', flat=True))

        uitslag = uitslag_klas(
                        max_score=old.max_score,
                        afstand=old.afstand_meter,
                        is_bevroren=old.is_bevroren)
        uitslag.save()
        uitslag.scores.set(score_pks)

        old.nieuwe_uitslag = uitslag
        old.save(update_fields=['nieuwe_uitslag'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0015_uitslag_1'),
        ('Wedstrijden', 'm0021_nieuwe_uitslag')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(migreer_uitslag)
    ]

# end of file
