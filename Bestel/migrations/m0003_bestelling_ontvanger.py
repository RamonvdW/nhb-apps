# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0002_transactie_actief'),
        ('Betaal', 'm0002_minor_changes'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelling',
            name='ontvanger',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Betaal.betaalinstellingenvereniging'),
        ),
        migrations.AlterField(
            model_name='bestelling',
            name='transacties',
            field=models.ManyToManyField(blank=True, to='Betaal.BetaalTransactie'),
        ),
    ]

# end of file
