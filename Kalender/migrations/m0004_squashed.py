# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0020_squashed'),
        ('NhbStructuur', 'm0019_squashed'),
        ('Schutter', 'm0010_squashed'),
        ('Wedstrijden', 'm0018_squashed'),
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
            options={'verbose_name': 'Kalender wedstrijd deeluitslag',
                     'verbose_name_plural': 'Kalender wedstrijd deeluitslagen'},
        ),
        migrations.CreateModel(
            name='KalenderWedstrijdSessie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField()),
                ('tijd_begin', models.TimeField()),
                ('tijd_einde', models.TimeField()),
                ('max_sporters', models.PositiveSmallIntegerField(default=1)),
                ('aanmeldingen', models.ManyToManyField(blank=True, to='Schutter.SchutterBoog')),
                ('wedstrijdklassen', models.ManyToManyField(blank=True, to='BasisTypen.KalenderWedstrijdklasse')),
            ],
            options={'verbose_name': 'Kalender wedstrijd sessie',
                     'verbose_name_plural': 'Kalender wedstrijd sessies'},
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
                ('locatie', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.wedstrijdlocatie')),
                ('organiserende_vereniging', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('sessies', models.ManyToManyField(blank=True, to='Kalender.KalenderWedstrijdSessie')),
                ('extern_beheerd', models.BooleanField(default=False)),
                ('wedstrijdklassen', models.ManyToManyField(blank=True, to='BasisTypen.KalenderWedstrijdklasse')),
                ('begrenzing', models.CharField(choices=[('L', 'Landelijk'), ('Y', 'Rayon'), ('G', 'Regio'), ('V', 'Vereniging')], default='L', max_length=1)),
                ('bijzonderheden', models.TextField(blank=True, default='', max_length=1000)),
            ],
            options={'verbose_name': 'Kalender wedstrijd',
                     'verbose_name_plural': 'Kalender wedstrijden'},
        ),
    ]

# end of file
