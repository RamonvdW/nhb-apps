# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0030_squashed'),
        ('Locatie', 'm0008_evenement_locatie'),
        ('Sporter', 'm0031_squashed'),
        ('Vereniging', 'm0007_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Evenement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titel', models.CharField(default='', max_length=50)),
                ('status', models.CharField(choices=[('O', 'Ontwerp'), ('W', 'Wacht op goedkeuring'),
                                                     ('A', 'Geaccepteerd'), ('X', 'Geannuleerd')],
                                            default='O', max_length=1)),
                ('is_ter_info', models.BooleanField(default=False)),
                ('datum', models.DateField()),
                ('aanvang', models.TimeField(default='10:00')),
                ('inschrijven_tot', models.PositiveSmallIntegerField(default=1)),
                ('contact_naam', models.CharField(blank=True, default='', max_length=50)),
                ('contact_email', models.CharField(blank=True, default='', max_length=150)),
                ('contact_website', models.CharField(blank=True, default='', max_length=100)),
                ('contact_telefoon', models.CharField(blank=True, default='', max_length=50)),
                ('beschrijving', models.TextField(blank=True, default='', max_length=1000)),
                ('prijs_euro_normaal', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('prijs_euro_onder18', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('locatie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Locatie.evenementlocatie')),
                ('organiserende_vereniging', models.ForeignKey(on_delete=models.deletion.PROTECT,
                                                               to='Vereniging.vereniging')),
            ],
            options={
                'verbose_name': 'Evenement',
                'verbose_name_plural': 'Evenementen',
            },
        ),
        migrations.CreateModel(
            name='EvenementInschrijving',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer', models.DateTimeField()),
                ('status', models.CharField(choices=[('R', 'Reservering'), ('B', 'Besteld'), ('D', 'Definitief'),
                                                     ('A', 'Afgemeld'), ('V', 'Verwijderd')],
                                            default='R', max_length=2)),
                ('ontvangen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('retour_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('log', models.TextField(blank=True)),
                ('evenement', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Evenement.evenement')),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('sporter', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Evenement inschrijving',
                'verbose_name_plural': 'Evenement inschrijvingen',
            },
        ),
        migrations.AddConstraint(
            model_name='evenementinschrijving',
            constraint=models.UniqueConstraint(fields=('evenement', 'sporter'),
                                               name='Geen dubbele evenement inschrijving'),
        ),
    ]

# end of file
