# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

def zet_sessie_pk(apps, _):
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    mutatie_klas = apps.get_model('Bestelling', 'BestellingMutatie')

    # zet alle specifieke verwijzingen over in een anonieme verwijzing

    for mutatie in (mutatie_klas
                    .objects
                    .exclude(sessie=None)
                    .select_related('sessie')):     # pragma: no cover
        mutatie.sessie_pk = mutatie.sessie.pk
        mutatie.save(update_fields=['sessie_pk'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0011_product_pk'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestellingmutatie',
            name='sessie_pk',
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.RunPython(zet_sessie_pk, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='bestellingmutatie',
            name='sessie',
        ),
    ]

# end of file
