# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

SPELD_DISCIPLINE_NVT = 'XX'


def corrigeer_graadspelden(apps, _):
    klas_voorwaarden = apps.get_model('Spelden', 'SpeldVoorwaarden')

    klas_voorwaarden.objects.filter(discipline=SPELD_DISCIPLINE_NVT,
                                    wedstrijd_soort='Indoor',
                                    aantal_pijlen=90).update(aantal_pijlen=60)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Spelden', 'm0012_short_metric'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='speld',
            name='prijs_euro',
        ),
        migrations.RunPython(corrigeer_graadspelden, migrations.RunPython.noop),
    ]

# end of file
