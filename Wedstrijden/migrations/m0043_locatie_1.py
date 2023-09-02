# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def kopieer_wedstrijd_locaties(apps, _):
    oud_klas = apps.get_model('Wedstrijden', 'WedstrijdLocatie')
    new_klas = apps.get_model('Locatie', 'Locatie')

    # TODO: controleer of locatie gebruikt wordt. Zo niet, dan verwijderen

    for loc_oud in oud_klas.objects.prefetch_related('verenigingen').all():
        loc_new = new_klas(
                        naam=loc_oud.naam,
                        zichtbaar=loc_oud.zichtbaar,
                        baan_type=loc_oud.baan_type,
                        discipline_25m1pijl=loc_oud.discipline_25m1pijl,
                        discipline_outdoor=loc_oud.discipline_outdoor,
                        discipline_indoor=loc_oud.discipline_indoor,
                        discipline_clout=loc_oud.discipline_clout,
                        discipline_veld=loc_oud.discipline_veld,
                        discipline_run=loc_oud.discipline_run,
                        discipline_3d=loc_oud.discipline_3d,
                        banen_18m=loc_oud.banen_18m,
                        banen_25m=loc_oud.banen_25m,
                        max_sporters_18m=loc_oud.max_sporters_18m,
                        max_sporters_25m=loc_oud.max_sporters_25m,
                        buiten_banen=loc_oud.buiten_banen,
                        buiten_max_afstand=loc_oud.buiten_max_afstand,
                        adres=loc_oud.adres,
                        plaats=loc_oud.plaats,
                        adres_uit_crm=loc_oud.adres_uit_crm,
                        notities=loc_oud.notities)
        loc_new.save()
        loc_new.verenigingen.set(loc_oud.verenigingen.all())

        loc_oud.locatie_new = loc_new
        loc_oud.save(update_fields=['locatie_new'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0042_vereniging_2'),
        ('Locatie', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='locatie_new',
            field=models.OneToOneField(null=True, on_delete=models.deletion.PROTECT, to='Locatie.locatie'),
        ),
        migrations.RunPython(kopieer_wedstrijd_locaties, migrations.RunPython.noop),
    ]

# end of file
