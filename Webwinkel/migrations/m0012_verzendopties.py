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
        ('Webwinkel', 'm0011_remove_bedragen'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='VerzendOptie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(default='?', max_length=100)),
                ('emballage_type', models.CharField(default='?', max_length=100)),
                ('emballage_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('emballage_gram', models.PositiveIntegerField(default=0)),
                ('afhandelen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('verzendkosten_type', models.CharField(default='?', max_length=100)),
                ('verzendkosten_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('max_gewicht_gram', models.PositiveIntegerField(default=0)),
                ('max_lang_1', models.PositiveIntegerField(default=0)),
                ('max_lang_2', models.PositiveIntegerField(default=0)),
                ('max_lang_3', models.PositiveIntegerField(default=0)),
                ('max_volume_cm3', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Verzend optie',
            },
        ),
        migrations.AddField(
            model_name='webwinkelproduct',
            name='lang_1',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='webwinkelproduct',
            name='lang_2',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='webwinkelproduct',
            name='lang_3',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='webwinkelproduct',
            name='volume_cm3',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='webwinkelproduct',
            name='type_verzendkosten',
            field=models.CharField(max_length=5,
                                   choices=[('pak', 'Pakketpost'), ('brief', 'Briefpost'),
                                            ('klein', 'Pakket 2kg'), ('groot', 'Pakket 10kg')], default='pak'),
        ),
    ]

# end of file
