# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0019_squashed'),
        ('Betalingen', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='betalingenvereniginginstellingen',
            name='akkoord_via_nhb',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='BetalingTransacties',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_id', models.CharField(max_length=32)),
                ('when', models.DateTimeField()),
                ('bedrag_ontvangen_euro', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('bedrag_retour_euro', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('klant_naam', models.CharField(max_length=100)),
                ('klant_iban', models.CharField(max_length=18)),
                ('klant_bic', models.CharField(max_length=11)),
                ('log', models.TextField()),
                ('account', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
            ],
        ),
    ]

# end of file
