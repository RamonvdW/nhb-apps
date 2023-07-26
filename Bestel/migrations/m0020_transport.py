# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Bestel.definities import BESTEL_TRANSPORT_VERZEND


def zet_transport(apps, _):
    """ zet transport = verzend als er webwinkel producten gekozen zijn (mandje/bestelling) """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    mandje_klas = apps.get_model('Bestel', 'BestelMandje')
    bestelling_klas = apps.get_model('Bestel', 'Bestelling')

    for bestelling in bestelling_klas.objects.all():                    # pragma: no cover
        if bestelling.verzendkosten_euro > 0:
            bestelling.transport = BESTEL_TRANSPORT_VERZEND
            bestelling.save(update_fields=['transport'])
    # for

    for mandje in mandje_klas.objects.prefetch_related('producten'):    # pragma: no cover
        if mandje.producten.exclude(webwinkel_keuze=None).count() > 0:
            mandje.transport = BESTEL_TRANSPORT_VERZEND
            mandje.save(update_fields=['transport'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0019_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelling',
            name='transport',
            field=models.CharField(choices=[('N', 'Niet van toepassing'), ('V', 'Verzend'), ('O', 'Ophalen')],
                                   default='N', max_length=1),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='transport',
            field=models.CharField(choices=[('N', 'Niet van toepassing'), ('V', 'Verzend'), ('O', 'Ophalen')],
                                   default='N', max_length=1),
        ),
        migrations.AddField(
            model_name='bestelmutatie',
            name='transport',
            field=models.CharField(choices=[('N', 'Niet van toepassing'), ('V', 'Verzend'), ('O', 'Ophalen')],
                                   default='N', max_length=1),
        ),
        migrations.RunPython(zet_transport),
    ]

# end of file
