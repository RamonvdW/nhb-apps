# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion
import NhbStructuur.models


RAYONS_2018 = (
    (1, "Rayon 1", "Noord Nederland"),
    (2, "Rayon 2", "Zuid-West Nederland"),
    (3, "Rayon 3", "Oost Brabant en Noord Limburg"),
    (4, "Rayon 4", "Zuid- en Midden-Limburg")
)


def maak_rayons_2018(rayon_klas):
    """ Deze functie maakt de rayons aan
        Wordt ook gebruikt vanuit NhbStructuur/tests.py
    """
    rayon = rayon_klas()
    for nummer, naam, geo in RAYONS_2018:
        rayon.rayon_nr = nummer     # ook PK
        rayon.naam = naam
        rayon.geografisch_gebied = geo
        rayon.save()
    # for


def init_rayons_2018(apps, _):
    """ Standaard rayons 2018 """

    # haal de klassen op die van toepassing zijn vóór de migratie
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')
    maak_rayons_2018(rayon_klas)


def maak_regios_2018(rayon_klas, regio_klas):
    """ Deze functie maak de regios aan
        Wordt ook gebruikt vanuit NhbStructuur/tests.py
    """
    # standard regio's in 2019-07-20:
    # elk rayon heeft 4 regios --> totaal 16 regios
    # 101 = rayon 1, eerst regio
    # 116 = rayon 4, laatste regio
    regio = regio_klas()
    regio.regio_nr = 101    # eerste regio nummer (ook PK)
    for rayon_nr in (1, 2, 3, 4):
        # haal de rayon referentie op
        regio.rayon = rayon_klas.objects.get(rayon_nr=rayon_nr)

        # 4 regios per rayon
        for _ in (1, 2, 3, 4):
            regio.naam = "Regio %s" % regio.regio_nr
            regio.save()

            regio.regio_nr += 1     # nieuwe PK
        # for
    # for


def maak_regios_2019(rayon_klas, regio_klas):
    """ Deze functie maak de regios aan
        Wordt ook gebruikt vanuit NhbStructuur/tests.py
    """
    # standard regio's in 2019-12-15:
    # rayon 100 voor administratieve verenigingen, zoals het bondsbureau
    regio = regio_klas()
    regio.regio_nr = 100    # ook PK
    regio.rayon = rayon_klas.objects.get(rayon_nr=1)
    regio.naam = "Regio %s" % regio.regio_nr
    regio.is_administratief = True
    regio.save()


def init_regios_2019(apps, _):
    """ Wijziging regios 2019 """
    # haal de klassen op die van toepassing zijn vóór de migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')
    maak_regios_2018(rayon_klas, regio_klas)
    maak_regios_2019(rayon_klas, regio_klas)


def maak_regio_clusters(cluster_klas, regio, gebruik, letters):
    new_clusters = list()
    for letter in letters:
        cluster = cluster_klas()
        cluster.regio = regio
        cluster.gebruik = gebruik
        cluster.letter = letter
        new_clusters.append(cluster)
    # for
    return new_clusters


def maak_clusters(regio_klas, cluster_klas):
    """ Deze functie maakt de standaard clusters aan in elke regio
        Totaal 128 clusters: 16 regios, 2 competities, 4 clusters elk
    """
    new_clusters = list()
    for regio in regio_klas.objects.filter(is_administratief=False):
        # maak 4 clusters aan voor de 18m en 25m
        new_clusters.extend(maak_regio_clusters(cluster_klas, regio, '18', 'abcd'))
        new_clusters.extend(maak_regio_clusters(cluster_klas, regio, '25', 'efgh'))
    # for
    return new_clusters


def init_clusters(apps, _):
    """ Maak de standaard clusters aan in elke regio """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    cluster_klas = apps.get_model('NhbStructuur', 'NhbCluster')

    new_clusters = maak_clusters(regio_klas, cluster_klas)
    cluster_klas.objects.bulk_create(new_clusters)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0013_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='NhbRayon',
            fields=[
                ('rayon_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=20)),
                ('geografisch_gebied', models.CharField(max_length=50)),
            ],
            options={'verbose_name': 'Nhb rayon', 'verbose_name_plural': 'Nhb rayons'},
        ),
        migrations.CreateModel(
            name='NhbRegio',
            fields=[
                ('regio_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=50)),
                ('is_administratief', models.BooleanField(default=False)),
                ('rayon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRayon')),
            ],
            options={'verbose_name': 'Nhb regio', 'verbose_name_plural': 'Nhb regios'},
        ),
        migrations.CreateModel(
            name='NhbCluster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('naam', models.CharField(default='', max_length=50, blank=True)),
                ('regio', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRegio')),
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
                ('account', models.ForeignKey(blank=True, null=True,
                                              on_delete=django.db.models.deletion.SET_NULL,
                                              to='Account.Account')),
            ],
            options={'verbose_name': 'Nhb lid', 'verbose_name_plural': 'Nhb leden'},
        ),
        migrations.CreateModel(
            name='NhbVereniging',
            fields=[
                ('nhb_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=200)),
                ('regio', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRegio')),
                ('plaats', models.CharField(blank=True, max_length=100)),
                ('contact_email', models.CharField(blank=True, max_length=150)),
                ('clusters', models.ManyToManyField(blank=True, to='NhbStructuur.NhbCluster')),
                ('geen_wedstrijden', models.BooleanField(default=False)),
                ('secretaris_lid',
                 models.ForeignKey(blank=True, null=True,
                                   on_delete=django.db.models.deletion.SET_NULL,
                                   to='NhbStructuur.NhbLid')),
            ],
            options={'verbose_name': 'Nhb vereniging', 'verbose_name_plural': 'Nhb verenigingen'},
        ),
        # losse AddField ivm circulaire dependency
        migrations.AddField(
            model_name='nhblid',
            name='bij_vereniging',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.PROTECT,
                                    to='NhbStructuur.NhbVereniging'),
        ),
        migrations.RunPython(init_rayons_2018),
        migrations.RunPython(init_regios_2019),
        migrations.RunPython(init_clusters)
    ]

# end of file
