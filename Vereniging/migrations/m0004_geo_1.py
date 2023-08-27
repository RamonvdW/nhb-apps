# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def vul_geo(apps, _):

    fix_klas = apps.get_model('Vereniging', 'Vereniging')

    geo_regio_klas = apps.get_model('Geo', 'Regio')
    geo_cluster_klas = apps.get_model('Geo', 'Cluster')

    regio_letter2cluster = dict()
    nr2regio = dict()

    for cluster in geo_cluster_klas.objects.select_related('regio').all():
        regio_letter2cluster[(cluster.regio.regio_nr, cluster.letter)] = cluster
    # for

    for regio in geo_regio_klas.objects.all():
        nr2regio[regio.regio_nr] = regio
    # for

    for obj in fix_klas.objects.select_related('regio').prefetch_related('clusters').all():
        obj.geo_regio = nr2regio[obj.regio.regio_nr]
        obj.save(update_fields=['geo_regio'])

        new_clusters = [regio_letter2cluster[(cluster.regio.regio_nr, cluster.letter)]
                        for cluster in obj.clusters.all()]
        obj.geo_clusters.set(new_clusters)
    # obj


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Geo', 'm0001_initial_copy'),
        ('Vereniging', 'm0003_vereniging_2'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='vereniging',
            name='geo_clusters',
            field=models.ManyToManyField(blank=True, to='Geo.cluster'),
        ),
        migrations.AddField(
            model_name='vereniging',
            name='geo_regio',
            field=models.ForeignKey(default=None, on_delete=models.deletion.PROTECT, to='Geo.regio', null=True),
            preserve_default=False,
        ),
        migrations.RunPython(vul_geo, migrations.RunPython.noop)
    ]

# end of file
