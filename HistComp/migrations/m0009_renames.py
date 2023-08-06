# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def rename_ib(apps, _):
    """ een aantal seizoenen heeft hoofdletter te veel """

    bad_name = "Instinctive Bow"
    fix_name = "Instinctive bow"

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    histcomp_klas = apps.get_model('HistComp', 'HistCompetitie')

    # in 2021/2022 werd 5 gebruikt voor de Indoor (in verband met corona)
    for histcomp in histcomp_klas.objects.filter(beschrijving=bad_name):      # pragma: no cover
        histcomp.beschrijving = fix_name
        histcomp.save(update_fields=['beschrijving'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0008_aantal'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='histcompetitie',
            old_name='boog_str',
            new_name='beschrijving',
        ),
        migrations.RenameModel(
            old_name='HistCompetitieIndividueel',
            new_name='HistCompRegioIndiv',
        ),
        migrations.DeleteModel(name='HistCompetitieTeam'),
        migrations.RunPython(code=rename_ib,
                             reverse_code=migrations.RunPython.noop)
    ]

# end of file
