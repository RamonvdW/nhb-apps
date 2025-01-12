# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleidingen', 'm0009_is_basiscursus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opleidingdiploma',
            name='sporter',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='old1', to='Sporter.sporter'),
        ),
        migrations.AlterField(
            model_name='opleidingdeelnemer',
            name='sporter',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, related_name='old2', to='Sporter.sporter'),
        ),
        migrations.AlterField(
            model_name='opleidingdeelnemer',
            name='koper',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, related_name='old3',
                                    to='Account.account'),
        ),
        migrations.AlterField(
            model_name='opleidingmoment',
            name='locatie',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, related_name='old4',
                                    to='Locatie.evenementlocatie'),
        ),
        migrations.AlterField(
            model_name='opleiding',
            name='momenten',
            field=models.ManyToManyField(blank=True, related_name='old5', to='Opleidingen.opleidingmoment'),
        ),
        migrations.AlterField(
            model_name='opleiding',
            name='deelnemers',
            field=models.ManyToManyField(blank=True, related_name='old6', to='Opleidingen.opleidingdeelnemer'),
        ),
    ]

# end of file
