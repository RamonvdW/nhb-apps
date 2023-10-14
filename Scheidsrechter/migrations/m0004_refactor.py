# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0028_scheids'),
        ('Scheidsrechter', 'm0003_constraints'),
        ('Wedstrijden', 'm0050_kwalificatiescores_log'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='WedstrijdDagScheidsrechters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dag_offset', models.SmallIntegerField(default=0)),
                ('gekozen_hoofd_sr', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_hoofd_sr', to='Sporter.sporter')),
                ('gekozen_sr1', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_sr1', to='Sporter.sporter')),
                ('gekozen_sr2', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_sr2', to='Sporter.sporter')),
                ('gekozen_sr3', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_sr3', to='Sporter.sporter')),
                ('gekozen_sr4', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_sr4', to='Sporter.sporter')),
                ('gekozen_sr5', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_sr5', to='Sporter.sporter')),
                ('gekozen_sr6', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_sr6', to='Sporter.sporter')),
                ('gekozen_sr7', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_sr7', to='Sporter.sporter')),
                ('gekozen_sr8', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_sr8', to='Sporter.sporter')),
                ('gekozen_sr9', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='gekozen_sr9', to='Sporter.sporter')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Wedstrijden.wedstrijd')),
            ],
            options={
                'verbose_name': 'Wedstrijddag scheidsrechters',
                'verbose_name_plural': 'Wedstrijddag scheidsrechters',
            },
        ),
        migrations.DeleteModel(
            name='WedstrijdDagScheids',
        ),
    ]

# end of file
