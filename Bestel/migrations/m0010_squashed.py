# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Bestel.models import BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK
from decimal import Decimal


def init_hoogste_bestel_nr(apps, _):
    """ maak het enige record aan in deze tabel """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    hoogste_klas = apps.get_model('Bestel', 'BestelHoogsteBestelNr')

    # maak het enige record aan met het hoogste gebruikte bestelnummer
    hoogste_klas(
            pk=BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK,
            hoogste_gebruikte_bestel_nr=1002000).save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Bestel', 'm0001_initial'),
                ('Bestel', 'm0002_transactie_actief'),
                ('Bestel', 'm0003_bestelling_ontvanger'),
                ('Bestel', 'm0004_bestelling_status'),
                ('Bestel', 'm0005_bestelmutatie'),
                ('Bestel', 'm0006_mutatie_betaling'),
                ('Bestel', 'm0007_bestelling_status_admin'),
                ('Bestel', 'm0008_renames'),
                ('Bestel', 'm0009_verkoper_info')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0021_squashed'),
        ('Betaal', 'm0009_squashed'),
        ('Kalender', 'm0008_inschrijving'),
        ('Betaal', 'm0002_minor_changes'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BestelHoogsteBestelNr',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hoogste_gebruikte_bestel_nr', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='BestelProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prijs_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('korting_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('inschrijving', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Kalender.kalenderinschrijving')),
            ],
            options={
                'verbose_name': 'Bestel product',
                'verbose_name_plural': 'Bestel producten',
            },
        ),
        migrations.CreateModel(
            name='BestelMandje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('totaal_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('account', models.OneToOneField(on_delete=models.deletion.CASCADE, to='Account.account')),
                ('producten', models.ManyToManyField(to='Bestel.BestelProduct')),
            ],
            options={
                'verbose_name': 'Mandje',
                'verbose_name_plural': 'Mandjes',
            },
        ),
        migrations.CreateModel(
            name='Bestelling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bestel_nr', models.PositiveIntegerField()),
                ('aangemaakt', models.DateTimeField(auto_now=True)),
                ('totaal_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('log', models.TextField()),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Account.account')),
                ('producten', models.ManyToManyField(to='Bestel.BestelProduct')),
                ('transacties', models.ManyToManyField(to='Betaal.BetaalTransactie')),
            ],
            options={
                'verbose_name': 'Bestelling',
                'verbose_name_plural': 'Bestellingen',
            },
        ),
        migrations.RunPython(init_hoogste_bestel_nr),
        migrations.AddField(
            model_name='bestelling',
            name='betaal_mutatie',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Betaal.betaalmutatie'),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='betaal_actief',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Betaal.betaalactief'),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='ontvanger',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Betaal.betaalinstellingenvereniging'),
        ),
        migrations.AlterField(
            model_name='bestelling',
            name='transacties',
            field=models.ManyToManyField(blank=True, to='Betaal.BetaalTransactie'),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='status',
            field=models.CharField(choices=[('N', 'Nieuw'), ('B', 'Te betalen'), ('A', 'Afgerond'), ('F', 'Mislukt')], default='N', max_length=1),
        ),
        migrations.CreateModel(
            name='BestelMutatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('code', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Bestel.bestelproduct')),
                ('inschrijving', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Kalender.kalenderinschrijving')),
                ('kortingscode', models.CharField(blank=True, default='', max_length=20)),
                ('bestelling', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Bestel.bestelling')),
                ('betaling_is_gelukt', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Bestel mutatie',
            },
        ),
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_adres1',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_adres2',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_kvk',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_naam',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_telefoon',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]

# end of file
