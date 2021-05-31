# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Schutter', 'm0008_para_opmerking'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='schuttervoorkeuren',
            name='voorkeur_discipline_25m1pijl',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='schuttervoorkeuren',
            name='voorkeur_discipline_3d',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='schuttervoorkeuren',
            name='voorkeur_discipline_clout',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='schuttervoorkeuren',
            name='voorkeur_discipline_indoor',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='schuttervoorkeuren',
            name='voorkeur_discipline_outdoor',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='schuttervoorkeuren',
            name='voorkeur_discipline_run',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='schuttervoorkeuren',
            name='voorkeur_discipline_veld',
            field=models.BooleanField(default=True),
        ),
    ]

# end of file
