# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0012_score_geen'),
    ]

    # migratie functies
    operations = [
        migrations.AddIndex(
            model_name='score',
            index=models.Index(fields=['afstand_meter'], name='Score_score_afstand_c4e380_idx'),
        ),
        migrations.AddIndex(
            model_name='score',
            index=models.Index(fields=['type'], name='Score_score_type_573ac6_idx'),
        ),
        migrations.AddIndex(
            model_name='scorehist',
            index=models.Index(fields=['when'], name='Score_score_when_9c19cd_idx'),
        ),
    ]

# end of file
