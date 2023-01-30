# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Score', 'm0019_squashed'),
        ('Overig', 'm0011_squashed'),
        ('Sporter', 'm0019_erelid'),
        ('Competitie', 'm0078_squashed'),
        ('NhbStructuur', 'm0030_bondsbureau'),
    ]

    # migratie functies
    operations = [
        migrations.RenameModel(
            old_name='RegioCompetitieSchutterBoog',
            new_name='RegioCompetitieSporterBoog',
        ),
        migrations.AlterModelOptions(
            name='regiocompetitiesporterboog',
            options={'verbose_name': 'Regiocompetitie sporterboog',
                     'verbose_name_plural': 'Regiocompetitie sportersboog'},
        ),
        migrations.RenameField(
            model_name='regiocompetitieteam',
            old_name='gekoppelde_schutters',
            new_name='leden',
        ),
        migrations.RenameModel(
            old_name='KampioenschapSchutterBoog',
            new_name='KampioenschapSporterBoog',
        ),
        migrations.AlterModelOptions(
            name='kampioenschapsporterboog',
            options={'verbose_name': 'Kampioenschap sporterboog', 'verbose_name_plural': 'Kampioenschap sportersboog'},
        ),
        migrations.RenameField(
            model_name='kampioenschapteam',
            old_name='feitelijke_schutters',
            new_name='feitelijke_leden',
        ),
        migrations.RenameField(
            model_name='kampioenschapteam',
            old_name='gekoppelde_schutters',
            new_name='gekoppelde_leden',
        ),
        migrations.RenameField(
            model_name='kampioenschapteam',
            old_name='tijdelijke_schutters',
            new_name='tijdelijke_leden',
        ),
        migrations.AlterField(
            model_name='kampioenschapteam',
            name='feitelijke_leden',
            field=models.ManyToManyField(blank=True, related_name='kampioenschapteam_feitelijke_leden',
                                         to='Competitie.kampioenschapsporterboog'),
        ),
        migrations.AlterField(
            model_name='kampioenschapteam',
            name='gekoppelde_leden',
            field=models.ManyToManyField(blank=True, related_name='kampioenschapteam_gekoppelde_leden',
                                         to='Competitie.kampioenschapsporterboog'),
        ),
        migrations.AlterField(
            model_name='kampioenschapteam',
            name='tijdelijke_leden',
            field=models.ManyToManyField(blank=True, related_name='kampioenschapteam_tijdelijke_leden',
                                         to='Competitie.regiocompetitiesporterboog'),
        ),
        migrations.RemoveIndex(
            model_name='kampioenschapsporterboog',
            name='Competitie__gemidde_2899dc_idx',
        ),
        migrations.RemoveIndex(
            model_name='kampioenschapsporterboog',
            name='Competitie__volgord_791c3d_idx',
        ),
        migrations.RemoveIndex(
            model_name='kampioenschapsporterboog',
            name='Competitie__rank_2f6fbf_idx',
        ),
        migrations.RemoveIndex(
            model_name='kampioenschapsporterboog',
            name='Competitie__volgord_9cc75f_idx',
        ),
        migrations.RemoveIndex(
            model_name='regiocompetitiesporterboog',
            name='Competitie__aantal__1682db_idx',
        ),
        migrations.RemoveIndex(
            model_name='regiocompetitiesporterboog',
            name='Competitie__aantal__409f0d_idx',
        ),
        migrations.RemoveIndex(
            model_name='regiocompetitiesporterboog',
            name='Competitie__gemidde_83a773_idx',
        ),
        migrations.AddIndex(
            model_name='kampioenschapsporterboog',
            index=models.Index(fields=['-gemiddelde'], name='Competitie__gemidde_e5f73d_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapsporterboog',
            index=models.Index(fields=['volgorde'], name='Competitie__volgord_b01f18_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapsporterboog',
            index=models.Index(fields=['rank'], name='Competitie__rank_3b305c_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapsporterboog',
            index=models.Index(fields=['volgorde', '-gemiddelde'], name='Competitie__volgord_0ec600_idx'),
        ),
        migrations.AddIndex(
            model_name='regiocompetitiesporterboog',
            index=models.Index(fields=['aantal_scores'], name='Competitie__aantal__955e64_idx'),
        ),
        migrations.AddIndex(
            model_name='regiocompetitiesporterboog',
            index=models.Index(fields=['-gemiddelde'], name='Competitie__gemidde_1225ce_idx'),
        ),
        migrations.AddIndex(
            model_name='regiocompetitiesporterboog',
            index=models.Index(fields=['aantal_scores', 'deelcompetitie'], name='Competitie__aantal__abf0e4_idx'),
        ),
    ]

# end of file
