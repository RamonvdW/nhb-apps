# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0015_kalenderwedstrijdklasse'),
        ('Kalender', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='kalenderwedstrijd',
            name='unmanaged_url',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijdsessie',
            name='klassen',
        ),
        migrations.AddField(
            model_name='kalenderwedstrijd',
            name='extern_beheerd',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='kalenderwedstrijd',
            name='wedstrijdklassen',
            field=models.ManyToManyField(blank=True, to='BasisTypen.KalenderWedstrijdklasse'),
        ),
        migrations.AddField(
            model_name='kalenderwedstrijdsessie',
            name='wedstrijdklassen',
            field=models.ManyToManyField(blank=True, to='BasisTypen.KalenderWedstrijdklasse'),
        ),
        migrations.AlterField(
            model_name='kalenderwedstrijd',
            name='contact_email',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AlterField(
            model_name='kalenderwedstrijd',
            name='contact_naam',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='kalenderwedstrijd',
            name='contact_telefoon',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='kalenderwedstrijd',
            name='contact_website',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='kalenderwedstrijd',
            name='scheidsrechters',
            field=models.TextField(blank=True, default='', max_length=500),
        ),
        migrations.AlterField(
            model_name='kalenderwedstrijd',
            name='voorwaarden_a_status_who',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]

# end of file
