# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Wedstrijden.definities import INSCHRIJVING_STATUS_AFGEMELD, INSCHRIJVING_STATUS_VERWIJDERD
import datetime


def zet_status_verwijderd(apps, _):

    klas = apps.get_model('Wedstrijden', 'WedstrijdInschrijving')

    for obj in klas.objects.filter(status=INSCHRIJVING_STATUS_AFGEMELD):            # pragma: no cover
        # analyseer de datums in de log: allemaal dezelfde = zelf verwijderd
        eerste_datum = None
        biggest_delta = 0
        for regel in obj.log.split('\n'):
            if regel.startswith('['):
                pos = regel.find(']')
                try:
                    datum = datetime.datetime.strptime(regel[:pos+1], "[%Y-%m-%d om %H:%M]")
                except ValueError:
                    pass
                else:
                    if eerste_datum:
                        diff = (datum - eerste_datum)
                        delta_minutes = diff.days * (24 * 3600) + diff.seconds
                        # print(eerste_datum, datum, delta_minutes)
                        biggest_delta = max(biggest_delta, delta_minutes)
                    else:
                        eerste_datum = datum
        # for
        biggest_delta /= 3600
        if biggest_delta < 73.0:     # 3*24=72 uur + maximaal 1 uur interval restart achtergrondtaak
            obj.status = INSCHRIJVING_STATUS_VERWIJDERD
            obj.save(update_fields=['status'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0051_begrenzing_wereld'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='wedstrijdinschrijving',
            name='status',
            field=models.CharField(choices=[('R', 'Reservering'), ('B', 'Besteld'), ('D', 'Definitief'), ('A', 'Afgemeld'), ('V', 'Verwijderd')], default='R', max_length=2),
        ),
        migrations.RunPython(zet_status_verwijderd, reverse_code=migrations.RunPython.noop),
    ]

# end of file
