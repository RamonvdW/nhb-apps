# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    replaces = [('Wedstrijden', 'm0037_squashed'),
                ('Wedstrijden', 'm0038_remove_max_dt_per_baan'),
                ('Wedstrijden', 'm0039_khsn')]

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0027_squashed'),
        ('BasisTypen', 'm0057_squashed'),
        ('NhbStructuur', 'm0034_squashed'),
        ('Score', 'm0019_squashed'),
        ('Sporter', 'm0025_squashed'),
    ]

    operations = [
        migrations.CreateModel(
            name='WedstrijdLocatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zichtbaar', models.BooleanField(default=True)),
                ('baan_type', models.CharField(choices=[('X', 'Onbekend'), ('O', 'Volledig overdekte binnenbaan'), ('H', 'Binnen-buiten schieten'), ('B', 'Buitenbaan'), ('E', 'Extern')], default='X', max_length=1)),
                ('verenigingen', models.ManyToManyField(blank=True, to='NhbStructuur.nhbvereniging')),
                ('banen_18m', models.PositiveSmallIntegerField(default=0)),
                ('banen_25m', models.PositiveSmallIntegerField(default=0)),
                ('max_dt_per_baan', models.PositiveSmallIntegerField(default=4)),
                ('adres', models.TextField(blank=True, max_length=256)),
                ('adres_uit_crm', models.BooleanField(default=False)),
                ('plaats', models.CharField(blank=True, default='', max_length=50)),
                ('notities', models.TextField(blank=True, max_length=1024)),
                ('buiten_banen', models.PositiveSmallIntegerField(default=0)),
                ('buiten_max_afstand', models.PositiveSmallIntegerField(default=0)),
                ('discipline_3d', models.BooleanField(default=False)),
                ('discipline_clout', models.BooleanField(default=False)),
                ('discipline_indoor', models.BooleanField(default=False)),
                ('discipline_outdoor', models.BooleanField(default=False)),
                ('discipline_25m1pijl', models.BooleanField(default=False)),
                ('discipline_run', models.BooleanField(default=False)),
                ('discipline_veld', models.BooleanField(default=False)),
                ('naam', models.CharField(blank=True, max_length=50)),
                ('max_sporters_18m', models.PositiveSmallIntegerField(default=0)),
                ('max_sporters_25m', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Wedstrijd locatie',
                'verbose_name_plural': 'Wedstrijd locaties',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdSessie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField()),
                ('tijd_begin', models.TimeField()),
                ('tijd_einde', models.TimeField()),
                ('max_sporters', models.PositiveSmallIntegerField(default=1)),
                ('aantal_inschrijvingen', models.PositiveSmallIntegerField(default=0)),
                ('wedstrijdklassen', models.ManyToManyField(blank=True, to='BasisTypen.kalenderwedstrijdklasse')),
                ('beschrijving', models.CharField(default='', max_length=50)),
            ],
            options={
                'verbose_name': 'Wedstrijd sessie',
                'verbose_name_plural': 'Wedstrijd sessies',
            },
        ),
        migrations.CreateModel(
            name='Wedstrijd',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titel', models.CharField(default='', max_length=50)),
                ('status', models.CharField(choices=[('O', 'Ontwerp'), ('W', 'Wacht op goedkeuring'), ('A', 'Geaccepteerd'), ('X', 'Geannuleerd')], default='O', max_length=1)),
                ('datum_begin', models.DateField()),
                ('datum_einde', models.DateField()),
                ('begrenzing', models.CharField(choices=[('L', 'Landelijk'), ('Y', 'Rayon'), ('G', 'Regio'), ('V', 'Vereniging')], default='L', max_length=1)),
                ('organisatie', models.CharField(choices=[('W', 'World Archery'), ('N', 'NHB'), ('F', 'IFAA')], default='W', max_length=1)),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('IN', 'Indoor'), ('25', '25m 1pijl'), ('CL', 'Clout'), ('VE', 'Veld'), ('RA', 'Run Archery'), ('3D', '3D')], default='OD', max_length=2)),
                ('wa_status', models.CharField(choices=[('A', 'A-status'), ('B', 'B-status')], default='B', max_length=1)),
                ('contact_naam', models.CharField(blank=True, default='', max_length=50)),
                ('contact_email', models.CharField(blank=True, default='', max_length=150)),
                ('contact_website', models.CharField(blank=True, default='', max_length=100)),
                ('contact_telefoon', models.CharField(blank=True, default='', max_length=50)),
                ('voorwaarden_a_status_acceptatie', models.BooleanField(default=False)),
                ('voorwaarden_a_status_when', models.DateTimeField(auto_now=True)),
                ('voorwaarden_a_status_who', models.CharField(blank=True, default='', max_length=100)),
                ('extern_beheerd', models.BooleanField(default=False)),
                ('aantal_banen', models.PositiveSmallIntegerField(default=1)),
                ('minuten_voor_begin_sessie_aanwezig_zijn', models.PositiveSmallIntegerField(default=45)),
                ('scheidsrechters', models.TextField(blank=True, default='', max_length=500)),
                ('bijzonderheden', models.TextField(blank=True, default='', max_length=1000)),
                ('prijs_euro_normaal', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('prijs_euro_onder18', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('boogtypen', models.ManyToManyField(blank=True, to='BasisTypen.boogtype')),
                ('locatie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijdlocatie')),
                ('organiserende_vereniging', models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('sessies', models.ManyToManyField(blank=True, to='Wedstrijden.wedstrijdsessie')),
                ('wedstrijdklassen', models.ManyToManyField(blank=True, to='BasisTypen.kalenderwedstrijdklasse')),
                ('inschrijven_tot', models.PositiveSmallIntegerField(default=7)),
                ('toon_op_kalender', models.BooleanField(default=True)),
                ('verkoopvoorwaarden_status_acceptatie', models.BooleanField(default=False)),
                ('verkoopvoorwaarden_status_when', models.DateTimeField(auto_now=True)),
                ('verkoopvoorwaarden_status_who', models.CharField(blank=True, default='', max_length=100)),
                ('uitvoerende_vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, related_name='uitvoerend', to='NhbStructuur.nhbvereniging')),
                ('is_ter_info', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Wedstrijd',
                'verbose_name_plural': 'Wedstrijden',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdKorting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geldig_tot_en_met', models.DateField()),
                ('percentage', models.PositiveSmallIntegerField(default=100)),
                ('soort', models.CharField(choices=[('s', 'Sporter'), ('v', 'Vereniging'), ('c', 'Combi')], default='v', max_length=1)),
                ('uitgegeven_door', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, related_name='wedstrijd_korting_uitgever', to='NhbStructuur.nhbvereniging')),
                ('voor_sporter', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Sporter.sporter')),
                ('voor_wedstrijden', models.ManyToManyField(to='Wedstrijden.wedstrijd')),
            ],
            options={
                'verbose_name': 'Wedstrijd korting',
                'verbose_name_plural': 'Wedstrijd kortingen',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdInschrijving',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer', models.DateTimeField()),
                ('status', models.CharField(choices=[('R', 'Reservering'), ('B', 'Besteld'), ('D', 'Definitief'), ('A', 'Afgemeld')], default='R', max_length=2)),
                ('ontvangen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('retour_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('korting', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Wedstrijden.wedstrijdkorting')),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('sessie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijdsessie')),
                ('sporterboog', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijd')),
                ('log', models.TextField(blank=True)),
                ('wedstrijdklasse', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.kalenderwedstrijdklasse')),
            ],
            options={
                'verbose_name': 'Wedstrijd inschrijving',
                'verbose_name_plural': 'Wedstrijd inschrijvingen',
            },
        ),
        migrations.AddConstraint(
            model_name='wedstrijdinschrijving',
            constraint=models.UniqueConstraint(fields=('sessie', 'sporterboog'), name='Geen dubbele wedstrijd inschrijving'),
        ),
        migrations.RemoveField(
            model_name='wedstrijdlocatie',
            name='max_dt_per_baan',
        ),
        migrations.AlterField(
            model_name='wedstrijd',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA')], default='W', max_length=1),
        ),
    ]
