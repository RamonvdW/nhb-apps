# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from Bestel.models import BestelProduct, BestelMandje
from decimal import Decimal


SESSIONVAR_MANDJE_INHOUD_AANTAL = 'mandje_inhoud_aantal'
SESSIONVAR_MANDJE_EVAL_AFTER = 'mandje_eval_after'

MANDJE_EVAL_INTERVAL_MINUTES = 1


def cached_aantal_in_mandje_get(request):
    """ retourneer hoeveel items in het mandje zitten
        dit wordt onthouden in de sessie
    """

    try:
        aantal = request.session[SESSIONVAR_MANDJE_INHOUD_AANTAL]
    except KeyError:
        aantal = 0

    return aantal


def mandje_tel_inhoud(request):
    """ tel het aantal producten in het mandje en cache het resultaat in een sessie variabele """

    try:
        mandje = (BestelMandje
                  .objects
                  .prefetch_related('producten')
                  .get(account=request.user))
    except BestelMandje.DoesNotExist:
        # geen mandje gevonden
        aantal = 0
    else:
        aantal = mandje.producten.count()

    request.session[SESSIONVAR_MANDJE_INHOUD_AANTAL] = aantal

    next_eval = timezone.now() + timedelta(seconds=60 * MANDJE_EVAL_INTERVAL_MINUTES)
    eval_after = str(next_eval.timestamp())     # number of seconds since 1-1-1970
    request.session[SESSIONVAR_MANDJE_EVAL_AFTER] = eval_after


def eval_mandje_inhoud(request):
    """ Als de gebruiker een tijdje weggeweest is dan kan de achtergrondtaak het mandje geleegd hebben.
        Als er dus iets in het mandje zit van deze gebruiker, kijk dan 1x per minuut of dit nog steeds zo is.
        Actief toevoegen/verwijderen resulteert ook in de evaluatie.
    """

    # kijk of het al weer tijd is
    try:
        eval_after = request.session[SESSIONVAR_MANDJE_EVAL_AFTER]
    except KeyError:
        eval_after = None

    now_str = str(timezone.now().timestamp())

    if eval_after and now_str <= eval_after:
        # nog niet
        return

    # update het aantal open taken in de sessie
    # en zet het volgende evaluatie moment
    mandje_tel_inhoud(request)


def mandje_toevoegen_inschrijving(account, inschrijving, prijs_euro):

    """ Deze functie wordt gebruikt van de achtergrondtaak van de kalender om een bestelling toe te voegen
        aan een mandje.
    """

    # maak een product regel aan voor de bestelling
    product = BestelProduct(
                    inschrijving=inschrijving,
                    prijs_euro=prijs_euro)
    product.save()

    # zoek het mandje van de koper erbij (of maak deze aan)
    mandje, is_created = BestelMandje.objects.get_or_create(account=account)

    # leg het product in het mandje
    mandje.producten.add(product)

    # verhoog de totale prijs
    with transaction.atomic():
        mandje = BestelMandje.objects.select_for_update().get(pk=mandje.pk)
        mandje.totaal_euro += prijs_euro
        mandje.save()

    return product


def mandje_verwijder_inschrijving(account, inschrijving):

    try:
        product = BestelProduct(inschrijving=inschrijving)
    except BestelProduct.DoesNotExist:
        # inschrijving niet gevonden, dus geen onderdeel van een bestelling of een mandje
        pass
    else:
        # product gevonden

        # zoek het mandje van de koper erbij
        with transaction.atomic():
            try:
                mandje = BestelMandje.objects.select_for_update().get(account=account)
            except BestelMandje.DoesNotExist:
                # mandje is er niet meer
                pass
            else:
                # mandje gevonden, product gevonden
                # verwijder het product uit het mandje, of het er nou in zit of niet
                mandje.producten.remove(product)

                # omdat er nu een product uit verwijderd is en een korting vervallen is:
                # bepaal opnieuw de totaal prijs van de inhoud van het mandje en sla deze op
                mandje.bepaal_totaalprijs_opnieuw()           # adviseert select_for_update


def mandje_enum_inschrijvingen(account):
    """ iterator voor de inschrijvingen die in het mandje van het gevraagde account te vinden zijn
        yield een KalenderWedstrijdInschrijving, MandjeProduct (met het veld inschrijving)
    """
    # haal het mandje op
    try:
        mandje = BestelMandje.objects.get(account=account)
    except BestelMandje.DoesNotExist:
        # geen mandje, dus ook geen producten om over te itereren
        pass
    else:
        for product in (mandje
                        .producten
                        .exclude(inschrijving=None)
                        .select_related('inschrijving',
                                        'inschrijving__sporterboog__sporter',
                                        'inschrijving__sporterboog__sporter__bij_vereniging')):
            product.komt_uit_mandje = True
            yield product.inschrijving, product
        # for


def mandje_korting_toepassen(product, percentage):
    """ Pas een gegeven kortingspercentage (positive integer) toe op de prijs van een product in het mandje
        De aanroeper heeft al gecontroleerd dat de korting toegepast mag worden.
        Deze functie mag alleen aangeroepen worden voor producten die door een van de mandje_enum_ functies
        geretourneerd is.

        Na aanroep moet de totaal_prijs van het mandje opnieuw vastgesteld worden
    """

    if product.komt_uit_mandje:
        procent = percentage / Decimal(100.0)
        product.korting_euro = product.prijs_euro * procent
        product.korting_euro = min(product.korting_euro, product.prijs_euro)  # voorkom korting > prijs
        product.save(update_fields=['korting_euro'])


def mandje_totaal_opnieuw_bepalen(account):
    """ bereken het totaal_euro veld opnieuw voor de inhoud van het mandje """
    # zoek het mandje van de koper erbij
    with transaction.atomic():
        try:
            mandje = BestelMandje.objects.select_for_update().get(account=account)
        except BestelMandje.DoesNotExist:
            # mandje is er niet meer
            pass
        else:
            # mandje gevonden
            mandje.bepaal_totaalprijs_opnieuw()     # adviseert select_for_update

# end of file
