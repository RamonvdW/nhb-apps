# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


# TODO: verplaats naar Geo/definities
RAYONS = (
    (1, "Rayon 1"),     # Noord-Nederland
    (2, "Rayon 2"),     # Zuid-West Nederland
    (3, "Rayon 3"),     # Oost-Brabant en Noord-Limburg
    (4, "Rayon 4"),     # Zuid- en Midden-Limburg
)

ADMINISTRATIEVE_REGIO = 100
VER_NR_BONDSBUREAU = 1368


# TODO: verplaats naar Geo/migrations/squashed
def init_rayons(apps, _):
    """ Maak de rayons aan """

    # haal de klassen op die van toepassing zijn vóór de migratie
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')

    bulk = list()
    for nummer, naam in RAYONS:
        rayon = rayon_klas(
                    rayon_nr=nummer,    # ook PK
                    naam=naam)
        bulk.append(rayon)
    # for

    rayon_klas.objects.bulk_create(bulk)


# TODO: verplaats naar Geo/migrations/squashed
def init_regios(apps, _):
    """ Maak de regios aan met korte namen
        De CRM import levert de feitelijke namen
    """

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


# TODO: verplaats naar Geo/migrations/squashed
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


# TODO: verplaats naar Vereniging/migrations/squashed
def maak_ver_bondsbureau(apps, _):

    """ Maak de vereniging Bondsbureau aan, want deze is nodig voor de functie MWW
        Verdere details volgen uit de CRM import.
    """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    ver_klas = apps.get_model('NhbStructuur', 'NhbVereniging')

    # alleen bij een lege database aanmaken
    ver, is_created = ver_klas.objects.get_or_create(
                                    ver_nr=VER_NR_BONDSBUREAU,
                                    regio=regio_klas.objects.get(regio_nr=ADMINISTRATIEVE_REGIO))
    if is_created:      # pragma: no branch
        ver.naam = 'Tijdelijk'
        ver.save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    replaces = [('NhbStructuur', 'm0031_squashed'),
                ('NhbStructuur', 'm0032_korter'),
                ('NhbStructuur', 'm0033_ver_is_extern')]

    # volgorde afdwingen
    dependencies = []

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='NhbRayon',
            fields=[
                ('rayon_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=20)),
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
                ('rayon', models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbrayon')),
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
                ('regio', models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbregio')),
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
            name='NhbVereniging',
            fields=[
                ('ver_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=50)),
                ('regio', models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbregio')),
                ('plaats', models.CharField(blank=True, max_length=35)),
                ('clusters', models.ManyToManyField(blank=True, to='NhbStructuur.nhbcluster')),
                ('geen_wedstrijden', models.BooleanField(default=False)),
                ('kvk_nummer', models.CharField(blank=True, default='', max_length=15)),
                ('telefoonnummer', models.CharField(blank=True, default='', max_length=20)),
                ('website', models.CharField(blank=True, default='', max_length=100)),
                ('adres_regel1', models.CharField(blank=True, default='', max_length=50)),
                ('adres_regel2', models.CharField(blank=True, default='', max_length=50)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('bank_bic', models.CharField(blank=True, default='', max_length=11)),
                ('bank_iban', models.CharField(blank=True, default='', max_length=18)),
                ('is_extern', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Nhb vereniging',
                'verbose_name_plural': 'Nhb verenigingen',
            },
        ),
        migrations.RunPython(init_rayons),
        migrations.RunPython(init_regios),
        migrations.RunPython(init_clusters),
        migrations.RunPython(maak_ver_bondsbureau),
    ]

# end of file
