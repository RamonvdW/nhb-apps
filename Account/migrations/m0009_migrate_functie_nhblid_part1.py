# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_temp_fields(apps, schema_editor):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    account_klas = apps.get_model('Account', 'Account')

    for obj in account_klas.objects.all():
        if obj.nhblid:
            obj.temp_nhb_nr = obj.nhblid.nhb_nr

        obj.temp_functies = ",".join([str(functie.pk) for functie in obj.functies.all()])
        obj.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0008_functies-optioneel'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='account',
            name='temp_nhb_nr',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='account',
            name='temp_functies',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.RunPython(zet_temp_fields),
    ]

# end of file
