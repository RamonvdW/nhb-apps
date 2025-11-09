# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def maak_functie_cs(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')
    functie_klas(rol='CS', beschrijving='Commissie Scheidsrechters').save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0119_squashed'),
        ('Sporter', 'm0031_squashed'),
        ('Wedstrijden', 'm0057_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='ScheidsBeschikbaarheid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField()),
                ('opgaaf', models.CharField(choices=[('?', 'Niet ingevuld'), ('J', 'Ja'), ('D', 'Onzeker'),
                                                     ('N', 'Nee')],
                                            default='?', max_length=1)),
                ('log', models.TextField(blank=True, default='')),
                ('scheids', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Wedstrijden.wedstrijd')),
                ('opmerking', models.CharField(blank=True, default='', max_length=100)),
            ],
            options={
                'verbose_name': 'Scheids beschikbaarheid',
                'verbose_name_plural': 'Scheids beschikbaarheid',
            },
        ),
        migrations.AddConstraint(
            model_name='scheidsbeschikbaarheid',
            constraint=models.UniqueConstraint(fields=('scheids', 'wedstrijd', 'datum'),
                                               name='Een per scheidsrechter en wedstrijd dag'),
        ),
        migrations.CreateModel(
            name='WedstrijdDagScheidsrechters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dag_offset', models.SmallIntegerField(default=0)),
                ('gekozen_hoofd_sr', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                       related_name='gekozen_hoofd_sr', to='Sporter.sporter')),
                ('gekozen_sr1', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='gekozen_sr1', to='Sporter.sporter')),
                ('gekozen_sr2', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='gekozen_sr2', to='Sporter.sporter')),
                ('gekozen_sr3', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='gekozen_sr3', to='Sporter.sporter')),
                ('gekozen_sr4', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='gekozen_sr4', to='Sporter.sporter')),
                ('gekozen_sr5', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='gekozen_sr5', to='Sporter.sporter')),
                ('gekozen_sr6', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='gekozen_sr6', to='Sporter.sporter')),
                ('gekozen_sr7', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='gekozen_sr7', to='Sporter.sporter')),
                ('gekozen_sr8', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='gekozen_sr8', to='Sporter.sporter')),
                ('gekozen_sr9', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='gekozen_sr9', to='Sporter.sporter')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Wedstrijden.wedstrijd')),
                ('notified_srs', models.ManyToManyField(related_name='notified_sr', to='Sporter.sporter')),
                ('notified_laatste', models.CharField(blank=True, default='', max_length=100)),
            ],
            options={
                'verbose_name': 'Wedstrijddag scheidsrechters',
                'verbose_name_plural': 'Wedstrijddag scheidsrechters',
            },
        ),
        migrations.CreateModel(
            name='MatchScheidsrechters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notified_laatste', models.CharField(blank=True, default='', max_length=100)),
                ('gekozen_hoofd_sr', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                       related_name='match_gekozen_hoofd_sr', to='Sporter.sporter')),
                ('gekozen_sr1', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='match_gekozen_sr1', to='Sporter.sporter')),
                ('gekozen_sr2', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='match_gekozen_sr2', to='Sporter.sporter')),
                ('match', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitiematch')),
                ('notified_srs', models.ManyToManyField(related_name='match_notified_sr', to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Match scheidsrechters',
                'verbose_name_plural': 'Match scheidsrechters',
            },
        ),
        migrations.CreateModel(
            name='ScheidsMutatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('mutatie', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('door', models.CharField(default='', max_length=50)),
                ('wedstrijd', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                                to='Wedstrijden.wedstrijd')),
                ('match', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                            to='Competitie.competitiematch')),
            ],
            options={
                'verbose_name': 'Scheids mutatie',
            },
        ),
        migrations.RunPython(maak_functie_cs),
    ]

# end of file
