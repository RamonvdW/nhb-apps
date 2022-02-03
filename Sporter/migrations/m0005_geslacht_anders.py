# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.models import GESLACHT_ANDERS


def zet_voorkeur_geslacht(apps, _):

    """ zet de nieuwe velden op SporterVoorkeuren voor 'geslacht anders' """

    # haal de klassen op die van toepassing zijn vóór de migratie
    voorkeuren_klas = apps.get_model('Sporter', 'SporterVoorkeuren')

    # defaults na migration:
    # wedstrijd_geslacht = M
    # wedstrijd_geslacht_gekozen = True

    for voorkeuren in voorkeuren_klas.objects.select_related('sporter').all():      # pragma: no cover
        geslacht = voorkeuren.sporter.geslacht

        if geslacht != GESLACHT_ANDERS:
            # M/V forceren in de voorkeuren
            if voorkeuren.wedstrijd_geslacht != geslacht:
                # forceer het geslacht; er mag geen keuze gemaakt worden
                voorkeuren.wedstrijd_geslacht = geslacht
                voorkeuren.save(update_fields=['wedstrijd_geslacht'])
        else:
            # X --> laat keuze maken
            voorkeuren.wedstrijd_geslacht_gekozen = False
            voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0004_indexes'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='sportervoorkeuren',
            name='wedstrijd_geslacht',
            field=models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], default='M', max_length=1),
        ),
        migrations.AddField(
            model_name='sportervoorkeuren',
            name='wedstrijd_geslacht_gekozen',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='sporter',
            name='geslacht',
            field=models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw'), ('X', 'Anders')], max_length=1),
        ),
        migrations.RunPython(zet_voorkeur_geslacht)
    ]

# end of file
