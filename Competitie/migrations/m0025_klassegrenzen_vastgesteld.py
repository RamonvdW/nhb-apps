# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_klassegrenzen_vastgesteld(apps, _):
    """ zet het nieuwe veld 'klassegrenzen_vastgesteld' voor elke Competitie """
    competitie_klas = apps.get_model('Competitie', 'Competitie')
    klasse_klas = apps.get_model('Competitie', 'CompetitieKlasse')

    for comp in competitie_klas.objects.all():      # pragma: no cover

        if klasse_klas.objects.filter(competitie=comp,
                                      min_ag__gt=0.000).count() > 0:
            comp.klassegrenzen_vastgesteld = True
            comp.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0024_gekozen_wedstrijden'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitie',
            name='klassegrenzen_vastgesteld',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(zet_klassegrenzen_vastgesteld),
    ]

# end of file
