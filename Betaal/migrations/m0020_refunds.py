# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def bedragen_over_nemen(apps, _):
    # beetje onnodig, want er zijn geen restituties geregistreerd
    transactie_klas = apps.get_model('Betaal', 'BetaalTransactie')
    for transactie in transactie_klas.objects.filter(is_restitutie=True):       # pragma: no cover
        transactie.bedrag_refund = transactie.bedrag_euro_boeking
        transactie.save(update_fields=['bedrag_refund'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0019_bedragen'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='betaaltransactie',
            name='bedrag_refund',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=7),
        ),
        migrations.AddField(
            model_name='betaaltransactie',
            name='refund_id',
            field=models.CharField(default='', max_length=64),
        ),
        migrations.AddField(
            model_name='betaaltransactie',
            name='refund_status',
            field=models.CharField(default='', max_length=15),
        ),
        migrations.RunPython(bedragen_over_nemen, reverse_code=migrations.RunPython.noop)
    ]

# end of file
