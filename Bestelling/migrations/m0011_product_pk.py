# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_product_pk(apps, _):
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    mutatie_klas = apps.get_model('Bestelling', 'BestellingMutatie')

    # zet alle specifieke verwijzingen over in een anonieme verwijzing

    for mutatie in mutatie_klas.objects.exclude(wedstrijd_inschrijving=None).select_related('wedstrijd_inschrijving'):
        mutatie.product_pk = mutatie.wedstrijd_inschrijving.pk
        mutatie.save(update_fields=['product_pk'])
    # for

    for mutatie in mutatie_klas.objects.exclude(evenement_inschrijving=None).select_related('evenement_inschrijving'):
        mutatie.product_pk = mutatie.evenement_inschrijving.pk
        mutatie.save(update_fields=['product_pk'])
    # for

    for mutatie in mutatie_klas.objects.exclude(opleiding_inschrijving=None).select_related('opleiding_inschrijving'):
        mutatie.product_pk = mutatie.opleiding_inschrijving.pk
        mutatie.save(update_fields=['product_pk'])
    # for

    for mutatie in mutatie_klas.objects.exclude(webwinkel_keuze=None).select_related('webwinkel_keuze'):
        mutatie.product_pk = mutatie.webwinkel_keuze.pk
        mutatie.save(update_fields=['product_pk'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0010_aanpassen'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestellingmutatie',
            name='product_pk',
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.RunPython(zet_product_pk, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='bestellingmutatie',
            name='evenement_inschrijving',
        ),
        migrations.RemoveField(
            model_name='bestellingmutatie',
            name='opleiding_inschrijving',
        ),
        migrations.RemoveField(
            model_name='bestellingmutatie',
            name='webwinkel_keuze',
        ),
        migrations.RemoveField(
            model_name='bestellingmutatie',
            name='wedstrijd_inschrijving',
        ),
    ]

# end of file
