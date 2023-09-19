# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import datetime


def zet_fase_d(apps, _):

    comp_klas = apps.get_model('Competitie', 'Competitie')
    for comp in comp_klas.objects.all():                                    # pragma: no cover
        comp.begin_fase_D_indiv = datetime.date(comp.begin_jaar, 8, 15)     # 15 augustus
        comp.save(update_fields=['begin_fase_D_indiv'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0104_locatie'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitie',
            name='begin_fase_D_indiv',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.RunPython(zet_fase_d, migrations.RunPython.noop)
    ]

# end of file
