# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion

def maak_taken(apps, _):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    taken_klas = apps.get_model('Competitie', 'CompetitieTaken')

    taken = taken_klas()
    taken.save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0004_remove_scorehist_datum'),
        ('Competitie', 'm0011_langere_ronde_beschrijving'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='CompetitieTaken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hoogste_scorehist',
                 models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                   to='Score.ScoreHist')),
            ],
        ),
        migrations.RunPython(maak_taken),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='scores',
            field=models.ManyToManyField(blank=True, to='Score.Score'),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_gemiddelde',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_laagste_score_nr',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_score1',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_score2',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_score3',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_score4',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_score5',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_score6',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_score7',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_totaal',
            field=models.PositiveIntegerField(default=0),
        ),
    ]

# end of file
