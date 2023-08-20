# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def add_vereniging_new(apps, _):
    """ migratie van veld vereniging """

    ver_klas = apps.get_model('Vereniging', 'Vereniging')
    fix_klas1 = apps.get_model('Competitie', 'RegiocompetitieSporterBoog')
    fix_klas2 = apps.get_model('Competitie', 'RegiocompetitieTeam')
    fix_klas3 = apps.get_model('Competitie', 'KampioenschapSporterBoog')
    fix_klas4 = apps.get_model('Competitie', 'KampioenschapTeam')
    fix_klas5 = apps.get_model('Competitie', 'CompetitieMatch')

    # maak een cache
    ver_nr2ver = dict()     # [ver_nr] = Vereniging()
    for ver in ver_klas.objects.all():
        ver_nr2ver[ver.ver_nr] = ver
    # for

    for obj in fix_klas1.objects.select_related('bij_vereniging').all():
        if obj.bij_vereniging:
            obj.bij_vereniging_new = ver_nr2ver[obj.bij_vereniging.ver_nr]
        obj.save(update_fields=['bij_vereniging_new'])
    # for

    for obj in fix_klas2.objects.select_related('vereniging').all():
        if obj.vereniging:
            obj.vereniging_new = ver_nr2ver[obj.vereniging.ver_nr]
        obj.save(update_fields=['vereniging_new'])
    # for

    for obj in fix_klas3.objects.select_related('bij_vereniging').all():
        if obj.bij_vereniging:
            obj.bij_vereniging_new = ver_nr2ver[obj.bij_vereniging.ver_nr]
        obj.save(update_fields=['bij_vereniging_new'])
    # for

    for obj in fix_klas4.objects.select_related('vereniging').all():
        if obj.vereniging:
            obj.vereniging_new = ver_nr2ver[obj.vereniging.ver_nr]
        obj.save(update_fields=['vereniging_new'])
    # for

    for obj in fix_klas5.objects.select_related('vereniging').all():
        if obj.vereniging:
            obj.vereniging_new = ver_nr2ver[obj.vereniging.ver_nr]
        obj.save(update_fields=['vereniging_new'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0002_vereniging_1'),
        ('Competitie', 'm0101_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitiesporterboog',
            name='bij_vereniging_new',
            field=models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging'),
        ),
        migrations.AddField(
            model_name='regiocompetitieteam',
            name='vereniging_new',
            field=models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging'),
        ),
        migrations.AddField(
            model_name='kampioenschapsporterboog',
            name='bij_vereniging_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging'),
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='vereniging_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging'),
        ),
        migrations.AddField(
            model_name='competitiematch',
            name='vereniging_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging'),
        ),
        migrations.RunPython(add_vereniging_new, migrations.RunPython.noop),
    ]

# end of file
