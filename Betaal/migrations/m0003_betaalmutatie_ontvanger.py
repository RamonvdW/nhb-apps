# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0002_minor_changes'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='betaalmutatie',
            name='ontvanger',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Betaal.betaalinstellingenvereniging'),
        ),
        migrations.AlterField(
            model_name='betaalinstellingenvereniging',
            name='vereniging',
            field=models.OneToOneField(on_delete=models.deletion.CASCADE, to='NhbStructuur.nhbvereniging'),
        ),
        migrations.AddField(
            model_name='betaalmutatie',
            name='url_betaling_gedaan',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='betaalmutatie',
            name='payment_id',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]

# end of file
