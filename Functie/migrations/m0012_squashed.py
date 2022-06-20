# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


ADMINISTRATIEVE_REGIO = 100


def init_functies_2019(apps, _):
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
                        nhb_rayon=obj,
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
                        nhb_regio=obj,
                        comp_type=comp_type))
        # for
    # for

    functie_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0019_squashed'),
        ('NhbStructuur', 'm0024_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Functie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=50)),
                ('rol', models.CharField(max_length=5)),
                ('comp_type', models.CharField(blank=True, default='', max_length=2)),
                ('nhb_rayon', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbrayon')),
                ('nhb_regio', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbregio')),
                ('nhb_ver', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='NhbStructuur.nhbvereniging')),
                ('accounts', models.ManyToManyField(blank=True, to='Account.account')),
                ('bevestigde_email', models.EmailField(blank=True, max_length=254)),
                ('nieuwe_email', models.EmailField(blank=True, max_length=254)),
            ],
        ),
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
        migrations.RunPython(init_functies_2019),
    ]

# end of file
