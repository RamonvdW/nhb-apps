# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_disciplines(apps, _):
    """ voor accommodaties, zet de nieuwe discipline velden """

    locatie_klas = apps.get_model('Wedstrijden', 'WedstrijdLocatie')

    # zet de discipline_indoor/outdoor voor alle accommodaties
    for locatie in locatie_klas.objects.all():                      # pragma: no cover
        if locatie.baan_type == 'B':        # buitenbaan
            locatie.discipline_outdoor = True
        else:
            locatie.discipline_indoor = True
        locatie.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0007_buitenbanen'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='wedstrijdlocatie',
            name='baan_type',
            field=models.CharField(
                choices=[('X', 'Onbekend'), ('O', 'Volledig overdekte binnenbaan'), ('H', 'Binnen-buiten schieten'),
                         ('B', 'Buitenbaan'), ('E', 'Extern')], default='X', max_length=1),
        ),
        migrations.AlterModelOptions(
            name='wedstrijdlocatie',
            options={'verbose_name': 'Wedstrijd locatie', 'verbose_name_plural': 'Wedstrijd locaties'},
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='discipline_3d',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='discipline_clout',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='discipline_indoor',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='discipline_outdoor',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='discipline_run',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='discipline_veld',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='naam',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.RunPython(zet_disciplines)
    ]

# end of file
