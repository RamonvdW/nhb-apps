# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from decimal import Decimal


def update_mandjes(apps, prod2regel):
    """ converteer mandje.producten naar regels """

    mandje_klas = apps.get_model('Bestelling', 'BestellingMandje')

    for mandje in mandje_klas.objects.prefetch_related('producten'):
        regels = list()
        for product in mandje.producten.all():
            try:
                regel = prod2regel[product.pk]
            except KeyError:
                pass
            else:
                regels.append(regel)
        # for

        if len(regels) > 0:
            mandje.regels.add(*regels)
    # for


def update_bestellingen(apps, prod2regel):
    """ converteer bestelling.producten naar regels """

    bestelling_klas = apps.get_model('Bestelling', 'Bestelling')

    for bestelling in bestelling_klas.objects.prefetch_related('producten'):
        regels = list()
        for product in bestelling.producten.all():
            try:
                regel = prod2regel[product.pk]
            except KeyError:
                pass
            else:
                regels.append(regel)
        # for

        if len(regels) > 0:
            bestelling.regels.add(*regels)
    # for


def migrate_product2regel_evenement(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    bestelling_product_klas = apps.get_model('Bestelling', 'BestellingProduct')
    bestelling_regel_klas = apps.get_model('Bestelling', 'BestellingRegel')

    prod2regel = dict()

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
                    btw_percentage='',
                    btw_euro=Decimal(0),
                    prijs_euro=prod.prijs_euro,
                    korting_euro=prod.korting_euro,
                    code="evenement")
        regel.save()

        prod2regel[prod.pk] = regel

        inschrijving.bestelling = regel
        inschrijving.save(update_fields=['bestelling'])
    # for

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
                    btw_percentage='',
                    btw_euro=Decimal(0),
                    prijs_euro=prod.prijs_euro,
                    korting_euro=prod.korting_euro,
                    code="evenement")

        regel.save()

        prod2regel[prod.pk] = regel

        afgemeld.bestelling = regel
        afgemeld.save(update_fields=['bestelling'])
    # for

    print(' %d evenementen' % len(prod2regel), end='')

    update_mandjes(apps, prod2regel)
    update_bestellingen(apps, prod2regel)


def migrate_product2regel_opleiding(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    bestelling_product_klas = apps.get_model('Bestelling', 'BestellingProduct')
    bestelling_regel_klas = apps.get_model('Bestelling', 'BestellingRegel')

    prod2regel = dict()

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
                    btw_percentage='',
                    btw_euro=Decimal(0),
                    prijs_euro=prod.prijs_euro,
                    korting_euro=prod.korting_euro,
                    code="opleiding")
        regel.save()

        prod2regel[prod.pk] = regel

        inschrijving.bestelling = regel
        inschrijving.save(update_fields=['bestelling'])
    # for

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
                    btw_percentage='',
                    prijs_euro=prod.prijs_euro,
                    korting_euro=prod.korting_euro,
                    btw_euro=Decimal(0),
                    code="opleiding")

        regel.save()

        prod2regel[prod.pk] = regel

        afgemeld.bestelling = regel
        afgemeld.save(update_fields=['bestelling'])
    # for

    print(', %d opleidingen' % len(prod2regel), end='')

    update_mandjes(apps, prod2regel)
    update_bestellingen(apps, prod2regel)


def migrate_product2regel_webwinkel(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    bestelling_product_klas = apps.get_model('Bestelling', 'BestellingProduct')
    bestelling_regel_klas = apps.get_model('Bestelling', 'BestellingRegel')

    prod2regel = dict()

    for prod in (bestelling_product_klas
                 .objects
                 .exclude(webwinkel_keuze=None)
                 .select_related('webwinkel_keuze',
                                 'webwinkel_keuze__product')):

        keuze = prod.webwinkel_keuze

        kort = "%s x %s" % (keuze.aantal, keuze.product.omslag_titel)

        regel = bestelling_regel_klas(
                    korte_beschrijving=kort,
                    btw_percentage='',                  # TODO: juiste percentage overnemen (uit de Bestelling)
                    btw_euro=Decimal(0),                # TODO: juiste bedrag invullen (uit de Bestelling)
                    prijs_euro=prod.prijs_euro,
                    korting_euro=Decimal(0),
                    code="webwinkel")
        regel.save()

        prod2regel[prod.pk] = regel

        keuze.bestelling = regel
        keuze.save(update_fields=['bestelling'])
    # for

    print(', %d webwinkel' % len(prod2regel), end='')

    update_mandjes(apps, prod2regel)
    update_bestellingen(apps, prod2regel)


def migrate_product2regel_wedstrijd(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    bestelling_product_klas = apps.get_model('Bestelling', 'BestellingProduct')
    bestelling_regel_klas = apps.get_model('Bestelling', 'BestellingRegel')

    prod2regel = dict()

    for prod in (bestelling_product_klas
                 .objects
                 .exclude(wedstrijd_inschrijving=None)
                 .select_related('wedstrijd_inschrijving',
                                 'wedstrijd_inschrijving__wedstrijd',
                                 'wedstrijd_inschrijving__sporterboog__sporter')):

        inschrijving = prod.wedstrijd_inschrijving

        kort = inschrijving.wedstrijd.titel
        if len(kort) > 60:
            kort = kort[:58] + '..'
        kort = "%s - %s" % (inschrijving.sporterboog.sporter.lid_nr, kort)

        regel = bestelling_regel_klas(
                    korte_beschrijving=kort,
                    btw_percentage='',
                    btw_euro=Decimal(0),
                    prijs_euro=prod.prijs_euro,
                    korting_euro=prod.korting_euro,
                    code="wedstrijd")
        regel.save()

        prod2regel[prod.pk] = regel

        inschrijving.bestelling = regel
        inschrijving.save(update_fields=['bestelling'])
    # for

    print(', %d wedstrijden..' % len(prod2regel), end='')

    update_mandjes(apps, prod2regel)
    update_bestellingen(apps, prod2regel)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0005_regel'),
        ('Evenement', 'm0003_bestelling'),
        ('Opleiding', 'm0007_bestelling'),
        ('Webwinkel', 'm0010_bestelling'),
        ('Wedstrijden', 'm0059_bestelling')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(migrate_product2regel_evenement),
        migrations.RunPython(migrate_product2regel_opleiding),
        migrations.RunPython(migrate_product2regel_webwinkel),
        migrations.RunPython(migrate_product2regel_wedstrijd),  # , migrations.RunPython.noop
    ]

# end of file
