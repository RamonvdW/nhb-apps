# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def copy_uitslagen(apps, _):
    """ kopieer WedstrijdUitslag naar CompetitieUitslag """

    uitslag_old_klas = apps.get_model('Wedstrijden', 'WedstrijdUitslag')
    uitslag_new_klas = apps.get_model('Wedstrijden', 'CompetitieWedstrijdUitslag')

    bulk = list()
    for uitslag_old in uitslag_old_klas.objects.all():      # pragma: no cover
        uitslag_new = uitslag_new_klas(
                            max_score=uitslag_old.max_score,
                            afstand_meter=uitslag_old.afstand_meter,
                            is_bevroren=uitslag_old.is_bevroren,
                            old=uitslag_old)

        bulk.append(uitslag_new)
        if len(bulk) > 500:
            uitslag_new_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    if len(bulk):
        uitslag_new_klas.objects.bulk_create(bulk)

    for uitslag_new in (uitslag_new_klas
                        .objects
                        .select_related('old')
                        .prefetch_related('scores')
                        .all()):                        # pragma: no cover

        uitslag_old = uitslag_new.old
        uitslag_new.scores.set(uitslag_old.scores.all())

        for wedstrijd in uitslag_old.wedstrijd_set.all():
            wedstrijd.uitslag2 = uitslag_new
            wedstrijd.save()
        # for
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0008_remove_is_ag'),
        ('Wedstrijden', 'm0008_externe_locatie'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='CompetitieWedstrijdUitslag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_score', models.PositiveSmallIntegerField()),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('is_bevroren', models.BooleanField(default=False)),
                ('scores', models.ManyToManyField(blank=True, to='Score.Score')),
                ('old', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Wedstrijden.WedstrijdUitslag')),
            ],
            options={
                'verbose_name': 'Competitie Wedstrijd Uitslag',
                'verbose_name_plural': 'Competitie Wedstrijd Uitslagen',
            },
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='uitslag2',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                    to='Wedstrijden.competitiewedstrijduitslag'),
        ),
        migrations.RunPython(copy_uitslagen)
    ]

# end of file
