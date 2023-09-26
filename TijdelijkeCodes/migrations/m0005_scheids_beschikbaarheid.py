# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0028_scheids'),
        ('TijdelijkeCodes', 'm0004_squashed'),
        ('Wedstrijden', 'm0047_aantal_scheids'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='tijdelijkecode',
            name='hoort_bij_sporter',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Sporter.sporter'),
        ),
        migrations.AddField(
            model_name='tijdelijkecode',
            name='hoort_bij_wedstrijd',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Wedstrijden.wedstrijd'),
        ),
    ]

# end of file
