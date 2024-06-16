# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

RAYONS = (
    (1, "Rayon 1"),     # Noord-Nederland
    (2, "Rayon 2"),     # Zuid-West Nederland
    (3, "Rayon 3"),     # Oost-Brabant en Noord-Limburg
    (4, "Rayon 4"),     # Zuid- en Midden-Limburg
)


def init_rayons(apps, _):
    """ Maak de rayons aan """

    # haal de klassen op die van toepassing zijn vóór de migratie
    rayon_klas = apps.get_model('Geo', 'Rayon')

    bulk = list()
    for nummer, naam in RAYONS:
        rayon = rayon_klas(
                    rayon_nr=nummer,    # ook PK
                    naam=naam)
        bulk.append(rayon)
    # for

    rayon_klas.objects.bulk_create(bulk)


def init_regios(apps, _):
    """ Maak de regios aan met korte namen
        De CRM import levert de feitelijke namen
    """

    # haal de klassen op die van toepassing zijn vóór de migratie
    regio_klas = apps.get_model('Geo', 'Regio')
    rayon_klas = apps.get_model('Geo', 'Rayon')

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
                rayon_nr=rayons[1].rayon_nr,
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
                        rayon=rayon,
                        rayon_nr=rayon.rayon_nr)
            bulk.append(regio)
            regio_nr += 1
        # for
    # for

    regio_klas.objects.bulk_create(bulk)


def init_clusters(apps, _):
    """ Maak de standaard clusters aan in elke regio """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    regio_klas = apps.get_model('Geo', 'Regio')
    cluster_klas = apps.get_model('Geo', 'Cluster')

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
        for letter in 'efgh':  # noqa
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
    dependencies = []

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Rayon',
            fields=[
                ('rayon_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=20)),
            ],
            options={
                'verbose_name': 'Rayon',
            },
        ),
        migrations.CreateModel(
            name='Regio',
            fields=[
                ('regio_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('is_administratief', models.BooleanField(default=False)),
                ('naam', models.CharField(max_length=50)),
                ('rayon_nr', models.PositiveIntegerField(default=0)),
                ('rayon', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Geo.rayon')),
            ],
            options={
                'verbose_name': 'Regio',
                'verbose_name_plural': "Regio's",
            },
        ),
        migrations.CreateModel(
            name='Cluster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('letter', models.CharField(default='x', max_length=1)),
                ('naam', models.CharField(blank=True, default='', max_length=50)),
                ('gebruik', models.CharField(choices=[('18', 'Indoor'), ('25', '25m 1pijl')], max_length=2)),
                ('regio', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Geo.regio')),
            ],
            options={
                'verbose_name': 'Cluster',
                'unique_together': {('regio', 'letter')},
            },
        ),
        migrations.RunPython(init_rayons),
        migrations.RunPython(init_regios),
        migrations.RunPython(init_clusters),
    ]

# end of file
