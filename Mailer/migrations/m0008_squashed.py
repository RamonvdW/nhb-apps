# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = []

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='MailQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('toegevoegd_op', models.DateTimeField()),
                ('is_verstuurd', models.BooleanField(default=False)),
                ('laatste_poging', models.DateTimeField()),
                ('aantal_pogingen', models.PositiveSmallIntegerField(default=0)),
                ('mail_to', models.CharField(max_length=150)),
                ('mail_subj', models.CharField(max_length=100)),
                ('mail_date', models.CharField(max_length=60)),
                ('mail_text', models.TextField()),
                ('log', models.TextField(blank=True)),
                ('is_blocked', models.BooleanField(default=False)),
                ('mail_html', models.TextField(default='')),
                ('template_used', models.CharField(default='', max_length=100)),
            ],
            options={
                'verbose_name': 'Mail queue',
                'verbose_name_plural': 'Mail queue',
            },
        ),
    ]

# end of file
