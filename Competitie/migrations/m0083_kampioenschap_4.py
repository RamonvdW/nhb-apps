# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0016_rol_mww'),
        ('Competitie', 'm0082_kampioenschap_3'),
        ('NhbStructuur', 'm0030_bondsbureau'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='deelcompetitie',
            name='laag',
        ),
        migrations.RemoveField(
            model_name='deelcompetitie',
            name='nhb_rayon',
        ),
        migrations.RemoveField(
            model_name='deelcompetitie',
            name='rk_bk_matches',
        ),
        migrations.AlterField(
            model_name='deelcompetitie',
            name='functie',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='Functie.functie'),
        ),
        migrations.AlterField(
            model_name='deelcompetitie',
            name='nhb_regio',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbregio'),
        ),
    ]

# end of file
