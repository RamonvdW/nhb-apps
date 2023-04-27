# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models


def sitetijdelijkeurl_overnemen(apps, _):
    """ neem de data over van de tabel in de Overig application """

    oud_klas = apps.get_model('Overig', 'SiteTijdelijkeUrl')
    new_klas = apps.get_model('TijdelijkeCodes', 'TijdelijkeCode')

    bulk = list()
    for obj in (oud_klas
                .objects
                .select_related('hoortbij_account',
                                'hoortbij_functie',
                                'hoortbij_kampioenschap')
                .all()):
        bulk.append(
            new_klas(
                url_code=obj.url_code,
                aangemaakt_op=obj.aangemaakt_op,
                geldig_tot=obj.geldig_tot,
                dispatch_to=obj.dispatch_to,
                hoortbij_account=obj.hoortbij_account,
                hoortbij_functie=obj.hoortbij_functie,
                hoortbij_kampioenschap=obj.hoortbij_kampioenschap)
        )
    # for

    new_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0025_merge_accountemail_2'),
        ('Competitie', 'm0096_squashed'),
        ('Functie', 'm0017_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='TijdelijkeCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_code', models.CharField(max_length=32)),
                ('aangemaakt_op', models.DateTimeField()),
                ('geldig_tot', models.DateTimeField()),
                ('dispatch_to', models.CharField(default='', max_length=20)),
                ('hoortbij_account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('hoortbij_functie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Functie.functie')),
                ('hoortbij_kampioenschap', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.kampioenschapsporterboog')),
            ],
        ),
        migrations.RunPython(sitetijdelijkeurl_overnemen, reverse_code=migrations.RunPython.noop)
    ]

# end of file
