# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def do_rename(apps, _):

    klas = apps.get_model('Logboek', 'LogboekRegel')
    klas.objects.filter(gebruikte_functie='NhbStructuur').update(gebruikte_functie='CRM-import')

    klas.objects.filter(activiteit__contains="Automatische inlog").update(gebruikte_functie='Inloggen (code)')


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Logboek', 'm0004_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(do_rename, reverse_code=migrations.RunPython.noop)
    ]


# end of file
