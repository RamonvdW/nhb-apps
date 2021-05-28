# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def maak_extra_leeftijdsklassen(apps, _):
    """ Maak de Masters en Veteranen leeftijdsklassen aan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    # pas de senioren klassen aan
    for lkl in leeftijdsklasse_klas.objects.filter(klasse_kort='Senior'):
        lkl.max_wedstrijdleeftijd = 49
        lkl.save(update_fields=['max_wedstrijdleeftijd'])
    # for

    # de nieuwe 'volgens_wa' vlag is gezet op alle klassen
    # haal deze eraf bij de aspiranten klassen
    for lkl in leeftijdsklasse_klas.objects.filter(klasse_kort='Aspirant'):
        lkl.volgens_wa = False
        lkl.save(update_fields=['volgens_wa'])
    # for

    # haal de leeftijdsgrens weg bij Senioren
    for lkl in leeftijdsklasse_klas.objects.filter(klasse_kort='Senior'):
        lkl.min_wedstrijdleeftijd = 0
        lkl.max_wedstrijdleeftijd = 0
        lkl.save(update_fields=['min_wedstrijdleeftijd', 'max_wedstrijdleeftijd'])
    # for

    # haal de leeftijd ondergrens weg bij de jeugdklassen
    for lkl in leeftijdsklasse_klas.objects.filter(max_wedstrijdleeftijd__lte=20):
        lkl.min_wedstrijdleeftijd = 0
        lkl.save(update_fields=['min_wedstrijdleeftijd'])
    # for

    # masters (50+)
    leeftijdsklasse_klas(
        afkorting='MH', geslacht='M',
        klasse_kort='Master',
        beschrijving='Masters, mannen',
        min_wedstrijdleeftijd=50,
        max_wedstrijdleeftijd=0,
        volgens_wa=False).save()            # volgens_wa moet True zijn - correctie in m0017

    leeftijdsklasse_klas(
        afkorting='MV', geslacht='V',
        klasse_kort='Master',
        beschrijving='Masters, vrouwen',
        min_wedstrijdleeftijd=50,
        max_wedstrijdleeftijd=0,
        volgens_wa=False).save()            # volgens_wa moet True zijn - correctie in m0017

    # veteranen (60+)
    leeftijdsklasse_klas(
        afkorting='VH', geslacht='M',
        klasse_kort='Veteraan',
        beschrijving='Veteranen, mannen',
        min_wedstrijdleeftijd=60,
        max_wedstrijdleeftijd=0,
        volgens_wa=False).save()

    leeftijdsklasse_klas(
        afkorting='VV', geslacht='V',
        klasse_kort='Veteraan',
        beschrijving='Veteranen, vrouwen',
        min_wedstrijdleeftijd=60,
        max_wedstrijdleeftijd=0,
        volgens_wa=False).save()


KALENDERWEDSTRIJDENKLASSEN = (
    (100, 'R', 'VH', 'Recurve veteraan mannen'),
    (101, 'R', 'VV', 'Recurve veteraan vrouwen'),

    (110, 'R', 'MH', 'Recurve master mannen'),
    (111, 'R', 'MV', 'Recurve master vrouwen'),

    (120, 'R', 'SH', 'Recurve senior mannen'),
    (121, 'R', 'SV', 'Recurve senior vrouwen'),

    (130, 'R', 'JH', 'Recurve junior mannen'),
    (131, 'R', 'JV', 'Recurve junior vrouwen'),

    (140, 'R', 'CH', 'Recurve cadet jongens'),
    (141, 'R', 'CV', 'Recurve cadet meisjes'),

    (150, 'R', 'AH2', 'Recurve aspirant jongens'),
    (151, 'R', 'AV2', 'Recurve aspirant meisjes'),


    (200, 'C', 'VH', 'Compound veteraan mannen'),
    (201, 'C', 'VV', 'Compound veteraan vrouwen'),

    (210, 'C', 'MH', 'Compound master mannen'),
    (211, 'C', 'MV', 'Compound master vrouwen'),

    (220, 'C', 'SH', 'Compound senior mannen'),
    (221, 'C', 'SV', 'Compound senior vrouwen'),

    (230, 'C', 'JH', 'Compound junior mannen'),
    (231, 'C', 'JV', 'Compound junior vrouwen'),

    (240, 'C', 'CH', 'Compound cadet jongens'),
    (241, 'C', 'CV', 'Compound cadet meisjes'),

    (250, 'C', 'AH2', 'Compound aspirant jongens'),
    (251, 'C', 'AV2', 'Compound aspirant meisjes'),


    (300, 'BB', 'VH', 'Barebow veteraan mannen'),
    (301, 'BB', 'VV', 'Barebow veteraan vrouwen'),

    (310, 'BB', 'MH', 'Barebow master mannen'),
    (311, 'BB', 'MV', 'Barebow master vrouwen'),

    (320, 'BB', 'SH', 'Barebow senior mannen'),
    (321, 'BB', 'SV', 'Barebow senior vrouwen'),

    (330, 'BB', 'JH', 'Barebow junior mannen'),
    (331, 'BB', 'JV', 'Barebow junior vrouwen'),

    (340, 'BB', 'CH', 'Barebow cadet jongens'),
    (341, 'BB', 'CV', 'Barebow cadet meisjes'),

    (350, 'BB', 'AH2', 'Barebow aspirant jongens'),
    (351, 'BB', 'AV2', 'Barebow aspirant meisjes'),


    (400, 'IB', 'VH', 'Longbow veteraan mannen'),
    (401, 'IB', 'VV', 'Longbow veteraan vrouwen'),

    (410, 'IB', 'MH', 'Longbow master mannen'),
    (411, 'IB', 'MV', 'Longbow master vrouwen'),

    (420, 'IB', 'SH', 'Longbow senior mannen'),
    (421, 'IB', 'SV', 'Longbow senior vrouwen'),

    (430, 'IB', 'JH', 'Longbow junior mannen'),
    (431, 'IB', 'JV', 'Longbow junior vrouwen'),

    (440, 'IB', 'CH', 'Longbow cadet jongens'),
    (441, 'IB', 'CV', 'Longbow cadet meisjes'),

    (450, 'IB', 'AH2', 'Longbow aspirant jongens'),
    (451, 'IB', 'AV2', 'Longbow aspirant meisjes'),


    (500, 'LB', 'VH', 'Instinctive Bow veteraan mannen'),
    (501, 'LB', 'VV', 'Instinctive Bow veteraan vrouwen'),

    (510, 'LB', 'MH', 'Instinctive Bow master mannen'),
    (511, 'LB', 'MV', 'Instinctive Bow master vrouwen'),

    (520, 'LB', 'SH', 'Instinctive Bow senior mannen'),
    (521, 'LB', 'SV', 'Instinctive Bow senior vrouwen'),

    (530, 'LB', 'JH', 'Instinctive Bow junior mannen'),
    (531, 'LB', 'JV', 'Instinctive Bow junior vrouwen'),

    (540, 'LB', 'CH', 'Instinctive Bow cadet jongens'),
    (541, 'LB', 'CV', 'Instinctive Bow cadet meisjes'),

    (550, 'LB', 'AH2', 'Instinctive Bow aspirant jongens'),
    (551, 'LB', 'AV2', 'Instinctive Bow aspirant meisjes'),
)


def maak_kalenderwedstrijdklassen(apps, _):

    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    afk2boog = dict()       # [afkorting] = BoogType
    for boog in boogtype_klas.objects.all():
        afk2boog[boog.afkorting] = boog
    # for

    afk2lkl = dict()        # [afkorting] = LeeftijdsKlasse
    for lkl in leeftijdsklasse_klas.objects.all():
        afk2lkl[lkl.afkorting] = lkl
    # for

    for volgorde, boog_afk, lkl_afk, beschrijving in KALENDERWEDSTRIJDENKLASSEN:
        boog = afk2boog[boog_afk]
        lkl = afk2lkl[lkl_afk]
        kalenderwedstrijdklasse_klas(
                beschrijving=beschrijving,
                boogtype=boog,
                leeftijdsklasse=lkl,
                volgorde=volgorde).save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0014_remove_team_wkl_boogtypen'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='leeftijdsklasse',
            name='volgens_wa',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterModelOptions(
            name='indivwedstrijdklasse',
            options={'verbose_name': 'Indiv Wedstrijdklasse', 'verbose_name_plural': 'Indiv Wedstrijdklassen'},
        ),
        migrations.RunPython(maak_extra_leeftijdsklassen),
        migrations.CreateModel(
            name='KalenderWedstrijdklasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('leeftijdsklasse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.leeftijdsklasse')),
            ],
            options={
                'verbose_name': 'KalenderWedstrijdklasse',
                'verbose_name_plural': 'KalenderWedstrijdklassen',
            },
        ),
        migrations.RunPython(maak_kalenderwedstrijdklassen)
    ]

# end of file
