# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def migrate_sporter(apps, _):

    """ NhbLid omzetten naar Sporter """

    record_klas = apps.get_model('Records', 'IndivRecord')
    sporter_klas = apps.get_model('Sporter', 'Sporter')

    cache = dict()
    for obj in sporter_klas.objects.all():                      # pragma: no cover
        cache[obj.pk] = obj
    # for

    for obj in record_klas.objects.exclude(nhb_lid=None):       # pragma: no cover
        obj.sporter = cache[obj.nhb_lid.nhb_nr]
        obj.save(update_fields=['sporter'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0002_copy_data'),
        ('Records', 'm0009_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='indivrecord',
            name='sporter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Sporter.sporter'),
        ),
        migrations.RunPython(migrate_sporter),
        migrations.RemoveField(
            model_name='indivrecord',
            name='nhb_lid'),
    ]

# end of file
