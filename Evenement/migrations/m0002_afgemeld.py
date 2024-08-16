# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0030_squashed'),
        ('Evenement', 'm0001_initial'),
        ('Sporter', 'm0031_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='evenementinschrijving',
            name='status',
            field=models.CharField(choices=[('R', 'Reservering'), ('B', 'Besteld'), ('D', 'Definitief')],
                                   default='R', max_length=2),
        ),
        migrations.CreateModel(
            name='EvenementAfgemeld',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer_inschrijving', models.DateTimeField()),
                ('wanneer_afgemeld', models.DateTimeField()),
                ('status', models.CharField(choices=[('A', 'Afgemeld'), ('V', 'Verwijderd')], max_length=2)),
                ('ontvangen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('retour_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('log', models.TextField(blank=True)),
                ('evenement', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Evenement.evenement')),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('sporter', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Evenement afmelding',
                'verbose_name_plural': 'Evenement afmeldingen',
            },
        ),
    ]

# end of file
