# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('Competitie', 'm0115_squashed'),
        ('Functie', 'm0025_squashed'),
        ('Registreer', 'm0005_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='TijdelijkeCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_code', models.CharField(max_length=32)),
                ('aangemaakt_op', models.DateTimeField()),
                ('geldig_tot', models.DateTimeField()),
                ('dispatch_to', models.CharField(default='', max_length=20)),
                ('hoort_bij_account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                                        to='Account.account')),
                ('hoort_bij_functie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                                        to='Functie.functie')),
                ('hoort_bij_kampioen', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                                         to='Competitie.kampioenschapsporterboog')),
                ('hoort_bij_gast_reg', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                                         to='Registreer.gastregistratie')),
            ],
        ),
    ]

# end of file
