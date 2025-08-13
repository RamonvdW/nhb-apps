# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0032_email_blank'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Transactie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('unieke_code', models.CharField(max_length=32)),
                ('has_been_used', models.BooleanField(default=False)),
                ('log', models.TextField(default='')),
            ],
            options={
                'verbose_name': 'Transactie',
            },
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('creds', models.JSONField(default=dict)),
                ('has_failed', models.BooleanField(default=False)),
                ('log', models.TextField(default='')),
            ],
            options={
                'verbose_name': 'Token',
            },
        ),
        migrations.CreateModel(
            name='Bestand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('afstand', models.PositiveSmallIntegerField(default=0)),
                ('is_team', models.BooleanField(default=False)),
                ('is_bk', models.BooleanField(default=False)),
                ('fname', models.CharField(max_length=80)),
                ('file_id', models.CharField(default='', max_length=64)),
                ('log', models.TextField(default='')),
                ('sporters', models.ManyToManyField(to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Bestand',
                'verbose_name_plural': 'Bestanden',
            },
        ),
    ]

# end of file
