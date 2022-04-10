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
        ('Kalender', 'm0009_prijs'),
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
                ('voor_wedstrijd', models.ManyToManyField(to='Kalender.KalenderWedstrijd')),
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
                ('betaling_voldaan', models.BooleanField(default=False)),
                ('gebruikte_code', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Kalender.kalenderwedstrijdkortingscode')),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.Account')),
                ('sessie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Kalender.kalenderwedstrijdsessie')),
                ('sporterboog', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Kalender.kalenderwedstrijd')),
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
            ],
            options={
                'verbose_name': 'Kalender mutatie',
            },
        ),
    ]

# end of file
