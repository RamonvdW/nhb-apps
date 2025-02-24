# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from django.conf import settings
from django.db.models import Count
from Bestelling.definities import BESTELLING_STATUS_AFGEROND
from Bestelling.definities import (BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD,
                                   BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_OPLEIDING_AFGEMELD,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_AFGEMELD,
                                   BESTELLING_REGEL_CODE_WEBWINKEL,
                                   BESTELLING_REGEL_CODE_TRANSPORT,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
from Webwinkel.definities import (KEUZE_STATUS_RESERVERING_MANDJE, KEUZE_STATUS_BESTELD, KEUZE_STATUS_BACKOFFICE,
                                  KEUZE_STATUS_GEANNULEERD)
from Wedstrijden.definities import WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD
from Wedstrijden.models import beschrijf_korting
from decimal import Decimal


def update_mandjes(apps, prod2regels):
    """ converteer mandje.producten naar regels """

    mandje_klas = apps.get_model('Bestelling', 'BestellingMandje')

    for mandje in mandje_klas.objects.prefetch_related('producten'):
        regels = list()
        for product in mandje.producten.all():
            try:
                nwe_regels = prod2regels[product.pk]
            except KeyError:
                pass
            else:
                regels.extend(nwe_regels)
        # for

        if len(regels) > 0:
            mandje.regels.add(*regels)
    # for


def update_bestellingen(apps, prod2regels):
    """ converteer bestelling.producten naar regels """

    bestelling_klas = apps.get_model('Bestelling', 'Bestelling')

    for bestelling in bestelling_klas.objects.prefetch_related('producten'):
        regels = list()
        for product in bestelling.producten.all():
            try:
                nwe_regels = prod2regels[product.pk]
            except KeyError:
                pass
            else:
                regels.extend(nwe_regels)
        # for

        if len(regels) > 0:
            bestelling.regels.add(*regels)
    # for


def migrate_product2regel_evenement(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    bestelling_product_klas = apps.get_model('Bestelling', 'BestellingProduct')
    bestelling_regel_klas = apps.get_model('Bestelling', 'BestellingRegel')

    print(' evenementen: ', end='')

    prod2regels = dict()        # [product.pk] = [regel, ..]

    # inschrijvingen
    for prod in (bestelling_product_klas
                 .objects
                 .exclude(evenement_inschrijving=None)
                 .select_related('evenement_inschrijving',
                                 'evenement_inschrijving__evenement',
                                 'evenement_inschrijving__sporter')):

        inschrijving = prod.evenement_inschrijving

        kort = inschrijving.evenement.titel
        if len(kort) > 40:
            kort = kort[:40] + '..'
        kort = "%s, voor %s" % (kort, inschrijving.sporter.lid_nr)

        regel = bestelling_regel_klas(
                    korte_beschrijving=kort,
                    bedrag_euro=prod.prijs_euro,
                    code=BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING)
        regel.save()
        prod2regels[prod.pk] = [regel]

        inschrijving.bestelling = regel
        inschrijving.save(update_fields=['bestelling'])
    # for

    # afgemeld
    for prod in (bestelling_product_klas
                 .objects
                 .exclude(evenement_afgemeld=None)
                 .select_related('evenement_afgemeld',
                                 'evenement_afgemeld__evenement',
                                 'evenement_afgemeld__sporter')):

        afgemeld = prod.evenement_afgemeld

        kort = afgemeld.evenement.titel
        if len(kort) > 40:
            kort = kort[:40] + '..'
        kort = "%s, voor %s" % (kort, afgemeld.sporter.lid_nr)

        regel = bestelling_regel_klas(
                    korte_beschrijving=kort,
                    bedrag_euro=prod.prijs_euro,
                    code=BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD)
        regel.save()
        prod2regels[prod.pk] = [regel]

        afgemeld.bestelling = regel
        afgemeld.save(update_fields=['bestelling'])
    # for

    print('%d' % len(prod2regels), end='')

    update_mandjes(apps, prod2regels)
    update_bestellingen(apps, prod2regels)


def migrate_product2regel_opleiding(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    bestelling_product_klas = apps.get_model('Bestelling', 'BestellingProduct')
    bestelling_regel_klas = apps.get_model('Bestelling', 'BestellingRegel')

    print(', opleidingen: ', end='')

    prod2regels = dict()    # [product.pk] = [regel ..]

    # inschrijving
    for prod in (bestelling_product_klas
                 .objects
                 .exclude(opleiding_inschrijving=None)
                 .select_related('opleiding_inschrijving',
                                 'opleiding_inschrijving__opleiding',
                                 'opleiding_inschrijving__sporter')):

        inschrijving = prod.opleiding_inschrijving

        kort = inschrijving.opleiding.titel
        if len(kort) > 40:
            kort = kort[:40] + '..'
        kort = "%s, voor %s" % (kort, inschrijving.sporter.lid_nr)

        regel = bestelling_regel_klas(
                    korte_beschrijving=kort,
                    bedrag_euro=prod.prijs_euro,
                    code=BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING)
        regel.save()

        prod2regels[prod.pk] = [regel]

        inschrijving.bestelling = regel
        inschrijving.save(update_fields=['bestelling'])
    # for

    # afgemeld
    for prod in (bestelling_product_klas
                 .objects
                 .exclude(opleiding_afgemeld=None)
                 .select_related('opleiding_afgemeld',
                                 'opleiding_afgemeld__opleiding',
                                 'opleiding_afgemeld__sporter')):

        afgemeld = prod.opleiding_afgemeld

        kort = afgemeld.opleiding.titel
        if len(kort) > 40:
            kort = kort[:40] + '..'
        kort = "%s, voor %s" % (kort, afgemeld.sporter.lid_nr)

        regel = bestelling_regel_klas(
                    korte_beschrijving=kort,
                    bedrag_euro=prod.prijs_euro,
                    code=BESTELLING_REGEL_CODE_OPLEIDING_AFGEMELD)

        regel.save()

        prod2regels[prod.pk] = [regel]

        afgemeld.bestelling = regel
        afgemeld.save(update_fields=['bestelling'])
    # for

    print('%d' % len(prod2regels), end='')

    update_mandjes(apps, prod2regels)
    update_bestellingen(apps, prod2regels)


def migrate_product2regel_webwinkel(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    bestelling_product_klas = apps.get_model('Bestelling', 'BestellingProduct')
    bestelling_regel_klas = apps.get_model('Bestelling', 'BestellingRegel')

    print(', webwinkel: ', end='')

    prod2regels = dict()    # [product.pk] = [regel, ..]

    for prod in (bestelling_product_klas
                 .objects
                 .exclude(webwinkel_keuze=None)
                 .annotate(mandje_count=Count('bestellingmandje'))
                 .annotate(bestelling_count=Count('bestelling'))
                 .select_related('webwinkel_keuze',
                                 'webwinkel_keuze__product')):

        keuze = prod.webwinkel_keuze

        # WebwinkelKeuze.status correct zetten
        if keuze.status == KEUZE_STATUS_RESERVERING_MANDJE:
            if prod.mandje_count == 0:
                if prod.bestelling_count == 0:
                    keuze.status = KEUZE_STATUS_GEANNULEERD
                elif prod.bestelling_count == 1:
                    bestelling = prod.bestelling_set.first()
                    keuze.status = KEUZE_STATUS_BESTELD
                    if bestelling.status == BESTELLING_STATUS_AFGEROND:
                        keuze.status = KEUZE_STATUS_BACKOFFICE
                keuze.save(update_fields=['status'])

        product = keuze.product
        kort = "%s x %s" % (keuze.aantal, product.omslag_titel)
        if product.kleding_maat:
            kort += ' maat %s' % product.kleding_maat

        prijs_euro = keuze.aantal * product.prijs_euro

        btw_str = "%.2f" % settings.WEBWINKEL_BTW_PERCENTAGE
        while btw_str[-1] == '0':
            btw_str = btw_str[:-1]              # 21,10 --> 21,1 / 21,00 --> 21,
        btw_str = btw_str.replace('.', ',')     # localize
        if btw_str[-1] == ",":
            btw_str = btw_str[:-1]              # drop the trailing dot/comma

        # de prijs is inclusief BTW, dus 100% + BTW% (voorbeeld: 121%)
        # reken uit hoeveel daarvan de BTW is (voorbeeld: 21 / 121)
        btw_deel = Decimal(settings.WEBWINKEL_BTW_PERCENTAGE / (100 + settings.WEBWINKEL_BTW_PERCENTAGE))
        btw_euro = prijs_euro * btw_deel
        btw_euro = round(btw_euro, 2)             # afronden op 2 decimalen

        regel = bestelling_regel_klas(
                    korte_beschrijving=kort,
                    bedrag_euro=prijs_euro,
                    btw_percentage=btw_str,
                    btw_euro=btw_euro,
                    gewicht_gram=product.gewicht_gram * keuze.aantal,
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        prod2regels[prod.pk] = [regel]

        keuze.bestelling = regel
        keuze.save(update_fields=['bestelling'])
    # for

    print('%d' % len(prod2regels), end='')

    update_mandjes(apps, prod2regels)
    update_bestellingen(apps, prod2regels)


def migrate_product2regel_wedstrijd(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    bestelling_product_klas = apps.get_model('Bestelling', 'BestellingProduct')
    bestelling_regel_klas = apps.get_model('Bestelling', 'BestellingRegel')

    print(', wedstrijden: ', end='')

    prod2regels = dict()        # [product.pk] = [regel, ..]

    # inschrijving
    bulk = list()
    for prod in (bestelling_product_klas
                 .objects
                 .exclude(wedstrijd_inschrijving=None)
                 .select_related('wedstrijd_inschrijving',
                                 'wedstrijd_inschrijving__korting',
                                 'wedstrijd_inschrijving__wedstrijd',
                                 'wedstrijd_inschrijving__sporterboog__sporter')):

        inschrijving = prod.wedstrijd_inschrijving

        kort = inschrijving.wedstrijd.titel
        if len(kort) > 60:
            kort = kort[:58] + '..'
        kort = "%s - %s" % (inschrijving.sporterboog.sporter.lid_nr, kort)

        regel = bestelling_regel_klas(
                    korte_beschrijving=kort,
                    bedrag_euro=prod.prijs_euro,
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD_INSCHRIJVING)

        if inschrijving.status == WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD:
            regel.code = BESTELLING_REGEL_CODE_WEDSTRIJD_AFGEMELD

        regel.save()
        prod2regels[prod.pk] = [regel]

        inschrijving.bestelling = regel
        inschrijving.save(update_fields=['bestelling'])

        # alleen wedstrijden hebben kortingen
        korting = inschrijving.korting
        if korting:
            kort, redenen = beschrijf_korting(korting)
            regel = bestelling_regel_klas(
                        korte_beschrijving=kort,
                        bedrag_euro=0 - prod.korting_euro,
                        code=BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
            if len(redenen):
                regel.korting_redenen = "||".join(redenen)
            regel.save()
            prod2regels[prod.pk].append(regel)
    # for

    print('%d..' % len(prod2regels), end='')

    update_mandjes(apps, prod2regels)
    update_bestellingen(apps, prod2regels)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0005_regel'),
        ('Evenement', 'm0003_bestelling'),
        ('Opleiding', 'm0008_bestelling'),
        ('Webwinkel', 'm0010_bestelling'),
        ('Wedstrijden', 'm0060_bestelling')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(migrate_product2regel_evenement),
        migrations.RunPython(migrate_product2regel_opleiding),
        migrations.RunPython(migrate_product2regel_webwinkel),
        migrations.RunPython(migrate_product2regel_wedstrijd),  # , migrations.RunPython.noop
    ]

# end of file
