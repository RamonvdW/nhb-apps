# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def vul_geo(apps, _):

    fix1_klas = apps.get_model('Competitie', 'Regiocompetitie')             # regio
    fix2_klas = apps.get_model('Competitie', 'RegiocompetitieRonde')        # cluster
    fix3_klas = apps.get_model('Competitie', 'Kampioenschap')               # rayon

    geo_rayon_klas = apps.get_model('Geo', 'Rayon')
    geo_regio_klas = apps.get_model('Geo', 'Regio')
    geo_cluster_klas = apps.get_model('Geo', 'Cluster')

    nr2rayon = dict()
    nr2regio = dict()
    regio_letter2cluster = dict()

    if True:        # pragma: no cover
        for rayon in geo_rayon_klas.objects.all():
            nr2rayon[rayon.rayon_nr] = rayon
        # for

        for regio in geo_regio_klas.objects.all():
            nr2regio[regio.regio_nr] = regio
        # for

        for cluster in geo_cluster_klas.objects.select_related('regio').all():
            regio_letter2cluster[(cluster.regio.regio_nr, cluster.letter)] = cluster
        # for

        for obj in fix1_klas.objects.select_related('regio').all():
            obj.geo_regio = nr2regio[obj.regio.regio_nr]
            obj.save(update_fields=['geo_regio'])
        # obj

        for obj in fix2_klas.objects.exclude(cluster=None).select_related('cluster', 'cluster__regio').all():
            obj.geo_cluster = regio_letter2cluster[(obj.cluster.regio.regio_nr, obj.cluster.letter)]
            obj.save(update_fields=['geo_cluster'])
        # obj

        for obj in fix3_klas.objects.exclude(rayon=None).select_related('rayon').all():
            obj.geo_rayon = nr2rayon[obj.rayon.rayon_nr]
            obj.save(update_fields=['geo_rayon'])
        # obj


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Geo', 'm0001_initial_copy'),
        ('Competitie', 'm0105_fase_d'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschap',
            name='geo_rayon',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Geo.rayon'),
        ),
        migrations.AddField(
            model_name='regiocompetitie',
            name='geo_regio',
            field=models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Geo.regio'),
        ),
        migrations.AddField(
            model_name='regiocompetitieronde',
            name='geo_cluster',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Geo.cluster'),
        ),
        migrations.RunPython(vul_geo, migrations.RunPython.noop)
    ]

# end of file
