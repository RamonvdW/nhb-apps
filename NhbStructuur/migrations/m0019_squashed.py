# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import NhbStructuur.models


RAYONS = (
    (1, "Rayon 1", "Noord Nederland"),
    (2, "Rayon 2", "Zuid-West Nederland"),
    (3, "Rayon 3", "Oost Brabant en Noord Limburg"),
    (4, "Rayon 4", "Zuid- en Midden-Limburg")
)


def init_rayons(apps, _):
    """ Maak de rayons aan """

    # haal de klassen op die van toepassing zijn vóór de migratie
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')

    bulk = list()
    for nummer, naam, geo in RAYONS:
        rayon = rayon_klas(
                    rayon_nr=nummer,    # ook PK
                    naam=naam,
                    geografisch_gebied=geo)
        bulk.append(rayon)
    # for

    rayon_klas.objects.bulk_create(bulk)


def init_regios(apps, _):
    """ Maak de regios aan """

    # haal de klassen op die van toepassing zijn vóór de migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')

    # maak een look-up tabel aan van de rayons
    rayons = dict()     # [rayon_nr] = NhbRayon
    for obj in rayon_klas.objects.all():
        rayons[obj.rayon_nr] = obj
    # for

    bulk = list()

    # rayon 100 voor administratieve verenigingen, zoals het bondsbureau
    regio = regio_klas(
                regio_nr=100,
                rayon=rayons[1],
                naam="Regio 100",
                is_administratief=True)
    bulk.append(regio)

    # elk rayon heeft 4 regios --> totaal 16 regios
    # 101 = rayon 1, eerst regio
    # 116 = rayon 4, laatste regio
    regio_nr = 101    # eerste regio nummer (ook PK)
    for rayon_nr in (1, 2, 3, 4):
        rayon = rayons[rayon_nr]
        for _ in (1, 2, 3, 4):
            regio = regio_klas(
                        regio_nr=regio_nr,
                        naam="Regio %s" % regio_nr,
                        rayon=rayon)
            bulk.append(regio)
            regio_nr += 1
        # for
    # for

    regio_klas.objects.bulk_create(bulk)


def init_clusters(apps, _):
    """ Maak de standaard clusters aan in elke regio """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    cluster_klas = apps.get_model('NhbStructuur', 'NhbCluster')

    bulk = list()

    # geef elke regio 4 clusters
    # in elke competitie
    for regio in regio_klas.objects.filter(is_administratief=False):
        # maak 4 clusters aan voor de 18m
        for letter in 'abcd':
            cluster = cluster_klas(
                            regio=regio,
                            gebruik='18',
                            letter=letter)
            bulk.append(cluster)

        # maak 4 clusters aan voor de 25m
        for letter in 'efgh':
            cluster = cluster_klas(
                            regio=regio,
                            gebruik='25',
                            letter=letter)
            bulk.append(cluster)
        # for
    # for

    cluster_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0019_squashed'),
    ]

    operations = [
        migrations.CreateModel(
            name='NhbRayon',
            fields=[
                ('rayon_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=20)),
                ('geografisch_gebied', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Nhb rayon',
                'verbose_name_plural': 'Nhb rayons',
            },
        ),
        migrations.CreateModel(
            name='NhbRegio',
            fields=[
                ('regio_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=50)),
                ('is_administratief', models.BooleanField(default=False)),
                ('rayon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbrayon')),
            ],
            options={
                'verbose_name': 'Nhb regio',
                'verbose_name_plural': 'Nhb regios',
            },
        ),
        migrations.CreateModel(
            name='NhbCluster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('naam', models.CharField(blank=True, default='', max_length=50)),
                ('regio', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbregio')),
                ('letter', models.CharField(default='x', max_length=1)),
                ('gebruik', models.CharField(choices=[('18', 'Indoor'), ('25', '25m 1pijl')], max_length=2)),
            ],
            options={
                'verbose_name': 'Nhb cluster',
                'verbose_name_plural': 'Nhb clusters',
                'unique_together': {('regio', 'letter')},
            },
        ),
        migrations.CreateModel(
            name='NhbLid',
            fields=[
                ('nhb_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('voornaam', models.CharField(max_length=100)),
                ('achternaam', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=150)),
                ('geboorte_datum', models.DateField(validators=[NhbStructuur.models.validate_geboorte_datum])),
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], max_length=1)),
                ('para_classificatie', models.CharField(blank=True, max_length=30)),
                ('is_actief_lid', models.BooleanField(default=True)),
                ('sinds_datum', models.DateField(validators=[NhbStructuur.models.validate_sinds_datum])),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('lid_tot_einde_jaar', models.PositiveSmallIntegerField(default=0)),
                ('unaccented_naam', models.CharField(blank=True, default='', max_length=200)),
            ],
            options={
                'verbose_name': 'Nhb lid',
                'verbose_name_plural': 'Nhb leden',
            },
        ),
        migrations.CreateModel(
            name='NhbVereniging',
            fields=[
                ('ver_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=200)),
                ('regio', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbregio')),
                ('plaats', models.CharField(blank=True, max_length=100)),
                ('contact_email', models.CharField(blank=True, max_length=150)),
                ('clusters', models.ManyToManyField(blank=True, to='NhbStructuur.NhbCluster')),
                ('geen_wedstrijden', models.BooleanField(default=False)),
                ('secretaris_lid', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='NhbStructuur.nhblid')),
            ],
            options={
                'verbose_name': 'Nhb vereniging',
                'verbose_name_plural': 'Nhb verenigingen',
            },
        ),
        # losse AddField ivm circulaire dependency
        migrations.AddField(
            model_name='nhblid',
            name='bij_vereniging',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.PROTECT,
                                    to='NhbStructuur.NhbVereniging'),
        ),
        migrations.RunPython(init_rayons),
        migrations.RunPython(init_regios),
        migrations.RunPython(init_clusters),
    ]

# end of file
