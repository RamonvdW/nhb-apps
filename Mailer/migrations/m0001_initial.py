# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie classs voor dit deel van de applicatie """

    # volgorde afdwingen
    initial = True
    dependencies = [
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='MailQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('toegevoegd_op', models.DateTimeField()),
                ('is_verstuurd', models.BooleanField()),
                ('laatste_poging', models.DateTimeField()),
                ('aantal_pogingen', models.PositiveSmallIntegerField()),
                ('mail_to', models.CharField(max_length=150)),
                ('mail_subj', models.CharField(max_length=100)),
                ('mail_date', models.CharField(max_length=60)),
                ('mail_text', models.TextField()),
                ('log', models.TextField()),
            ],
            options={
                'verbose_name': 'Mail queue',
                'verbose_name_plural': 'Mail queue',
            },
        ),
    ]

# end of file
