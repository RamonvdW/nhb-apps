# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def copy_nhblid(apps, _):
    """ vul de Sporters tabel aan de hand van het NhbLid """

    # haal de klassen op die van toepassing zijn vóór de migratie
    old_klas = apps.get_model('NhbStructuur', 'NhbLid')
    new_klas = apps.get_model('Sporter', 'Sporter')

    bulk = list()
    for lid in (old_klas
                .objects
                .select_related('account',
                                'bij_vereniging')
                .all()):                        # pragma: no cover

        sporter = new_klas()
        sporter.lid_nr = lid.nhb_nr
        sporter.voornaam = lid.voornaam
        sporter.achternaam = lid.achternaam
        sporter.unaccented_naam = lid.unaccented_naam
        sporter.email = lid.email
        sporter.geboorte_datum = lid.geboorte_datum
        sporter.geslacht = lid.geslacht
        sporter.para_classificatie = lid.para_classificatie
        sporter.sinds_datum = lid.sinds_datum
        sporter.is_actief_lid = lid.is_actief_lid
        sporter.bij_vereniging = lid.bij_vereniging
        sporter.lid_tot_einde_jaar = lid.lid_tot_einde_jaar
        sporter.account = lid.account
        bulk.append(sporter)

        if len(bulk) > 500:
            new_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    if len(bulk):                               # pragma: no cover
        new_klas.objects.bulk_create(bulk)


def copy_voorkeuren(cache, apps):
    """ vul de SporterVoorkeuren tabel aan de hand van het SchutterVoorkeuren """

    # haal de klassen op die van toepassing zijn vóór de migratie
    old_klas = apps.get_model('Schutter', 'SchutterVoorkeuren')
    new_klas = apps.get_model('Sporter', 'SporterVoorkeuren')

    bulk = list()
    for obj in (old_klas
                .objects
                .select_related('nhblid')
                .all()):                        # pragma: no cover

        voorkeuren = new_klas()
        voorkeuren.sporter = cache[obj.nhblid.nhb_nr]
        voorkeuren.voorkeur_eigen_blazoen = obj.voorkeur_eigen_blazoen
        voorkeuren.voorkeur_meedoen_competitie = obj.voorkeur_meedoen_competitie
        voorkeuren.opmerking_para_sporter = obj.opmerking_para_sporter
        voorkeuren.voorkeur_discipline_25m1pijl = obj.voorkeur_discipline_25m1pijl
        voorkeuren.voorkeur_discipline_outdoor = obj.voorkeur_discipline_outdoor
        voorkeuren.voorkeur_discipline_indoor = obj.voorkeur_discipline_indoor
        voorkeuren.voorkeur_discipline_clout = obj.voorkeur_discipline_clout
        voorkeuren.voorkeur_discipline_veld = obj.voorkeur_discipline_veld
        voorkeuren.voorkeur_discipline_run = obj.voorkeur_discipline_run
        voorkeuren.voorkeur_discipline_3d = obj.voorkeur_discipline_3d
        bulk.append(voorkeuren)

        if len(bulk) > 500:
            new_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    if len(bulk):                               # pragma: no cover
        new_klas.objects.bulk_create(bulk)


def copy_bogen(cache, apps):
    """ vul de SporterBoog tabel aan de hand van het SchutterBoog """

    # haal de klassen op die van toepassing zijn vóór de migratie
    old_klas = apps.get_model('Schutter', 'SchutterBoog')
    new_klas = apps.get_model('Sporter', 'SporterBoog')

    bulk = list()
    for obj in (old_klas
                .objects
                .select_related('nhblid',
                                'boogtype')
                .exclude(nhblid=None)
                .all()):                        # pragma: no cover

        boog = new_klas()
        boog.sporter = cache[obj.nhblid.nhb_nr]
        boog.boogtype = obj.boogtype
        boog.heeft_interesse = obj.heeft_interesse
        boog.voor_wedstrijd = obj.voor_wedstrijd
        bulk.append(boog)

        if len(bulk) > 500:
            new_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    if len(bulk):                               # pragma: no cover
        new_klas.objects.bulk_create(bulk)


def copy_secretaris(cache, apps):
    """ vul de Secretaris tabel aan de hand van de NhbVereniging """

    # haal de klassen op die van toepassing zijn vóór de migratie
    ver_klas = apps.get_model('NhbStructuur', 'NhbVereniging')
    sec_klas = apps.get_model('Sporter', 'Secretaris')

    bulk = list()
    for obj in (ver_klas
                .objects
                .select_related('secretaris_lid')
                .all()):                        # pragma: no cover
        secretaris = sec_klas()
        if obj.secretaris_lid:
            secretaris.sporter = cache[obj.secretaris_lid.nhb_nr]
        secretaris.vereniging = obj
        bulk.append(secretaris)
    # for

    if len(bulk):                               # pragma: no cover
        sec_klas.objects.bulk_create(bulk)


def copy_speelsterkte(cache, apps):
    """ kopieer de data uit de Speelsterkte tabel """

    # haal de klassen op die van toepassing zijn vóór de migratie
    old_klas = apps.get_model('NhbStructuur', 'Speelsterkte')
    new_klas = apps.get_model('Sporter', 'Speelsterkte')

    bulk = list()
    for obj in (old_klas
                .objects
                .select_related('lid')
                .all()):                        # pragma: no cover
        speelsterkte = new_klas()
        speelsterkte.sporter = cache[obj.lid.nhb_nr]
        speelsterkte.datum = obj.datum
        speelsterkte.beschrijving = obj.beschrijving
        speelsterkte.discipline = obj.discipline
        speelsterkte.category = obj.category
        speelsterkte.volgorde = obj.volgorde
        bulk.append(speelsterkte)

        if len(bulk) > 500:
            new_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    if len(bulk):                               # pragma: no cover
        new_klas.objects.bulk_create(bulk)


def copy_rest(apps, _):

    sporter_klas = apps.get_model('Sporter', 'Sporter')

    cache = dict()  # [lid_nr] = Sporter
    for sporter in sporter_klas.objects.all():      # pragma: no cover
        cache[sporter.lid_nr] = sporter
    # for

    copy_voorkeuren(cache, apps)
    copy_bogen(cache, apps)
    copy_secretaris(cache, apps)
    copy_speelsterkte(cache, apps)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0001_initial'),
        ('Schutter', 'm0011_voorkeur_eigen_blazoen'),
        ('NhbStructuur', 'm0021_verwijder_rayon_geografisch_gebied')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(copy_nhblid),
        migrations.RunPython(copy_rest),
    ]


"""
    performance debug helper:

    from django.db import connection

        q_begin = len(connection.queries)

        # queries here

        print('queries: %s' % (len(connection.queries) - q_begin))
        for obj in connection.queries[q_begin:]:
            print('%10s %s' % (obj['time'], obj['sql'][:200]))
        # for
        sys.exit(1)

    test uitvoeren met settings.DEBUG=True anders wordt er niets bijgehouden
"""

# end of file
