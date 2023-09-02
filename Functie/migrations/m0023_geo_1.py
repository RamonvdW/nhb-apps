# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def vul_geo(apps, _):

    fix_klas = apps.get_model('Functie', 'Functie')

    geo_rayon_klas = apps.get_model('Geo', 'Rayon')
    geo_regio_klas = apps.get_model('Geo', 'Regio')

    nr2rayon = dict()
    nr2regio = dict()

    for rayon in geo_rayon_klas.objects.all():
        nr2rayon[rayon.rayon_nr] = rayon
    # for

    for regio in geo_regio_klas.objects.all():
        nr2regio[regio.regio_nr] = regio
    # for

    for obj in fix_klas.objects.select_related('regio', 'rayon').all():
        if obj.regio:
            obj.geo_regio = nr2regio[obj.regio.regio_nr]
        if obj.rayon:
            obj.geo_rayon = nr2rayon[obj.rayon.rayon_nr]
        obj.save(update_fields=['geo_regio', 'geo_rayon'])
    # obj


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Geo', 'm0001_initial_copy'),
        ('Functie', 'm0022_scheidsrechters'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='functie',
            name='geo_rayon',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Geo.rayon'),
        ),
        migrations.AddField(
            model_name='functie',
            name='geo_regio',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Geo.regio'),
        ),
        migrations.RunPython(vul_geo, migrations.RunPython.noop)
    ]

# end of file
