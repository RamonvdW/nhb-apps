# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migrate_feedback_from_overig(apps, _):
    """ Maak de enige tabel regel aan die gebruikt wordt door het cron job
        regiocomp_upd_tussenstand.
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    old_klas = apps.get_model('Overig', 'SiteFeedback')
    feedback_klas = apps.get_model('Feedback', 'Feedback')

    bulk = list()

    for old in old_klas.objects.all():              # pragma: no cover
        feedback = feedback_klas(
                        toegevoegd_op=old.toegevoegd_op,
                        site_versie=old.site_versie,
                        gebruiker=old.gebruiker,
                        op_pagina=old.op_pagina,
                        volledige_url='',
                        bevinding=old.bevinding,
                        is_afgehandeld=old.is_afgehandeld,
                        feedback=old.feedback)
        bulk.append(feedback)
    # for

    feedback_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Overig', 'm0009_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('toegevoegd_op', models.DateTimeField(null=True)),
                ('site_versie', models.CharField(max_length=20)),
                ('gebruiker', models.CharField(max_length=50)),
                ('op_pagina', models.CharField(max_length=50)),
                ('volledige_url', models.CharField(max_length=250, null=True, blank=True)),
                ('bevinding', models.CharField(choices=[('8', 'Tevreden'), ('6', 'Bruikbaar'), ('4', 'Moet beter')], max_length=1)),
                ('is_afgehandeld', models.BooleanField(default=False)),
                ('feedback', models.TextField()),
            ],
            options={
                'verbose_name': 'Feedback',
                'verbose_name_plural': 'Feedback',
            },
        ),
        migrations.RunPython(migrate_feedback_from_overig)
    ]

# end of file
