# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Betaal.definities import (TRANSACTIE_TYPE_HANDMATIG, TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                               TRANSACTIE_TYPE_MOLLIE_RESTITUTIE)


def set_transactie_type(apps, _):

    transactie_klas = apps.get_model('Betaal', 'BetaalTransactie')

    transactie_klas.objects.filter(is_handmatig=True).update(transactie_type=TRANSACTIE_TYPE_HANDMATIG)
    transactie_klas.objects.filter(is_restitutie=True).update(transactie_type=TRANSACTIE_TYPE_MOLLIE_RESTITUTIE)
    transactie_klas.objects.filter(is_restitutie=False, is_handmatig=False).update(transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0023_remove_oud_1'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='betaaltransactie',
            name='transactie_type',
            field=models.CharField(default='HA', max_length=2),
        ),
        migrations.RunPython(set_transactie_type),
        migrations.RenameField(
            model_name='betaaltransactie',
            old_name='bedrag_euro_klant',
            new_name='bedrag_handmatig',
        ),
        migrations.RemoveField(
            model_name='betaaltransactie',
            name='is_handmatig',
        ),
        migrations.RemoveField(
            model_name='betaaltransactie',
            name='is_restitutie',
        ),
    ]

# end of file
