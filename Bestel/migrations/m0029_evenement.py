# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Evenement', 'm0002_afgemeld'),
        ('Bestel', 'm0028_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelproduct',
            name='evenement_inschrijving',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=models.deletion.SET_NULL, to='Evenement.evenementinschrijving'),
        ),
        migrations.AddField(
            model_name='bestelproduct',
            name='evenement_afgemeld',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Evenement.evenementafgemeld'),
        ),
        migrations.AddField(
            model_name='bestelmutatie',
            name='evenement_inschrijving',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Evenement.evenementinschrijving'),
        ),
    ]

# end of file
