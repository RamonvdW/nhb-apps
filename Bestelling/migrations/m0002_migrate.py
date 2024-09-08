# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Bestel.definities import BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK
from Bestelling.definities import BESTELLING_HOOGSTE_BESTEL_NR_FIXED_PK


def migrate_from_bestel(apps, _):
    """ maak het enige record aan in deze tabel """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    hoogste_oud = apps.get_model('Bestel', 'BestelHoogsteBestelNr')
    hoogste_new = apps.get_model('Bestelling', 'BestellingHoogsteBestelNr')

    product_oud = apps.get_model('Bestel', 'BestelProduct')
    product_new = apps.get_model('Bestelling', 'BestellingProduct')

    mandje_oud = apps.get_model('Bestel', 'BestelMandje')
    mandje_new = apps.get_model('Bestelling', 'BestellingMandje')

    bestelling_oud = apps.get_model('Bestel', 'Bestelling2')
    bestelling_new = apps.get_model('Bestelling', 'Bestelling')

    mutatie_oud = apps.get_model('Bestel', 'BestelMutatie')
    mutatie_new = apps.get_model('Bestelling', 'BestellingMutatie')

    # maak het enige record aan met het hoogste gebruikte bestelnummer
    hoogste = hoogste_oud.objects.get(pk=BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK)
    hoogste_new(
            pk=BESTELLING_HOOGSTE_BESTEL_NR_FIXED_PK,
            hoogste_gebruikte_bestel_nr=hoogste.hoogste_gebruikte_bestel_nr).save()

    # producten van de bestellingen overzetten
    # (verwachting: 4000 records)
    print('P', end='')
    bestelproduct_pk2bestellingproduct = dict()     # [BestelProduct.pk] = BestellingProduct
    for product in (product_oud                     # pragma: no cover
                    .objects
                    .select_related('wedstrijd_inschrijving',
                                    'evenement_inschrijving',
                                    'evenement_afgemeld',
                                    'webwinkel_keuze')):
        obj = product_new(
                    wedstrijd_inschrijving=product.wedstrijd_inschrijving,
                    evenement_inschrijving=product.evenement_inschrijving,
                    evenement_afgemeld=product.evenement_afgemeld,
                    webwinkel_keuze=product.webwinkel_keuze,
                    prijs_euro=product.prijs_euro,
                    korting_euro=product.korting_euro)
        obj.save()

        bestelproduct_pk2bestellingproduct[product.pk] = obj.pk
    # for

    # mandje overzetten
    # (verwachting: enkele)
    print('M', end='')
    for mandje in (mandje_oud.objects               # pragma: no cover
                   .order_by('pk')
                   .prefetch_related('producten')
                   .select_related('account')):
        product_pks = list(mandje.producten.values_list('pk', flat=True))
        producten = [bestelproduct_pk2bestellingproduct[pk]
                     for pk in product_pks]

        obj = mandje_new(
                    account=mandje.account,
                    afleveradres_regel_1=mandje.afleveradres_regel_1,
                    afleveradres_regel_2=mandje.afleveradres_regel_2,
                    afleveradres_regel_3=mandje.afleveradres_regel_3,
                    afleveradres_regel_4=mandje.afleveradres_regel_4,
                    afleveradres_regel_5=mandje.afleveradres_regel_5,
                    transport=mandje.transport,
                    verzendkosten_euro=mandje.verzendkosten_euro,
                    btw_percentage_cat1=mandje.btw_percentage_cat1,
                    btw_percentage_cat2=mandje.btw_percentage_cat2,
                    btw_percentage_cat3=mandje.btw_percentage_cat3,
                    btw_euro_cat1=mandje.btw_euro_cat1,
                    btw_euro_cat2=mandje.btw_euro_cat2,
                    btw_euro_cat3=mandje.btw_euro_cat3,
                    totaal_euro=mandje.totaal_euro,
                    vorige_herinnering=mandje.vorige_herinnering)
        obj.save()
        obj.producten.set(producten)
    # for

    # bestellingen overnemen
    # (verwachting: 3000 records)
    print('B', end='')
    bestelling2_pk2bestelling = dict()      # [Bestelling2.pk] = Bestelling
    for bestelling in (bestelling_oud       # pragma: no cover
                       .objects
                       .prefetch_related('producten',
                                         'transacties')
                       .select_related('account',
                                       'ontvanger',
                                       'betaal_mutatie',
                                       'betaal_actief')):

        product_pks = list(bestelling.producten.values_list('pk', flat=True))
        producten = [bestelproduct_pk2bestellingproduct[pk]
                     for pk in product_pks]

        transacties = bestelling.transacties.all()

        obj = bestelling_new(
                    bestel_nr=bestelling.bestel_nr,
                    aangemaakt=bestelling.aangemaakt,
                    account=bestelling.account,
                    ontvanger=bestelling.ontvanger,
                    verkoper_naam=bestelling.verkoper_naam,
                    verkoper_adres1=bestelling.verkoper_adres1,
                    verkoper_adres2=bestelling.verkoper_adres2,
                    verkoper_kvk=bestelling.verkoper_kvk,
                    verkoper_btw_nr=bestelling.verkoper_btw_nr,
                    verkoper_email=bestelling.verkoper_email,
                    verkoper_telefoon=bestelling.verkoper_telefoon,
                    verkoper_iban=bestelling.verkoper_iban,
                    verkoper_bic=bestelling.verkoper_bic,
                    verkoper_heeft_mollie=bestelling.verkoper_heeft_mollie,
                    afleveradres_regel_1=bestelling.afleveradres_regel_1,
                    afleveradres_regel_2=bestelling.afleveradres_regel_2,
                    afleveradres_regel_3=bestelling.afleveradres_regel_3,
                    afleveradres_regel_4=bestelling.afleveradres_regel_4,
                    afleveradres_regel_5=bestelling.afleveradres_regel_5,
                    transport=bestelling.transport,
                    verzendkosten_euro=bestelling.verzendkosten_euro,
                    btw_percentage_cat1=bestelling.btw_percentage_cat1,
                    btw_percentage_cat2=bestelling.btw_percentage_cat2,
                    btw_percentage_cat3=bestelling.btw_percentage_cat3,
                    btw_euro_cat1=bestelling.btw_euro_cat1,
                    btw_euro_cat2=bestelling.btw_euro_cat2,
                    btw_euro_cat3=bestelling.btw_euro_cat3,
                    totaal_euro=bestelling.totaal_euro,
                    status=bestelling.status,
                    betaal_mutatie=bestelling.betaal_mutatie,
                    betaal_actief=bestelling.betaal_actief,
                    log=bestelling.log)
        obj.save()
        obj.producten.set(producten)
        obj.transacties.set(transacties)

        bestelling2_pk2bestelling[bestelling.pk] = obj
    # for

    # mutaties overnemen
    # (schatting: 10000 records)
    print('U', end='')
    bulk = list()
    for mutatie in (mutatie_oud     # pragma: no cover
                    .objects
                    .select_related('product',
                                    'bestelling',
                                    'wedstrijd_inschrijving',
                                    'evenement_inschrijving',
                                    'webwinkel_keuze',
                                    'account')):
        if mutatie.product is not None:
            product = bestelproduct_pk2bestellingproduct[mutatie.product.pk]
        else:
            product = None

        if mutatie.bestelling is not None:
            bestelling = bestelling2_pk2bestelling[mutatie.bestelling.pk]
        else:
            bestelling = None

        obj = mutatie_new(
                    when=mutatie.when,
                    code=mutatie.code,
                    is_verwerkt=mutatie.is_verwerkt,
                    account=mutatie.account,
                    wedstrijd_inschrijving=mutatie.wedstrijd_inschrijving,
                    webwinkel_keuze=mutatie.webwinkel_keuze,
                    product=product,
                    korting=mutatie.korting,
                    bestelling=bestelling,
                    betaling_is_gelukt=mutatie.betaling_is_gelukt,
                    bedrag_euro=mutatie.bedrag_euro,
                    transport=mutatie.transport)
        bulk.append(obj)
        if len(bulk) >= 500:
            mutatie_new.objects.bulk_create(bulk)
            bulk = list()
    # for
    if len(bulk):
        mutatie_new.objects.bulk_create(bulk)
    del bulk

    print('...', end='')


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0001_initial'),
        ('Bestel', 'm0030_rename'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='bestelling',
            name='aangemaakt',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='bestellingmutatie',
            name='when',
            field=models.DateTimeField(),
        ),
        migrations.RunPython(migrate_from_bestel),
        migrations.AlterField(
            model_name='bestelling',
            name='aangemaakt',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='bestellingmutatie',
            name='when',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

# end of file
