# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0023_squashed'),
        ('Webwinkel', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='WebwinkelKeuze',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer', models.DateTimeField()),
                ('status', models.CharField(choices=[('M', 'Reservering'), ('B', 'Besteld'), ('BO', 'Betaald')], default='M', max_length=2)),
                ('aantal', models.PositiveSmallIntegerField(default=1)),
                ('totaal_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('ontvangen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('log', models.TextField(blank=True)),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('product', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Webwinkel.webwinkelproduct')),
            ],
        ),
    ]

# end of file
