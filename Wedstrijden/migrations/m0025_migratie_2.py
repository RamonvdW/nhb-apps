# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def migreer_kalender(apps, _):
    """ Migreer de tabellen uit Kalender naar Wedstrijden

        Maak voor elke record een nieuwe aan en verwijs van oud naar nieuw
        Relaties volgens later
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    if apps:                # pragma: no branch
        deeluitslag_oud_klas = apps.get_model('Kalender', 'KalenderWedstrijdDeeluitslag')
        if deeluitslag_oud_klas.objects.count() > 0:            # pragma: no cover
            raise ValueError('Onverwachte aanwezigheid van KalenderWedstrijdDeeluitslag')

    # sessies
    sessie_oud2new = dict()  # [oud.pk] = new
    if apps:                # pragma: no branch
        sessie_oud_klas = apps.get_model('Kalender', 'KalenderWedstrijdSessie')
        sessie_new_klas = apps.get_model('Wedstrijden', 'WedstrijdSessie')

        bulk = list()
        for obj in sessie_oud_klas.objects.all():           # pragma: no cover
            sessie = sessie_new_klas(
                        datum=obj.datum,
                        tijd_begin=obj.tijd_begin,
                        tijd_einde=obj.tijd_einde,
                        # wedstrijdklassen
                        max_sporters=obj.max_sporters,
                        aantal_inschrijvingen=obj.aantal_inschrijvingen,
                        oud=obj)
            bulk.append(sessie)
        # for
        sessie_new_klas.objects.bulk_create(bulk)

        for obj in (sessie_new_klas
                    .objects
                    .select_related('oud')
                    .prefetch_related('oud__wedstrijdklassen')
                    .all()):                                # pragma: no cover
            oud = obj.oud
            sessie_oud2new[oud.pk] = obj

            obj.wedstrijdklassen.set(oud.wedstrijdklassen.all())
        # for

    # wedstrijden
    wedstrijd_oud2new = dict()  # [oud.pk] = new
    if apps:                # pragma: no branch
        pk2locatie = dict()     # [pk] = WedstrijdLocatie
        locatie_klas = apps.get_model('Wedstrijden', 'WedstrijdLocatie')
        for obj in locatie_klas.objects.all():                  # pragma: no cover
            pk2locatie[obj.pk] = obj
        # for

        wedstrijd_oud_klas = apps.get_model('Kalender', 'KalenderWedstrijd')
        wedstrijd_new_klas = apps.get_model('Wedstrijden', 'Wedstrijd')

        bulk = list()
        for obj in wedstrijd_oud_klas.objects.all():            # pragma: no cover
            wedstrijd = wedstrijd_new_klas(
                            titel=obj.titel,
                            status=obj.status,
                            datum_begin=obj.datum_begin,
                            datum_einde=obj.datum_einde,
                            locatie=pk2locatie[obj.locatie_pk],
                            begrenzing=obj.begrenzing,
                            organisatie=obj.organisatie,
                            discipline=obj.discipline,
                            wa_status=obj.wa_status,
                            organiserende_vereniging=obj.organiserende_vereniging,
                            contact_naam=obj.contact_naam,
                            contact_email=obj.contact_email,
                            contact_website=obj.contact_website,
                            contact_telefoon=obj.contact_telefoon,
                            voorwaarden_a_status_acceptatie=obj.voorwaarden_a_status_acceptatie,
                            voorwaarden_a_status_when=obj.voorwaarden_a_status_when,
                            voorwaarden_a_status_who=obj.voorwaarden_a_status_who,
                            extern_beheerd=obj.extern_beheerd,
                            # boogtypen
                            # wedstrijdklassen
                            aantal_banen=obj.aantal_banen,
                            minuten_voor_begin_sessie_aanwezig_zijn=obj.minuten_voor_begin_sessie_aanwezig_zijn,
                            scheidsrechters=obj.scheidsrechters,
                            bijzonderheden=obj.bijzonderheden,
                            prijs_euro_normaal=obj.prijs_euro_normaal,
                            prijs_euro_onder18=obj.prijs_euro_onder18,
                            # sessies
                            oud=obj)
            bulk.append(wedstrijd)
        # for
        wedstrijd_new_klas.objects.bulk_create(bulk)

        for obj in (wedstrijd_new_klas
                    .objects
                    .select_related('oud')
                    .prefetch_related('oud__boogtypen',
                                      'oud__wedstrijdklassen',
                                      'oud__sessies')
                    .all()):                                    # pragma: no cover

            oud = obj.oud
            wedstrijd_oud2new[oud.pk] = obj

            obj.boogtypen.set(oud.boogtypen.all())
            obj.wedstrijdklassen.set(oud.wedstrijdklassen.all())

            for sessie in oud.sessies.all():
                obj.sessies.add(sessie_oud2new[sessie.pk])
            # for
        # for

    # kortingen
    korting_oud2new = dict()        # [oud.pk] = new
    if apps:                # pragma: no branch
        korting_oud_klas = apps.get_model('Kalender', 'KalenderWedstrijdKortingscode')
        korting_new_klas = apps.get_model('Wedstrijden', 'WedstrijdKortingscode')

        bulk = list()
        for obj in korting_oud_klas.objects.all():           # pragma: no cover
            korting = korting_new_klas(
                            code=obj.code,
                            geldig_tot_en_met=obj.geldig_tot_en_met,
                            uitgegeven_door=obj.uitgegeven_door,
                            percentage=obj.percentage,
                            soort=obj.soort,
                            # voor_wedstrijden
                            voor_sporter=obj.voor_sporter,
                            voor_vereniging=obj.voor_vereniging,
                            # combi_basis_wedstrijd
                            oud=obj)
            bulk.append(korting)
        # for
        korting_new_klas.objects.bulk_create(bulk)

        for obj in korting_new_klas.objects.select_related('oud').all():        # pragma: no cover
            oud = obj.oud
            korting_oud2new[oud.pk] = obj
        # for

    if apps:                # pragma: no branch
        inschrijving_oud_klas = apps.get_model('Kalender', 'KalenderInschrijving')
        inschrijving_new_klas = apps.get_model('Wedstrijden', 'WedstrijdInschrijving')

        bulk = list()
        for obj in (inschrijving_oud_klas
                    .objects
                    .select_related('sessie',
                                    'wedstrijd',
                                    'gebruikte_code')
                    .all()):                                        # pragma: no cover

            inschrijving = inschrijving_new_klas(
                                wanneer=obj.wanneer,
                                status=obj.status,
                                # wedstrijd
                                # sessie
                                sporterboog=obj.sporterboog,
                                koper=obj.koper,
                                # gebruikte_code
                                ontvangen_euro=obj.ontvangen_euro,
                                retour_euro=obj.retour_euro,
                                oud=obj)

            if obj.sessie:
                inschrijving.sessie = sessie_oud2new[obj.sessie.pk]

            if obj.wedstrijd:
                inschrijving.wedstrijd = wedstrijd_oud2new[obj.wedstrijd.pk]

            if obj.gebruikte_code:
                inschrijving.gebruikte_code = korting_oud2new[obj.gebruikte_code.pk]

            bulk.append(inschrijving)
        # for
        inschrijving_new_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0013_migratie_1'),
        ('Wedstrijden', 'm0024_migratie_1'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(migreer_kalender),
    ]

# end of file
