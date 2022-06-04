# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


def migreer_kosten(apps, _):
    """ Pas het nieuwe 'organisatie' veld aan voor situaties waar de default (WA) niet kan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    wedstrijd_klas = apps.get_model('Kalender', 'KalenderWedstrijd')

    for wedstrijd in wedstrijd_klas.objects.prefetch_related('sessies'):        # pragma: no cover
        prijzen = list()
        for sessie in wedstrijd.sessies.all():
            if sessie.prijs_euro > 0.001:
                prijzen.append(sessie.prijs_euro)
        # for

        if len(prijzen) == 0:
            prijzen.append(Decimal('0'))

        wedstrijd.prijs_euro_normaal = max(prijzen)
        wedstrijd.prijs_euro_onder18 = min(prijzen)
        wedstrijd.save(update_fields=['prijs_euro_normaal', 'prijs_euro_onder18'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0010_delete_kalendermutatie'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kalenderwedstrijd',
            name='prijs_euro_normaal',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5),
        ),
        migrations.AddField(
            model_name='kalenderwedstrijd',
            name='prijs_euro_onder18',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5),
        ),
        migrations.RunPython(migreer_kosten),
        migrations.RemoveField(
            model_name='kalenderwedstrijdsessie',
            name='prijs_euro',
        ),
    ]

# end of file
