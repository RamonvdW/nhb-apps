# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('Bestelling', 'm0014_rename'),
        ('Spelden', 'm0010_aanvraagprep_wedstrijd'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='speldaanvraag',
            name='bestelling_regel',
        ),
        migrations.RemoveField(
            model_name='speldaanvraag',
            name='door_account',
        ),
        migrations.RemoveField(
            model_name='speldaanvraag',
            name='log',
        ),
        migrations.RemoveField(
            model_name='speldaanvraag',
            name='speld',
        ),
        migrations.CreateModel(
            name='SpeldBestelling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aangemaakt_op', models.DateField(auto_now_add=True)),
                ('is_nieuwe_aanvraag', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('M', 'Reservering'), ('B', 'Besteld'), ('BO', 'Betaald'),
                                                     ('A', 'Geannuleerd')],
                                            default='M', max_length=2)),
                ('aanvraag', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Spelden.speldaanvraag')),
                ('bestelling_regel', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Bestelling.bestellingregel')),
                ('door_account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
                ('speld', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Spelden.speld')),
                ('log', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Speld bestelling',
                'verbose_name_plural': 'Speld bestellingen',
            },
        ),
    ]

 # end of file
