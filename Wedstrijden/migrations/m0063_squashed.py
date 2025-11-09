# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


def maak_functie_mwz(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')

    functie_klas(rol='MWZ', beschrijving='Manager Wedstrijdzaken').save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Wedstrijden', 'm0057_squashed'),
                ('Wedstrijden', 'm0058_allow_blank'),
                ('Wedstrijden', 'm0059_langere_titel'),
                ('Wedstrijden', 'm0060_bestelling'),
                ('Wedstrijden', 'm0061_afmelden_sessie'),
                ('Wedstrijden', 'm0062_urls')]

    # dit is de eerste
    initial = True

    # migratie functies
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('BasisTypen', 'm0062_squashed'),
        ('Functie', 'm0028_squashed'),
        ('Locatie', 'm0009_squashed'),
        ('Score', 'm0021_squashed'),
        ('Sporter', 'm0033_squashed'),
        ('Vereniging', 'm0007_squashed'),
    ]

    # migratie functies
    operations = [
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
                ('titel', models.CharField(default='', max_length=75)),
                ('status', models.CharField(choices=[('O', 'Ontwerp'), ('W', 'Wacht op goedkeuring'),
                                                     ('A', 'Geaccepteerd'), ('X', 'Geannuleerd')],
                                            default='O', max_length=1)),
                ('datum_begin', models.DateField()),
                ('datum_einde', models.DateField()),
                ('begrenzing', models.CharField(choices=[('W', 'Wereld'), ('L', 'Landelijk'), ('Y', 'Rayon'),
                                                         ('G', 'Regio'), ('V', 'Vereniging')],
                                                default='W', max_length=1)),
                ('organisatie', models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA'),
                                                          ('S', 'WA strikt')], default='W', max_length=1)),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('IN', 'Indoor'), ('25', '25m 1pijl'),
                                                         ('CL', 'Clout'), ('VE', 'Veld'), ('RA', 'Run Archery'),
                                                         ('3D', '3D')], default='OD', max_length=2)),
                ('wa_status', models.CharField(choices=[('A', 'A-status'), ('B', 'B-status')],
                                               default='B', max_length=1)),
                ('contact_naam', models.CharField(blank=True, default='', max_length=50)),
                ('contact_email', models.CharField(blank=True, default='', max_length=150)),
                ('contact_website', models.CharField(blank=True, default='', max_length=100)),
                ('contact_telefoon', models.CharField(blank=True, default='', max_length=50)),
                ('voorwaarden_a_status_acceptatie', models.BooleanField(default=False)),
                ('voorwaarden_a_status_when', models.DateTimeField(auto_now_add=True)),
                ('voorwaarden_a_status_who', models.CharField(blank=True, default='', max_length=100)),
                ('extern_beheerd', models.BooleanField(default=False)),
                ('aantal_banen', models.PositiveSmallIntegerField(default=1)),
                ('minuten_voor_begin_sessie_aanwezig_zijn', models.PositiveSmallIntegerField(default=45)),
                ('scheidsrechters', models.TextField(blank=True, default='', max_length=500)),
                ('bijzonderheden', models.TextField(blank=True, default='', max_length=1000)),
                ('prijs_euro_normaal', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('prijs_euro_onder18', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('boogtypen', models.ManyToManyField(blank=True, to='BasisTypen.boogtype')),
                ('locatie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Locatie.wedstrijdlocatie')),
                ('organiserende_vereniging', models.ForeignKey(on_delete=models.deletion.PROTECT,
                                                               to='Vereniging.vereniging')),
                ('sessies', models.ManyToManyField(blank=True, to='Wedstrijden.wedstrijdsessie')),
                ('wedstrijdklassen', models.ManyToManyField(blank=True, to='BasisTypen.kalenderwedstrijdklasse')),
                ('inschrijven_tot', models.PositiveSmallIntegerField(default=7)),
                ('toon_op_kalender', models.BooleanField(default=True)),
                ('verkoopvoorwaarden_status_acceptatie', models.BooleanField(default=False)),
                ('verkoopvoorwaarden_status_when', models.DateTimeField(auto_now_add=True)),
                ('verkoopvoorwaarden_status_who', models.CharField(blank=True, default='', max_length=100)),
                ('uitvoerende_vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                             related_name='uitvoerend', to='Vereniging.vereniging')),
                ('is_ter_info', models.BooleanField(default=False)),
                ('eis_kwalificatie_scores', models.BooleanField(default=False)),
                ('aantal_scheids', models.IntegerField(default=-1)),
                ('verstop_voor_mwz', models.BooleanField(default=False)),
                ('url_uitslag_1', models.CharField(blank=True, default='', max_length=200)),
                ('url_uitslag_2', models.CharField(blank=True, default='', max_length=200)),
                ('url_uitslag_3', models.CharField(blank=True, default='', max_length=200)),
                ('url_uitslag_4', models.CharField(blank=True, default='', max_length=200)),
                ('url_flyer', models.CharField(blank=True, default='', max_length=200)),
                ('url_deelnemerslijst', models.CharField(blank=True, default='', max_length=200)),
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
                ('soort', models.CharField(choices=[('s', 'Sporter'), ('v', 'Vereniging'), ('c', 'Combi')],
                                           default='v', max_length=1)),
                ('uitgegeven_door', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                      related_name='wedstrijd_korting_uitgever',
                                                      to='Vereniging.vereniging')),
                ('voor_sporter', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                   to='Sporter.sporter')),
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
                ('status', models.CharField(choices=[('R', 'Reservering'), ('B', 'Besteld'), ('D', 'Definitief'),
                                                     ('A', 'Afgemeld'), ('V', 'Verwijderd')],
                                            default='R', max_length=2)),
                ('ontvangen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('retour_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('korting', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                              to='Wedstrijden.wedstrijdkorting')),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('sessie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                             to='Wedstrijden.wedstrijdsessie')),
                ('sporterboog', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijd')),
                ('log', models.TextField(blank=True)),
                ('wedstrijdklasse', models.ForeignKey(on_delete=models.deletion.PROTECT,
                                                      to='BasisTypen.kalenderwedstrijdklasse')),
                ('bestelling', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT,
                                                 to='Bestelling.bestellingregel')),
            ],
            options={
                'verbose_name': 'Wedstrijd inschrijving',
                'verbose_name_plural': 'Wedstrijd inschrijvingen',
                'constraints': [models.UniqueConstraint(fields=('sessie', 'sporterboog'),
                                                        name='Geen dubbele wedstrijd inschrijving')],
            },
        ),
        migrations.CreateModel(
            name='Kwalificatiescore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField(default='2000-01-01')),
                ('naam', models.CharField(max_length=50)),
                ('waar', models.CharField(max_length=50)),
                ('resultaat', models.PositiveSmallIntegerField(default=0)),
                ('inschrijving', models.ForeignKey(on_delete=models.deletion.CASCADE,
                                                   to='Wedstrijden.wedstrijdinschrijving')),
                ('check_status', models.CharField(choices=[('A', 'Afgekeurd'), ('N', 'Nog doen'), ('G', 'Goed')],
                                                  default='N', max_length=1)),
                ('log', models.TextField(default='')),
            ],
        ),
        migrations.RunPython(maak_functie_mwz),
    ]

# end of file
