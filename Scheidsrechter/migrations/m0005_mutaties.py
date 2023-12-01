# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0051_begrenzing_wereld'),
        ('Scheidsrechter', 'm0004_refactor'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='ScheidsMutatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('mutatie', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('door', models.CharField(default='', max_length=50)),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Wedstrijden.wedstrijd')),
            ],
            options={
                'verbose_name': 'Scheids mutatie',
            },
        ),
    ]
    
# end of file
    
