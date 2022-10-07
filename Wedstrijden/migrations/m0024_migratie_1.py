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
        ('Account', 'm0021_squashed'),
        ('Wedstrijden', 'm0023_squashed'),
        ('BasisTypen', 'm0043_jongens'),
        ('NhbStructuur', 'm0027_squashed'),
        ('Sporter', 'm0010_squashed'),
        ('Kalender', 'm0012_squashed')
    ]

    # migratie functies
    operations = [
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
                ('voorwaarden_a_status_when', models.DateTimeField()),
                ('voorwaarden_a_status_who', models.CharField(blank=True, default='', max_length=100)),
                ('extern_beheerd', models.BooleanField(default=False)),
                ('aantal_banen', models.PositiveSmallIntegerField(default=1)),
                ('minuten_voor_begin_sessie_aanwezig_zijn', models.PositiveSmallIntegerField(default=45)),
                ('scheidsrechters', models.TextField(blank=True, default='', max_length=500)),
                ('bijzonderheden', models.TextField(blank=True, default='', max_length=1000)),
                ('prijs_euro_normaal', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('prijs_euro_onder18', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('boogtypen', models.ManyToManyField(blank=True, to='BasisTypen.BoogType')),
            ],
            options={
                'verbose_name': 'Wedstrijd',
                'verbose_name_plural': 'Wedstrijden',
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
                ('wedstrijdklassen', models.ManyToManyField(blank=True, to='BasisTypen.KalenderWedstrijdklasse')),
            ],
            options={
                'verbose_name': 'Wedstrijd sessie',
                'verbose_name_plural': 'Wedstrijd sessies',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdKortingscode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default='', max_length=20)),
                ('geldig_tot_en_met', models.DateField()),
                ('percentage', models.PositiveSmallIntegerField(default=100)),
                ('soort', models.CharField(choices=[('s', 'Sporter'), ('v', 'Vereniging'), ('c', 'Combi')], default='v', max_length=1)),
                ('combi_basis_wedstrijd', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='wedstrijd_combi_korting', to='Wedstrijden.wedstrijd')),
                ('uitgegeven_door', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, related_name='wedstrijd_korting_uitgever', to='NhbStructuur.nhbvereniging')),
                ('voor_sporter', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Sporter.sporter')),
                ('voor_vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='NhbStructuur.nhbvereniging')),
                ('voor_wedstrijden', models.ManyToManyField(to='Wedstrijden.Wedstrijd')),
            ],
            options={
                'verbose_name': 'Wedstrijd kortingscode',
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
                ('gebruikte_code', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Wedstrijden.wedstrijdkortingscode')),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('sessie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijdsessie')),
                ('sporterboog', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijd')),
            ],
            options={
                'verbose_name': 'Wedstrijd inschrijving',
                'verbose_name_plural': 'Wedstrijd inschrijvingen',
            },
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='locatie',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijdlocatie'),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='organiserende_vereniging',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging'),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='sessies',
            field=models.ManyToManyField(blank=True, to='Wedstrijden.WedstrijdSessie'),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='wedstrijdklassen',
            field=models.ManyToManyField(blank=True, to='BasisTypen.KalenderWedstrijdklasse'),
        ),
        migrations.AddConstraint(
            model_name='wedstrijdinschrijving',
            constraint=models.UniqueConstraint(fields=('sessie', 'sporterboog'), name='Geen dubbele wedstrijd inschrijving'),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='oud',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Kalender.kalenderwedstrijd'),
        ),
        migrations.AddField(
            model_name='wedstrijdinschrijving',
            name='oud',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Kalender.kalenderinschrijving'),
        ),
        migrations.AddField(
            model_name='wedstrijdkortingscode',
            name='oud',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Kalender.kalenderwedstrijdkortingscode'),
        ),
        migrations.AddField(
            model_name='wedstrijdsessie',
            name='oud',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Kalender.kalenderwedstrijdsessie'),
        ),
    ]

# end of file
