# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def buiten_naar_extern(apps, _):
    """ Zet een buitenlocatie met afwijkend adres van de binnenlocatie om naar een externe locatie """

    klas_wedstrijdlocatie = apps.get_model('Wedstrijden', 'WedstrijdLocatie')
    klas_nhbvereniging = apps.get_model('NhbStructuur', 'NhbVereniging')

    # bepaal alle verenigingen met een buitenlocatie
    ver_pks = list()
    for loc in (klas_wedstrijdlocatie
                .objects
                .prefetch_related('verenigingen')
                .filter(baan_type='B')):

        for ver in loc.verenigingen.all():
            ver_pks.append(ver.pk)
        # for
    # for

    for ver in klas_nhbvereniging.objects.filter(pk__in=ver_pks):

        buiten_locatie = ver.wedstrijdlocatie_set.get(baan_type='B')

        if buiten_locatie.adres == '':
            # geen adres --> zelfde als binnen locatie, dus zo laten
            continue

        binnen_locatie = ver.wedstrijdlocatie_set.get(adres_uit_crm=True)

        adres1 = binnen_locatie.adres.replace('\n', ' ').replace(',', ' ').replace(' ', '')
        adres2 = buiten_locatie.adres.replace('\r\n', ' ').replace('\n', ' ').replace(',', ' ').replace(' ', '')

        if adres1 == adres2 or adres1.startswith(adres2):
            # zelfde adres, dus zo laten
            continue

        # adres van buiten accommodatie verschilt van binnen accommodatie
        # verander deze in een externe locatie
        buiten_locatie.baan_type = 'E'
        buiten_locatie.save(update_fields=['baan_type'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0016_plaats'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(buiten_naar_extern)
    ]

# end of file
