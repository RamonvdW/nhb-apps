# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Kalender', 'm0006_squashed'), ('Kalender', 'm0007_organisatie'), ('Kalender', 'm0008_inschrijving'), ('Kalender', 'm0009_combi_korting'), ('Kalender', 'm0010_delete_kalendermutatie'), ('Kalender', 'm0011_kosten')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0021_squashed'),
        ('BasisTypen', 'm0042_squashed'),
        ('NhbStructuur', 'm0027_squashed'),
        ('Sporter', 'm0010_squashed'),
        ('Wedstrijden', 'm0023_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='KalenderWedstrijdDeeluitslag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('bestandsnaam', models.CharField(blank=True, default='', max_length=100)),
                ('toegevoegd_op', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Kalender wedstrijd deeluitslag',
                'verbose_name_plural': 'Kalender wedstrijd deeluitslagen',
            },
        ),
        migrations.CreateModel(
            name='KalenderWedstrijdSessie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField()),
                ('tijd_begin', models.TimeField()),
                ('tijd_einde', models.TimeField()),
                ('max_sporters', models.PositiveSmallIntegerField(default=1)),
                ('wedstrijdklassen', models.ManyToManyField(blank=True, to='BasisTypen.KalenderWedstrijdklasse')),
                ('aantal_inschrijvingen', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Kalender wedstrijd sessie',
                'verbose_name_plural': 'Kalender wedstrijd sessies',
            },
        ),
        migrations.CreateModel(
            name='KalenderWedstrijd',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titel', models.CharField(default='', max_length=50)),
                ('status', models.CharField(choices=[('O', 'Ontwerp'), ('W', 'Wacht op goedkeuring'), ('A', 'Geaccepteerd'), ('X', 'Geannuleerd')], default='O', max_length=1)),
                ('datum_begin', models.DateField()),
                ('datum_einde', models.DateField()),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('IN', 'Indoor'), ('25', '25m 1pijl'), ('CL', 'Clout'), ('VE', 'Veld'), ('RA', 'Run Archery'), ('3D', '3D')], default='OD', max_length=2)),
                ('wa_status', models.CharField(choices=[('A', 'A-status'), ('B', 'B-status')], default='B', max_length=1)),
                ('contact_naam', models.CharField(blank=True, default='', max_length=50)),
                ('contact_email', models.CharField(blank=True, default='', max_length=150)),
                ('contact_website', models.CharField(blank=True, default='', max_length=100)),
                ('contact_telefoon', models.CharField(blank=True, default='', max_length=50)),
                ('voorwaarden_a_status_acceptatie', models.BooleanField(default=False)),
                ('voorwaarden_a_status_when', models.DateTimeField()),
                ('voorwaarden_a_status_who', models.CharField(blank=True, default='', max_length=100)),
                ('aantal_banen', models.PositiveSmallIntegerField(default=1)),
                ('minuten_voor_begin_sessie_aanwezig_zijn', models.PositiveSmallIntegerField(default=45)),
                ('scheidsrechters', models.TextField(blank=True, default='', max_length=500)),
                ('boogtypen', models.ManyToManyField(blank=True, to='BasisTypen.BoogType')),
                ('deeluitslagen', models.ManyToManyField(blank=True, to='Kalender.KalenderWedstrijdDeeluitslag')),
                ('locatie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijdlocatie')),
                ('organiserende_vereniging', models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('sessies', models.ManyToManyField(blank=True, to='Kalender.KalenderWedstrijdSessie')),
                ('extern_beheerd', models.BooleanField(default=False)),
                ('wedstrijdklassen', models.ManyToManyField(blank=True, to='BasisTypen.KalenderWedstrijdklasse')),
                ('begrenzing', models.CharField(choices=[('L', 'Landelijk'), ('Y', 'Rayon'), ('G', 'Regio'), ('V', 'Vereniging')], default='L', max_length=1)),
                ('bijzonderheden', models.TextField(blank=True, default='', max_length=1000)),
                ('organisatie', models.CharField(choices=[('W', 'World Archery'), ('N', 'NHB'), ('F', 'IFAA')], default='W', max_length=1)),
                ('prijs_euro_normaal', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('prijs_euro_onder18', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
            ],
            options={
                'verbose_name': 'Kalender wedstrijd',
                'verbose_name_plural': 'Kalender wedstrijden',
            },
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
                ('combi_basis_wedstrijd', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='combi_korting', to='Kalender.kalenderwedstrijd')),
                ('soort', models.CharField(choices=[('s', 'Sporter'), ('v', 'Vereniging'), ('c', 'Combi')], default='v', max_length=1)),
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
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('sessie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Kalender.kalenderwedstrijdsessie')),
                ('sporterboog', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Kalender.kalenderwedstrijd')),
                ('status', models.CharField(choices=[('R', 'Reservering'), ('B', 'Besteld'), ('D', 'Definitief'), ('A', 'Afgemeld')], default='R', max_length=2)),
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
    ]

# end of file
