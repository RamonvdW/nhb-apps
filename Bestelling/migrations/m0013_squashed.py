# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Bestelling.definities import BESTELLING_HOOGSTE_BESTEL_NR_FIXED_PK
from decimal import Decimal


def init_hoogste_bestel_nr(apps, _):
    """ maak het enige record aan in deze tabel """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    hoogste_klas = apps.get_model('Bestelling', 'BestellingHoogsteBestelNr')

    # maak het enige record aan met het hoogste gebruikte bestelnummer
    hoogste_klas(
            pk=BESTELLING_HOOGSTE_BESTEL_NR_FIXED_PK,
            hoogste_gebruikte_bestel_nr=1002000).save()


class Migration(migrations.Migration):

    replaces = [('Bestelling', 'm0003_squashed'),
                ('Bestelling', 'm0004_opleiding_2'),
                ('Bestelling', 'm0005_regel'),
                ('Bestelling', 'm0006_prod2regel'),
                ('Bestelling', 'm0007_remove_product'),
                ('Bestelling', 'm0008_korting_ver_nr'),
                ('Bestelling', 'm0009_remove_verzendkosten'),
                ('Bestelling', 'm0010_aanpassen'),
                ('Bestelling', 'm0011_product_pk'),
                ('Bestelling', 'm0012_sessie_pk')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('BasisTypen', 'm0062_squashed'),
        ('Betaal', 'm0026_squashed'),
        #('Evenement', 'm0002_bedragen'),
        #('Evenement', 'm0003_bestelling'),
        #('Opleiding', 'm0006_squashed'),
        #('Opleiding', 'm0008_bestelling'),
        ('Sporter', 'm0033_squashed'),
        #('Webwinkel', 'm0009_squashed'),
        #('Webwinkel', 'm0010_bestelling'),
        #('Wedstrijden', 'm0057_squashed'),
        #('Wedstrijden', 'm0060_bestelling'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BestellingHoogsteBestelNr',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hoogste_gebruikte_bestel_nr', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='BestellingRegel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('korte_beschrijving', models.CharField(blank=True, default='?', max_length=250)),
                ('korting_redenen', models.CharField(blank=True, default='', max_length=500)),
                ('bedrag_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('btw_percentage', models.CharField(blank=True, default='', max_length=5)),
                ('btw_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('gewicht_gram', models.SmallIntegerField(default=0)),
                ('code', models.CharField(blank=True, default='?', max_length=25)),
                ('korting_ver_nr', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Bestelling regel',
            },
        ),
        migrations.CreateModel(
            name='Bestelling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bestel_nr', models.PositiveIntegerField()),
                ('aangemaakt', models.DateTimeField(auto_now_add=True)),
                ('verkoper_naam', models.CharField(blank=True, default='', max_length=100)),
                ('verkoper_adres1', models.CharField(blank=True, default='', max_length=100)),
                ('verkoper_adres2', models.CharField(blank=True, default='', max_length=100)),
                ('verkoper_kvk', models.CharField(blank=True, default='', max_length=15)),
                ('verkoper_btw_nr', models.CharField(blank=True, default='', max_length=15)),
                ('verkoper_email', models.EmailField(blank=True, default='', max_length=254)),
                ('verkoper_telefoon', models.CharField(blank=True, default='', max_length=20)),
                ('verkoper_iban', models.CharField(blank=True, default='', max_length=18)),
                ('verkoper_bic', models.CharField(blank=True, default='', max_length=11)),
                ('verkoper_heeft_mollie', models.BooleanField(default=False)),
                ('afleveradres_regel_1', models.CharField(blank=True, default='', max_length=100)),
                ('afleveradres_regel_2', models.CharField(blank=True, default='', max_length=100)),
                ('afleveradres_regel_3', models.CharField(blank=True, default='', max_length=100)),
                ('afleveradres_regel_4', models.CharField(blank=True, default='', max_length=100)),
                ('afleveradres_regel_5', models.CharField(blank=True, default='', max_length=100)),
                ('transport', models.CharField(choices=[('N', 'Niet van toepassing'), ('V', 'Verzend'),
                                                        ('O', 'Ophalen')], default='N', max_length=1)),
                ('btw_percentage_cat1', models.CharField(blank=True, default='', max_length=5)),
                ('btw_percentage_cat2', models.CharField(blank=True, default='', max_length=5)),
                ('btw_percentage_cat3', models.CharField(blank=True, default='', max_length=5)),
                ('btw_euro_cat1', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_euro_cat2', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_euro_cat3', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('totaal_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('status', models.CharField(choices=[('N', 'Nieuw'), ('B', 'Betaling actief'), ('A', 'Afgerond'),
                                                     ('F', 'Mislukt'), ('G', 'Geannuleerd')], default='N', max_length=1)),
                ('log', models.TextField()),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                              to='Account.account')),
                ('betaal_actief', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                    to='Betaal.betaalactief')),
                ('betaal_mutatie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                     to='Betaal.betaalmutatie')),
                ('ontvanger', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                to='Betaal.betaalinstellingenvereniging')),
                ('transacties', models.ManyToManyField(blank=True, to='Betaal.betaaltransactie')),
                ('regels', models.ManyToManyField(to='Bestelling.bestellingregel')),
            ],
            options={
                'verbose_name': 'Bestelling',
                'verbose_name_plural': 'Bestellingen',
            },
        ),
        migrations.CreateModel(
            name='BestellingMandje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('afleveradres_regel_1', models.CharField(blank=True, default='', max_length=100)),
                ('afleveradres_regel_2', models.CharField(blank=True, default='', max_length=100)),
                ('afleveradres_regel_3', models.CharField(blank=True, default='', max_length=100)),
                ('afleveradres_regel_4', models.CharField(blank=True, default='', max_length=100)),
                ('afleveradres_regel_5', models.CharField(blank=True, default='', max_length=100)),
                ('transport', models.CharField(choices=[('N', 'Niet van toepassing'), ('V', 'Verzend'),
                                                        ('O', 'Ophalen')], default='N', max_length=1)),
                ('verzendkosten_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_percentage_cat1', models.CharField(blank=True, default='', max_length=5)),
                ('btw_percentage_cat2', models.CharField(blank=True, default='', max_length=5)),
                ('btw_percentage_cat3', models.CharField(blank=True, default='', max_length=5)),
                ('btw_euro_cat1', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_euro_cat2', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_euro_cat3', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('totaal_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('vorige_herinnering', models.DateField(default='2000-01-01')),
                ('account', models.OneToOneField(on_delete=models.deletion.CASCADE, to='Account.account')),
                ('regels', models.ManyToManyField(to='Bestelling.bestellingregel')),
            ],
            options={
                'verbose_name': 'Mandje',
                'verbose_name_plural': 'Mandjes',
            },
        ),
        migrations.CreateModel(
            name='BestellingMutatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('code', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('korting', models.CharField(blank=True, default='', max_length=20)),
                ('betaling_is_gelukt', models.BooleanField(default=False)),
                ('bedrag_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('transport', models.CharField(choices=[('N', 'Niet van toepassing'), ('V', 'Verzend'),
                                                        ('O', 'Ophalen')], default='N', max_length=1)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                              to='Account.account')),
                ('bestelling', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                 to='Bestelling.bestelling')),
                ('regel', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                            to='Bestelling.bestellingregel')),
                ('sporterboog', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  to='Sporter.sporterboog')),
                ('wedstrijdklasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                      to='BasisTypen.kalenderwedstrijdklasse')),
                ('product_pk', models.PositiveBigIntegerField(default=0)),
                ('sessie_pk', models.PositiveBigIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Bestelling mutatie',
            },
        ),
        migrations.RunPython(init_hoogste_bestel_nr),
    ]

# end of file
