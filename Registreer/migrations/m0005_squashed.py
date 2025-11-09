# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.conf import settings
from Registreer.definities import GAST_LID_NUMMER_FIXED_PK
from Sporter.models import validate_geboorte_datum


GAST_LID_NUMMER_EERSTE = 800001


def init_gast_lid_nr(apps, _):
    """ initialiseer het eerste gast lid nummer """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    gast_klas = apps.get_model('Registreer', 'GastLidNummer')

    gast_klas(pk=GAST_LID_NUMMER_FIXED_PK,
              volgende_lid_nr=GAST_LID_NUMMER_EERSTE).save()


def maak_vereniging_extern(apps, _):
    """ maak de vereniging voor gast sporters """

    ver_nr = settings.EXTERN_VER_NR

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    ver_klas = apps.get_model('Vereniging', 'Vereniging')
    sec_klas = apps.get_model('Vereniging', 'Secretaris')
    regio_klas = apps.get_model('Geo', 'Regio')
    functie_klas = apps.get_model('Functie', 'Functie')

    # zoek regio 100 op
    regio100 = regio_klas.objects.get(regio_nr=100)

    # maak de vereniging voor externe leden aan
    ver = ver_klas(
                ver_nr=ver_nr,
                naam='Extern',
                is_extern=True,
                regio=regio100,
                plaats='',
                geen_wedstrijden=False,
                contact_email=settings.EMAIL_BONDSBUREAU)
    ver.save()

    # maak de Secretaris administratie aan voor deze vereniging
    sec_klas(vereniging=ver).save()

    # maak de beheerders rol aan
    functie_klas(rol='SEC', beschrijving='Secretaris %s' % ver_nr, vereniging=ver).save()
    # (bewust geen HWL en WL)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('Functie', 'm0025_squashed'),
        ('Geo', 'm0002_squashed'),
        ('Sporter', 'm0033_squashed'),
        ('Vereniging', 'm0007_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='GastLidNummer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volgende_lid_nr', models.PositiveIntegerField()),
                ('kan_aanmaken', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Volgende gast lid nr',
                'verbose_name_plural': 'Volgende gast lid nr',
            },
        ),
        migrations.CreateModel(
            name='GastRegistratie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aangemaakt', models.DateTimeField(auto_now_add=True)),
                ('fase', models.PositiveSmallIntegerField(default=0)),
                ('logboek', models.TextField(default='')),
                ('lid_nr', models.PositiveIntegerField(default=0)),
                ('email_is_bevestigd', models.BooleanField(default=False)),
                ('email', models.CharField(max_length=150)),
                ('voornaam', models.CharField(max_length=50)),
                ('achternaam', models.CharField(max_length=100)),
                ('geboorte_datum', models.DateField(default='2000-01-01', validators=[validate_geboorte_datum])),
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw'), ('X', 'Anders')],
                                              default='M', max_length=1)),
                ('eigen_sportbond_naam', models.CharField(blank=True, default='', max_length=100)),
                ('eigen_lid_nummer', models.CharField(blank=True, default='', max_length=25)),
                ('club', models.CharField(blank=True, default='', max_length=100)),
                ('land', models.CharField(blank=True, default='', max_length=100)),
                ('telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                              to='Account.account')),
                ('sporter', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                              to='Sporter.sporter')),
                ('wa_id', models.CharField(blank=True, default='', max_length=8)),
                ('club_plaats', models.CharField(blank=True, default='', max_length=50)),
            ],
            options={
                'verbose_name': 'Gast registratie',
            },
        ),
        migrations.CreateModel(
            name='GastRegistratieRateTracker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_ip', models.CharField(max_length=48)),
                ('minuut', models.PositiveSmallIntegerField(default=0)),
                ('teller_minuut', models.PositiveSmallIntegerField(default=0)),
                ('teller_uur', models.PositiveSmallIntegerField(default=0)),
                ('uur', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Rate tracker',
            },
        ),
        migrations.RunPython(init_gast_lid_nr),
        migrations.RunPython(maak_vereniging_extern),
    ]

# end of file
