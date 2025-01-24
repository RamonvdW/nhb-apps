# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleiding', 'm0002_opleiding'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='opleidingdeelnemer',
            old_name='ontvangen_euro',
            new_name='bedrag_ontvangen',
        ),
        migrations.RemoveField(
            model_name='opleidingdeelnemer',
            name='retour_euro',
        ),
        migrations.AddField(
            model_name='opleidingdeelnemer',
            name='nummer',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='opleidingdeelnemer',
            name='status',
            field=models.CharField(choices=[('R', 'Reservering'), ('B', 'Besteld'), ('D', 'Definitief')],
                                   default='R', max_length=2),
        ),
        migrations.AddField(
            model_name='opleidingdeelnemer',
            name='log',
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name='OpleidingAfgemeld',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer_afgemeld', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('C', 'Geannuleerd'), ('A', 'Afgemeld')], max_length=2)),
                ('wanneer_aangemeld', models.DateTimeField(auto_now_add=True)),
                ('nummer', models.BigIntegerField(default=0)),
                ('bedrag_ontvangen', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('bedrag_retour', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('aanpassing_email', models.EmailField(blank=True, max_length=254)),
                ('aanpassing_telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('aanpassing_geboorteplaats', models.CharField(blank=True, default='', max_length=100)),
                ('log', models.TextField(blank=True)),
                ('koper', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                            to='Account.account')),
                ('opleiding', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Opleiding.opleiding')),
                ('sporter', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Opleiding afmelding',
                'verbose_name_plural': 'Opleiding afmeldingen',
            },
        ),
        migrations.RenameModel(
            old_name='OpleidingDeelnemer',
            new_name='OpleidingInschrijving',
        ),
        migrations.AlterModelOptions(
            name='opleidinginschrijving',
            options={'verbose_name': 'Opleiding inschrijving', 'verbose_name_plural': 'Opleiding inschrijvingen'},
        ),
    ]

# end of file
