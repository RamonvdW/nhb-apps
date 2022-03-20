# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_organisatie(apps, _):
    """ Pas het nieuwe 'organisatie' veld aan voor situaties waar de default (WA) niet kan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalender_klas = apps.get_model('Kalender', 'KalenderWedstrijd')

    for kal in kalender_klas.objects.all():
        if kal.discipline not in ('IN', 'OD', 'VE'):
            # niet Indoor, Outdoor, Veld --> maak organisatie = NHB
            kal.organisatie = 'N'
            kal.save(update_fields=['organisatie'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kalenderwedstrijd',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'Nationaal'), ('F', 'IFAA')], default='W', max_length=1),
        ),
        migrations.RunPython(zet_organisatie)
    ]

# end of file
