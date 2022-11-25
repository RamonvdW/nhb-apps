# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def force_new_import(apps, _):

    # verwijder alle speelsterktes zodat we deze opnieuw importeren
    # en daarbij de pas_code opslaan en de aangepaste volgorde zetten
    speelsterkte_klas = apps.get_model('Sporter', 'Speelsterkte')
    speelsterkte_klas.objects.all().delete()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0016_verwijder_secretaris'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(force_new_import),
        migrations.AddField(
            model_name='speelsterkte',
            name='pas_code',
            field=models.CharField(blank=True, default='', max_length=8),
        ),
    ]

# end of file
