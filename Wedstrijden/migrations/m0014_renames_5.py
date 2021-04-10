# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def copy_plannen(apps, _):
    """ kopieer WedstrijdenPlan naar CompetitieWedstrijdenPlan """

    plan_old_klas = apps.get_model('Wedstrijden', 'WedstrijdenPlan')
    plan_new_klas = apps.get_model('Wedstrijden', 'CompetitieWedstrijdenPlan')

    bulk = list()
    for plan_old in plan_old_klas.objects.all():      # pragma: no cover
        plan_new = plan_new_klas(
                            bevat_hiaat=plan_old.bevat_hiaat,
                            old=plan_old)

        bulk.append(plan_new)
        if len(bulk) > 500:
            plan_new_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    if len(bulk):
        plan_new_klas.objects.bulk_create(bulk)

    for plan_new in (plan_new_klas
                     .objects
                     .select_related('old')
                     .prefetch_related('wedstrijden')
                     .all()):                        # pragma: no cover

        plan_old = plan_new.old
        plan_new.wedstrijden.set(plan_old.wedstrijden.all())
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0013_renames_4'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='CompetitieWedstrijdenPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bevat_hiaat', models.BooleanField(default=True)),
                ('wedstrijden', models.ManyToManyField(blank=True, to='Wedstrijden.CompetitieWedstrijd')),
                ('old', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Wedstrijden.wedstrijdenplan'))
            ],
            options={
                'verbose_name': 'Competitie Wedstrijden Plan',
                'verbose_name_plural': 'Competitie Wedstrijden Plannen',
            },
        ),
        migrations.RunPython(copy_plannen)
    ]

# end of file
