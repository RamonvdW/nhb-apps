# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0011_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='score',
            name='type',
            field=models.CharField(choices=[('S', 'Score'), ('I', 'Indiv AG'), ('T', 'Team AG'), ('G', 'Geen score')], default='S', max_length=1),
        ),
        migrations.AddConstraint(
            model_name='score',
            constraint=models.UniqueConstraint(condition=models.Q(type='G'), fields=('sporterboog', 'type'),
                                               name='max 1 geen score per sporterboog'),
        ),
    ]

# end of file
