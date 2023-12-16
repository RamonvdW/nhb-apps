# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_onderwerp(apps, _):

    klas_taak = apps.get_model('Taken', 'Taak')

    for taak in klas_taak.objects.all():                            # pragma: no cover
        taak.onderwerp = taak.beschrijving.split('\n')[0][:100]
        taak.save(update_fields=['onderwerp'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Taken', 'm0005_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='taak',
            name='onderwerp',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.RunPython(zet_onderwerp, reverse_code=migrations.RunPython.noop),
    ]

# end of file
