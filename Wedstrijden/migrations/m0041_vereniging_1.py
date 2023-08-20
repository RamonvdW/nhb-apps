# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def add_vereniging_new(apps, _):
    """ migratie van veld vereniging """

    ver_klas = apps.get_model('Vereniging', 'Vereniging')
    fix_klas1 = apps.get_model('Wedstrijden', 'Wedstrijd')
    fix_klas2 = apps.get_model('Wedstrijden', 'WedstrijdKorting')
    fix_klas3 = apps.get_model('Wedstrijden', 'WedstrijdLocatie')

    # maak een cache
    ver_nr2ver = dict()     # [ver_nr] = Vereniging()
    for ver in ver_klas.objects.all():
        ver_nr2ver[ver.ver_nr] = ver
    # for

    for obj in fix_klas1.objects.select_related('organiserende_vereniging', 'uitvoerende_vereniging').all():
        obj.organiserende_vereniging_new = ver_nr2ver[obj.organiserende_vereniging.ver_nr]

        if obj.uitvoerende_vereniging:
            obj.uitvoerende_vereniging_new = ver_nr2ver[obj.uitvoerende_vereniging.ver_nr]

        obj.save(update_fields=['organiserende_vereniging_new', 'uitvoerende_vereniging_new'])
    # for

    for obj in fix_klas2.objects.select_related('uitgegeven_door').all():
        obj.uitgegeven_door_new = ver_nr2ver[obj.uitgegeven_door.ver_nr]
        obj.save(update_fields=['uitgegeven_door_new'])
    # for

    for obj in fix_klas3.objects.prefetch_related('verenigingen').all():
        new_vers = list()
        for old_ver in obj.verenigingen.all():
            new_ver = ver_nr2ver[old_ver.ver_nr]
            new_vers.append(new_ver)
        # for
        obj.verenigingen_new.set(new_vers)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0002_vereniging_1'),
        ('Wedstrijden', 'm0040_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijd',
            name='organiserende_vereniging_new',
            field=models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging'),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='uitvoerende_vereniging_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                    related_name='uitvoerend', to='Vereniging.vereniging'),
        ),
        migrations.AddField(
            model_name='wedstrijdkorting',
            name='uitgegeven_door_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                    related_name='wedstrijd_korting_uitgever', to='Vereniging.vereniging'),
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='verenigingen_new',
            field=models.ManyToManyField(to='Vereniging.vereniging'),
        ),
        migrations.RunPython(add_vereniging_new, migrations.RunPython.noop),
    ]

# end of file
