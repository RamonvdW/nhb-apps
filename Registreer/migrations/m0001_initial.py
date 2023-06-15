# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.conf import settings
from Registreer.models import GAST_LID_NUMMER_FIXED_PK
from Sporter.models import validate_geboorte_datum


GAST_LID_NUMMER_EERSTE = 800001


def init_gast_lid_nr(apps, _):
    """ initialiseer het eerste gast lid nummer """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    gast_klas = apps.get_model('Registreer', 'GastLidNummer')

    gast_klas(pk=GAST_LID_NUMMER_FIXED_PK,
              volgende_lid_nr=GAST_LID_NUMMER_EERSTE).save()


def maak_vereniging_8000(apps, _):
    """ maak de NHB vereniging voor gast sporters """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    ver_klas = apps.get_model('NhbStructuur', 'NhbVereniging')
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    functie_klas = apps.get_model('Functie', 'Functie')

    # zoek regio 100 op
    regio100 = regio_klas.objects.get(regio_nr=100)

    # maak vereniging 8000 aan
    ver = ver_klas(
                ver_nr=8000,
                naam='Extern',
                plaats='',
                regio=regio100,
                geen_wedstrijden=False,
                contact_email=settings.EMAIL_BONDSBUREAU)
    ver.save()

    # maak de beheerders rollen aan
    functie_klas(rol='SEC', beschrijving='Secretaris 8000', nhb_ver=ver).save()
    functie_klas(rol='HWL', beschrijving='Hoofdwedstrijdleider 8000', nhb_ver=ver).save()
    functie_klas(rol='WL', beschrijving='Wedstrijdleider 8000', nhb_ver=ver).save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0025_merge_accountemail_2'),
        ('NhbStructuur', 'm0032_korter'),
        ('Sporter', 'm0022_pas_code'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='GastLidNummer',
            fields=[
                ('volgende_lid_nr', models.PositiveIntegerField()),
            ],
            options={
                'verbose_name': 'Volgende gast lid nr',
                'verbose_name_plural': 'Volgende gast lid nr'
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
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw'), ('X', 'Anders')], default='M', max_length=1)),
                ('eigen_sportbond_naam', models.CharField(blank=True, default='', max_length=100)),
                ('eigen_lid_nummer', models.CharField(blank=True, default='', max_length=25)),
                ('eigen_vereniging', models.CharField(blank=True, default='', max_length=100)),
                ('woonplaats', models.CharField(blank=True, default='', max_length=100)),
                ('land', models.CharField(blank=True, default='', max_length=100)),
                ('telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
                ('sporter', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
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
        migrations.RunPython(maak_vereniging_8000),
    ]

# end of file
