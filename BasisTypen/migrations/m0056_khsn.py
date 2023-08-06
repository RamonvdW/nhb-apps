# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0055_titels'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='boogtype',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='kalenderwedstrijdklasse',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='leeftijdsklasse',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='teamtype',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA')], default='W', max_length=1),
        ),
    ]

# end of file
