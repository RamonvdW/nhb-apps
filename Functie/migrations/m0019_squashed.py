# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


ADMINISTRATIEVE_REGIO = 100
VER_NR = 1368


def init_functies_bondscompetitie_2019(apps, _):

    """ Functies voor de NHB structuur van 2019 """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')
    functie_klas = apps.get_model('Functie', 'Functie')

    comps = (('18', 'Indoor'),
             ('25', '25m 1pijl'))

    bulk = list()

    for comp_type, comp_descr in comps:
        # BKO
        bulk.append(
            functie_klas(
                    beschrijving='BKO ' + comp_descr,
                    rol='BKO',
                    comp_type=comp_type))

        # RKO per rayon
        for obj in (rayon_klas
                    .objects
                    .all()):

            bulk.append(
                functie_klas(
                        beschrijving='RKO Rayon %s %s' % (obj.rayon_nr, comp_descr),
                        rol='RKO',
                        rayon=obj,
                        comp_type=comp_type))
        # for

        # RCL per regio
        for obj in (regio_klas
                    .objects
                    .exclude(regio_nr=ADMINISTRATIEVE_REGIO)):

            bulk.append(
                functie_klas(
                        beschrijving='RCL Regio %s %s' % (obj.regio_nr, comp_descr),
                        rol='RCL',
                        regio=obj,
                        comp_type=comp_type))
        # for
    # for

    functie_klas.objects.bulk_create(bulk)


def init_functies_extra(apps, _):
    """ maak rollen uit die niet met de bondscompetities te doen hebben """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')
    ver_klas = apps.get_model('NhbStructuur', 'NhbVereniging')

    ver = ver_klas.objects.get(ver_nr=VER_NR)

    functie_klas(rol='MO', beschrijving='Manager Opleidingen').save()
    functie_klas(rol='MWZ', beschrijving='Manager Wedstrijdzaken').save()
    functie_klas(rol='SUP', beschrijving='Support').save()
    functie_klas(rol='MWW', beschrijving='Manager Webwinkel', vereniging=ver).save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    replaces = [('Functie', 'm0017_squashed'),
                ('Functie', 'm0018_renames')]

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0023_squashed'),
        ('NhbStructuur', 'm0034_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='VerklaringHanterenPersoonsgegevens',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acceptatie_datum', models.DateTimeField()),
                ('account', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='vhpg', to='Account.account')),
            ],
            options={
                'verbose_name': 'Verklaring Hanteren Persoonsgegevens',
                'verbose_name_plural': 'Verklaring Hanteren Persoonsgegevens',
            },
        ),
        migrations.CreateModel(
            name='Functie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=50)),
                ('rol', models.CharField(max_length=5)),
                ('comp_type', models.CharField(blank=True, default='', max_length=2)),
                ('rayon', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbrayon')),
                ('regio', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbregio')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='NhbStructuur.nhbvereniging')),
                ('accounts', models.ManyToManyField(blank=True, to='Account.account')),
                ('bevestigde_email', models.EmailField(blank=True, max_length=254)),
                ('nieuwe_email', models.EmailField(blank=True, max_length=254)),
                ('telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('laatste_email_over_taken', models.DateTimeField(blank=True, null=True)),
                ('optout_herinnering_taken', models.BooleanField(default=False)),
                ('optout_nieuwe_taak', models.BooleanField(default=False)),
            ],
        ),
        migrations.RunPython(init_functies_bondscompetitie_2019),
        migrations.RunPython(init_functies_extra),
    ]

# end of file
