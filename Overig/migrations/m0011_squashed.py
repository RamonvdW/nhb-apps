# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0023_squashed'),
        ('Competitie', 'm0096_squashed'),
        ('Feedback', 'm0003_squashed'),
        ('Functie', 'm0017_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SiteTijdelijkeUrl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_code', models.CharField(max_length=32)),
                ('aangemaakt_op', models.DateTimeField()),
                ('geldig_tot', models.DateTimeField()),
                ('hoortbij_accountemail', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Account.accountemail')),
                ('dispatch_to', models.CharField(default='', max_length=20)),
                ('hoortbij_functie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Functie.functie')),
                ('hoortbij_kampioenschap', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.kampioenschapsporterboog')),
            ],
        ),
    ]

# end of file
