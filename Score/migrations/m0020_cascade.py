# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0062_squashed'),
        ('Sporter', 'm0031_squashed'),
        ('Score', 'm0019_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='aanvangsgemiddelde',
            name='boogtype',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='BasisTypen.boogtype'),
        ),
        migrations.AlterField(
            model_name='aanvangsgemiddelde',
            name='sporterboog',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporterboog'),
        ),
        migrations.AlterField(
            model_name='aanvangsgemiddeldehist',
            name='ag',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Score.aanvangsgemiddelde',
                                    related_name='ag_hist'),
        ),
        migrations.AlterField(
            model_name='score',
            name='sporterboog',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporterboog'),
        ),
    ]

# end of file
