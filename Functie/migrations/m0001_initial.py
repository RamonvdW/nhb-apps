# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    initial = True
    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        ('NhbStructuur', 'm0003_nhbstructuur_2019'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Functie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=50)),
                ('rol', models.CharField(max_length=5)),
                ('comp_type', models.CharField(max_length=2)),
                ('nhb_rayon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRayon')),
                ('nhb_regio', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRegio')),
                ('nhb_ver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbVereniging')),
            ],
        ),
    ]

# end of file
