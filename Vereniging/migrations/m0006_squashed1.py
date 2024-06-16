# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Geo.definities import ADMINISTRATIEVE_REGIO
from Vereniging.definities import VER_NR_BONDSBUREAU


def maak_ver_bondsbureau(apps, _):

    """ Maak de vereniging Bondsbureau aan, want deze is nodig voor de functie MWW
        Verdere details volgen uit de CRM import.
    """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    regio_klas = apps.get_model('Geo', 'Regio')
    ver_klas = apps.get_model('Vereniging', 'Vereniging')

    # alleen bij een lege database aanmaken
    ver, is_created = ver_klas.objects.get_or_create(
                                    ver_nr=VER_NR_BONDSBUREAU,
                                    regio=regio_klas.objects.get(regio_nr=ADMINISTRATIEVE_REGIO))
    if is_created:      # pragma: no branch
        ver.naam = 'Tijdelijk'
        ver.save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Geo', 'm0002_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Vereniging',
            fields=[
                ('ver_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=50)),
                ('adres_regel1', models.CharField(blank=True, default='', max_length=50)),
                ('adres_regel2', models.CharField(blank=True, default='', max_length=50)),
                ('plaats', models.CharField(blank=True, max_length=35)),
                ('geen_wedstrijden', models.BooleanField(default=False)),
                ('is_extern', models.BooleanField(default=False)),
                ('kvk_nummer', models.CharField(blank=True, default='', max_length=15)),
                ('website', models.CharField(blank=True, default='', max_length=100)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('telefoonnummer', models.CharField(blank=True, default='', max_length=20)),
                ('bank_iban', models.CharField(blank=True, default='', max_length=18)),
                ('bank_bic', models.CharField(blank=True, default='', max_length=11)),
                ('clusters', models.ManyToManyField(blank=True, to='Geo.cluster')),
                ('regio', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Geo.regio')),
            ],
            options={
                'verbose_name': 'Vereniging',
                'verbose_name_plural': 'Verenigingen',
            },
        ),
        migrations.RunPython(maak_ver_bondsbureau),
    ]

# end of file
