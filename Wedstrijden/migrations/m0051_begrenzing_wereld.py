# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Wedstrijden.definities import WEDSTRIJD_BEGRENZING_LANDELIJK, WEDSTRIJD_BEGRENZING_WERELD


def zet_nieuwe_doelgroep(apps, _):
    """ zet alle wedstrijden om van 'landelijk' naar 'wereld' zodat gast-accounts erop in kunnen schrijven """
    wedstrijd_klas = apps.get_model('Wedstrijden', 'Wedstrijd')
    wedstrijd_klas.objects.filter(begrenzing=WEDSTRIJD_BEGRENZING_LANDELIJK).update(begrenzing=WEDSTRIJD_BEGRENZING_WERELD)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0050_kwalificatiescores_log'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='wedstrijd',
            name='begrenzing',
            field=models.CharField(choices=[('W', 'Wereld'), ('L', 'Landelijk'), ('Y', 'Rayon'),
                                            ('G', 'Regio'), ('V', 'Vereniging')], default='W', max_length=1),
        ),
        migrations.RunPython(zet_nieuwe_doelgroep, reverse_code=migrations.RunPython.noop)
    ]

# end of file
