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
        ('Account', 'm0019_squashed'),
        ('Kalender', 'm0007_organisatie'),
        ('NhbStructuur', 'm0024_squashed'),
        ('Sporter', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='kalenderwedstrijdsessie',
            name='sporters',
        ),
        migrations.AddField(
            model_name='kalenderwedstrijdsessie',
            name='prijs_euro',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='kalenderwedstrijdsessie',
            name='aantal_inschrijvingen',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.CreateModel(
            name='KalenderWedstrijdKortingscode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default='', max_length=20)),
                ('geldig_tot_en_met', models.DateField()),
                ('percentage', models.PositiveSmallIntegerField(default=100)),
                ('voor_sporter', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Sporter.sporter')),
                ('voor_vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='NhbStructuur.nhbvereniging')),
                ('voor_wedstrijden', models.ManyToManyField(to='Kalender.KalenderWedstrijd')),
                ('uitgegeven_door', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, related_name='korting_uitgever', to='NhbStructuur.nhbvereniging')),
            ],
            options={
                'verbose_name': 'Kalender kortingscode',
            },
        ),
        migrations.CreateModel(
            name='KalenderInschrijving',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer', models.DateTimeField()),
                ('gebruikte_code', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Kalender.kalenderwedstrijdkortingscode')),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.Account')),
                ('sessie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Kalender.kalenderwedstrijdsessie')),
                ('sporterboog', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Kalender.kalenderwedstrijd')),
                ('status', models.CharField(choices=[('R', 'Reservering'), ('D', 'Definitief'), ('A', 'Afgemeld')], default='R', max_length=2)),
                ('ontvangen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('retour_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
            ],
            options={
                'verbose_name': 'Kalender inschrijving',
                'verbose_name_plural': 'Kalender inschrijvingen',
            },
        ),
        migrations.AddConstraint(
            model_name='kalenderinschrijving',
            constraint=models.UniqueConstraint(fields=('sessie', 'sporterboog'), name='Geen dubbele inschrijving'),
        ),
        migrations.CreateModel(
            name='KalenderMutatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('code', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('inschrijving', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Kalender.kalenderinschrijving')),
                ('korting', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Kalender.kalenderwedstrijdkortingscode')),
                ('korting_voor_koper', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
            ],
            options={
                'verbose_name': 'Kalender mutatie',
            },
        ),
    ]

# end of file
