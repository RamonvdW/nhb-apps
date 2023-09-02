# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def kopieer_structuur(apps, _):

    klas_rayon_oud = apps.get_model('NhbStructuur', 'Rayon')
    klas_regio_oud = apps.get_model('NhbStructuur', 'Regio')
    klas_cluster_oud = apps.get_model('NhbStructuur', 'Cluster')

    klas_rayon_new = apps.get_model('Geo', 'Rayon')
    klas_regio_new = apps.get_model('Geo', 'Regio')
    klas_cluster_new = apps.get_model('Geo', 'Cluster')

    old2new_rayon = dict()      # [rayon_nr] = nieuwe rayon
    old2new_regio = dict()      # [regio_nr] = nieuwe regio

    # Rayon
    bulk = list()
    for obj in klas_rayon_oud.objects.all():
        bulk.append(
            klas_rayon_new(
                    rayon_nr=obj.rayon_nr,
                    naam=obj.naam))
    # for
    klas_rayon_new.objects.bulk_create(bulk)
    for obj in bulk:
        old2new_rayon[obj.rayon_nr] = obj
    # for

    # Regio
    bulk = list()
    for obj in klas_regio_oud.objects.all():
        bulk.append(
            klas_regio_new(
                regio_nr=obj.regio_nr,
                is_administratief=obj.is_administratief,
                naam=obj.naam,
                rayon_nr=obj.rayon_nr,
                rayon=old2new_rayon[obj.rayon_nr]))
    # for
    klas_regio_new.objects.bulk_create(bulk)
    for obj in bulk:
        old2new_regio[obj.regio_nr] = obj
    # for

    # Cluster
    bulk = list()
    for obj in klas_cluster_oud.objects.select_related('regio').all():
        bulk.append(
            klas_cluster_new(
                regio=old2new_regio[obj.regio.regio_nr],
                letter=obj.letter,
                naam=obj.naam,
                gebruik=obj.gebruik))
    # for
    klas_cluster_new.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0037_rayon_nr'),
    ]

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
        migrations.RunPython(kopieer_structuur, migrations.RunPython.noop)
    ]

# end of file
