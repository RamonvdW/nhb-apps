# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion

""" Deze migratie maakt 128 clusters aan
    (16 regios, 2 competities, 4 clusters elk)
"""


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
    """ Deze functie maakt de standaard clusters aan in elke regio """
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

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0010_regio_is_administratief'),
    ]

    # migratie functies
    operations = [
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
        migrations.AddField(
            model_name='nhbvereniging',
            name='clusters',
            field=models.ManyToManyField(to='NhbStructuur.NhbCluster')
        ),
        migrations.RunPython(init_clusters)
    ]

# end of file
