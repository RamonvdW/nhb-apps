# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0031_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Vraag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_actief', models.BooleanField(default=True)),
                ('gebruik_voor_toets', models.BooleanField(default=True)),
                ('gebruik_voor_quiz', models.BooleanField(default=False)),
                ('vraag_tekst', models.TextField(blank=True)),
                ('antwoord_a', models.TextField(blank=True)),
                ('antwoord_b', models.TextField(blank=True)),
                ('antwoord_c', models.TextField(blank=True)),
                ('antwoord_d', models.TextField(blank=True)),
                ('juiste_antwoord', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
                                                     default='A', max_length=1)),
                ('logboek', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Vraag',
                'verbose_name_plural': 'Vragen',
            },
        ),
        migrations.CreateModel(
            name='VoorstelVraag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aangemaakt', models.DateTimeField(auto_now_add=True)),
                ('vraag_tekst', models.TextField(blank=True)),
                ('antwoord_a', models.TextField(blank=True)),
                ('antwoord_b', models.TextField(blank=True)),
                ('antwoord_c', models.TextField(blank=True)),
                ('antwoord_d', models.TextField(blank=True)),
                ('juiste_antwoord', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
                                                     default='A', max_length=1)),
                ('logboek', models.TextField(blank=True)),
                ('ingediend_door', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'VoorstelVraag',
                'verbose_name_plural': 'VoorstelVragen',
            },
        ),
        migrations.CreateModel(
            name='Uitdaging',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tonen_vanaf', models.DateField(default='2000-01-01')),
                ('vraag', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Instaptoets.vraag')),
            ],
            options={
                'verbose_name': 'Uitdaging',
                'verbose_name_plural': 'Uitdagingen',
            },
        ),
        migrations.CreateModel(
            name='ToetsAntwoord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('antwoord', models.CharField(default='?', max_length=1)),
                ('vraag', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Instaptoets.vraag')),
            ],
            options={
                'verbose_name': 'Antwoord',
                'verbose_name_plural': 'Antwoorden',
            },
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opgestart', models.DateTimeField(auto_now_add=True)),
                ('aantal_vragen', models.PositiveSmallIntegerField(default=0)),
                ('aantal_antwoorden', models.PositiveSmallIntegerField(default=0)),
                ('sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
                ('vraag_antwoord', models.ManyToManyField(blank=True, to='Instaptoets.toetsantwoord')),
                ('huidige_vraag', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL,
                                                    related_name='quiz_huidige', to='Instaptoets.toetsantwoord')),
            ],
            options={
                'verbose_name': 'Quiz',
                'verbose_name_plural': 'Quizzen',
            },
        ),
        migrations.CreateModel(
            name='Instaptoets',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opgestart', models.DateTimeField(auto_now_add=True)),
                ('afgerond', models.DateTimeField(default=datetime.datetime(9999, 12, 31, 0, 0,
                                                                            tzinfo=datetime.timezone.utc))),
                ('aantal_vragen', models.PositiveSmallIntegerField(default=0)),
                ('aantal_antwoorden', models.PositiveSmallIntegerField(default=0)),
                ('sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
                ('vraag_antwoord', models.ManyToManyField(blank=True, to='Instaptoets.toetsantwoord')),
                ('huidige_vraag', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL,
                                                    related_name='toets_huidige', to='Instaptoets.toetsantwoord')),
                ('is_afgerond', models.BooleanField(default=False)),
                ('aantal_goed', models.PositiveSmallIntegerField(default=0)),
                ('geslaagd', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Instaptoets',
                'verbose_name_plural': 'Instaptoetsen',
            },
        ),
    ]

# end of file
