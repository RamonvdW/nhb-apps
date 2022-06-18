# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_inschrijving(apps, _):
    """ vertaal de oude KalenderInschrijving naar de nieuwe WedstrijdInschrijving """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    inschrijving_new_klas = apps.get_model('Wedstrijden', 'WedstrijdInschrijving')
    product_klas = apps.get_model('Bestel', 'BestelProduct')
    mutatie_klas = apps.get_model('Bestel', 'BestelMutatie')

    inschrijving_oud2new = dict()   # [oud.pk] = new
    for obj in inschrijving_new_klas.objects.select_related('oud').all():
        oud = obj.oud
        inschrijving_oud2new[oud.pk] = obj
    # for

    for obj in product_klas.objects.select_related('inschrijving').exclude(inschrijving=None).all():
        obj.wedstrijd_inschrijving = inschrijving_oud2new[obj.inschrijving.pk]
        obj.save(update_fields=['wedstrijd_inschrijving'])
    # for

    for obj in mutatie_klas.objects.select_related('inschrijving').exclude(inschrijving=None).all():
        obj.wedstrijd_inschrijving = inschrijving_oud2new[obj.inschrijving.pk]
        obj.save(update_fields=['wedstrijd_inschrijving'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0010_squashed'),
        ('Kalender', 'm0012_squashed'),
        ('Wedstrijden', 'm0025_migratie_2'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelmutatie',
            name='wedstrijd_inschrijving',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Wedstrijden.wedstrijdinschrijving'),
        ),
        migrations.AddField(
            model_name='bestelproduct',
            name='wedstrijd_inschrijving',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Wedstrijden.wedstrijdinschrijving'),
        ),
        migrations.RunPython(migreer_inschrijving),
        migrations.RemoveField(
            model_name='bestelmutatie',
            name='inschrijving',
        ),
        migrations.RemoveField(
            model_name='bestelproduct',
            name='inschrijving',
        ),
    ]

# end of file
