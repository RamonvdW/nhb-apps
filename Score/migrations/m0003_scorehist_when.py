# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.utils import timezone
import datetime
import pytz


def zet_when(apps, _):
    """ Voor alle bestaande ScoreHist objecten,
        zet 'when' gebaseerd op 'datum' met als tijdstip 00:00:00
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    scorehist_klas = apps.get_model('Score', 'ScoreHist')

    for obj in scorehist_klas.objects.all():        # pragma: no cover
        # converteer 'datum' naar 'when'
        # defaults voor hour, minute, second, millisecond is 0
        obj.when = datetime.datetime(year=obj.datum.year,
                                     month=obj.datum.month,
                                     day=obj.datum.day,
                                     tzinfo=pytz.UTC)
        obj.save(update_fields=['when'])
    # for


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0002_add_is_ag'),
    ]

    now = timezone.now()

    # migratie functions
    operations = [
        migrations.AddField(
            model_name='scorehist',
            name='when',
            field=models.DateTimeField(auto_now_add=True, default=now),
            preserve_default=False,
        ),
        migrations.RunPython(zet_when),
    ]

# end of file
