# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0024_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddIndex(
            model_name='boogtype',
            index=models.Index(fields=['afkorting'], name='BasisTypen__afkorti_0bf4b9_idx'),
        ),
        migrations.AddIndex(
            model_name='boogtype',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_81dcc1_idx'),
        ),
        migrations.AddIndex(
            model_name='teamtype',
            index=models.Index(fields=['afkorting'], name='BasisTypen__afkorti_6ad4da_idx'),
        ),
        migrations.AddIndex(
            model_name='teamtype',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_4984e4_idx'),
        ),
        migrations.AddIndex(
            model_name='indivwedstrijdklasse',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_8e5550_idx'),
        ),
        migrations.AddIndex(
            model_name='kalenderwedstrijdklasse',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_246cec_idx'),
        ),
        migrations.AddIndex(
            model_name='teamwedstrijdklasse',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_46891c_idx'),
        ),
    ]

# end of file
