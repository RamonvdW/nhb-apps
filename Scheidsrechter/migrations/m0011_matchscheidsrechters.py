# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0113_squashed'),
        ('Scheidsrechter', 'm0010_scheidsmutatie_match'),
        ('Sporter', 'm0031_squashed'),
    ]

    # migratie functies
    operations = [
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
    ]

# end of file
