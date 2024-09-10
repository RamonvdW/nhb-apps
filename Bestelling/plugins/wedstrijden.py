# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module levert functionaliteit voor de Bestel-applicatie, met kennis van de Wedstrijden, zoals kortingen. """

from django.conf import settings
from django.utils import timezone
from BasisTypen.definities import ORGANISATIE_IFAA
from Bestelling.models import BestellingProduct
from Mailer.operations import mailer_queue_email, mailer_email_is_valide, render_email_template
from Wedstrijden.definities import (WEDSTRIJD_KORTING_COMBI, WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF, WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD, WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR)
from Wedstrijden.models import WedstrijdKorting, WedstrijdInschrijving
from decimal import Decimal
import datetime

EMAIL_TEMPLATE_INFO_INSCHRIJVING_WEDSTRIJD = 'email_bestelling/info-inschrijving-wedstrijd.dtl'


class BepaalAutomatischeKorting(object):

    def __init__(self, stdout):
        self._stdout = stdout

        self._org_ver_nrs = list()                                # verenigingen die voorkomen in het mandje
        self._lid_nr2ver_nr = dict()                              # [lid_nr] = ver_nr
        self._lid_nr2wedstrijd_pks = dict()                       # [lid_nr] = [wedstrijd.pk, ...]
        self._lid_nr2wedstrijd_pks_eerder = dict()                # [lid_nr] = [wedstrijd.pk, ...]
        self._lid_nr_wedstrijd_pk2inschrijving = dict()           # [(lid_nr, wedstrijd_pk)] = inschrijving
        self._inschrijving_pk2product = dict()                    # [inschrijving.pk] = BestellingProduct
        self._alle_combi_kortingen = list()
        self._max_korting_euro = None
        self._max_korting_pks = None

    def _laad_mandje(self, mandje):
        """ laad de inhoud van het mandje en reset all kortingen """

        for product in (mandje
                        .producten
                        .exclude(wedstrijd_inschrijving=None)
                        .select_related('wedstrijd_inschrijving',
                                        'wedstrijd_inschrijving__korting',
                                        'wedstrijd_inschrijving__sporterboog',
                                        'wedstrijd_inschrijving__sporterboog__sporter',
                                        'wedstrijd_inschrijving__sporterboog__sporter__bij_vereniging',
                                        'wedstrijd_inschrijving__wedstrijd',
                                        'wedstrijd_inschrijving__wedstrijd__organiserende_vereniging')):

            inschrijving = product.wedstrijd_inschrijving
            self._inschrijving_pk2product[inschrijving.pk] = product

            # verwijder automatische kortingen
            if inschrijving.korting:
                inschrijving.korting = None
                inschrijving.save(update_fields=['korting'])

            product.korting_euro = Decimal(0)
            product.save(update_fields=['korting_euro'])

            inschrijving.mogelijke_kortingen = list()
            inschrijving.heeft_mogelijke_combi_korting = False

            ver_nr = inschrijving.wedstrijd.organiserende_vereniging.ver_nr
            if ver_nr not in self._org_ver_nrs:
                self._org_ver_nrs.append(ver_nr)

            sporter = inschrijving.sporterboog.sporter
            lid_nr = sporter.lid_nr
            if sporter.bij_vereniging:
                ver_nr = sporter.bij_vereniging.ver_nr
                self._lid_nr2ver_nr[lid_nr] = ver_nr
            else:
                self._lid_nr2ver_nr[lid_nr] = -1

            try:
                self._lid_nr2wedstrijd_pks[lid_nr].append(inschrijving.wedstrijd.pk)
            except KeyError:
                self._lid_nr2wedstrijd_pks[lid_nr] = [inschrijving.wedstrijd.pk]

            tup = (lid_nr, inschrijving.wedstrijd.pk)
            self._lid_nr_wedstrijd_pk2inschrijving[tup] = inschrijving
        # for

        # zoek, i.v.m. combinatiekortingen, ook naar wedstrijden waar al op ingeschreven is
        # maar we willen niet stapelen, dus als die eerder inschrijving al een korting heeft, dan niet overwegen
        for lid_nr, nieuwe_pks in self._lid_nr2wedstrijd_pks.items():
            pks = list(WedstrijdInschrijving
                       .objects
                       .filter(sporterboog__sporter__lid_nr=lid_nr)
                       .filter(korting=None)                            # niet stapelen
                       .exclude(status__in=(WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD, WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD))
                       .exclude(wedstrijd__pk__in=nieuwe_pks)
                       .values_list('wedstrijd__pk', flat=True))
            self._lid_nr2wedstrijd_pks_eerder[lid_nr] = pks
        # for

        # self._stdout.write('inschrijvingen:')
        # for lid_nr, pks in self._lid_nr2wedstrijd_pks.items():
        #     self._stdout.write('  %s: %s' % (lid_nr, repr(pks)))

        # self._stdout.write('inschrijvingen_eerder:')
        # for lid_nr, pks in self._lid_nr2wedstrijd_pks_eerder.items():
        #     self._stdout.write('  %s: %s' % (lid_nr, repr(pks)))

        # self._stdout.write('org_ver_nrs: %s' % repr(self._org_ver_nrs))

    def _zoek_mogelijke_kortingen(self):
        """ koppel aan elke inschrijving een mogelijke korting """
        lid_nrs_in_mandje = list(self._lid_nr2wedstrijd_pks.keys())

        # bepaal alle kortingen die mogelijk van toepassing kunnen zijn
        for korting in (WedstrijdKorting
                        .objects
                        .filter(uitgegeven_door__ver_nr__in=self._org_ver_nrs)
                        .select_related('voor_sporter')
                        .prefetch_related('voor_wedstrijden')):

            # kijk of deze korting van toepassing is op het mandje
            # self._stdout.write('mogelijke korting: %s (%d%%)' % (korting, korting.percentage))

            voor_wedstrijd_pks = list(korting.voor_wedstrijden.all().values_list('pk', flat=True))
            # print('  voor wedstrijd_pks: %s' % repr(voor_wedstrijd_pks))

            if korting.soort == WEDSTRIJD_KORTING_SPORTER and korting.voor_sporter:
                lid_nr = korting.voor_sporter.lid_nr
                if lid_nr in lid_nrs_in_mandje:
                    # inschrijving voor deze sporter is aanwezig in het mandje
                    # self._stdout.write('  kandidaat individuele korting voor sporter: %s' % korting.voor_sporter)

                    # kijk of deze korting van toepassing is
                    for pk in voor_wedstrijd_pks:
                        try:
                            tup = (lid_nr, pk)
                            inschrijving = self._lid_nr_wedstrijd_pk2inschrijving[tup]
                        except KeyError:
                            pass
                        else:
                            # self._stdout.write('    gevonden inschrijving: %s' % inschrijving)
                            inschrijving.mogelijke_kortingen.append(korting)

            elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
                # kijk of deze korting van toepassing is op het mandje
                target_ver_nr = korting.uitgegeven_door.ver_nr
                for lid_nr in lid_nrs_in_mandje:
                    if self._lid_nr2ver_nr[lid_nr] == target_ver_nr:
                        # inschrijving voor sporter van de bedoelde vereniging is aanwezig in het mandje
                        # self._stdout.write('  kandidaat verenigingskorting voor leden van vereniging: %s' % target_ver_nr)

                        # kijk of deze korting van toepassing is op een van de wedstrijden
                        for wedstrijd_pk in self._lid_nr2wedstrijd_pks[lid_nr]:
                            if wedstrijd_pk in voor_wedstrijd_pks:
                                tup = (lid_nr, wedstrijd_pk)
                                inschrijving = self._lid_nr_wedstrijd_pk2inschrijving[tup]
                                # self._stdout.write('    gevonden inschrijving: %s' % inschrijving)
                                inschrijving.mogelijke_kortingen.append(korting)
                        # for
                # for

            elif korting.soort == WEDSTRIJD_KORTING_COMBI:                  # pragma: no branch
                # kijk of deze korting van toepassing is op het mandje
                for lid_nr in lid_nrs_in_mandje:
                    # kijk of voldaan wordt aan de eisen van de combi-korting
                    pks = self._lid_nr2wedstrijd_pks[lid_nr] + self._lid_nr2wedstrijd_pks_eerder[lid_nr]

                    alle_gevonden = True
                    for pk in voor_wedstrijd_pks:
                        if pk not in pks:
                            alle_gevonden = False
                            break
                    # for

                    if alle_gevonden:
                        # dit is een kandidaat-korting
                        # self._stdout.write('  kandidaat combi-korting: %s' % korting)
                        self._alle_combi_kortingen.append(korting)

                        # voeg deze toe aan alle producten in het mandje waar deze bij hoort
                        for wedstrijd_pk in voor_wedstrijd_pks:
                            tup = (lid_nr, wedstrijd_pk)
                            try:
                                inschrijving = self._lid_nr_wedstrijd_pk2inschrijving[tup]
                            except KeyError:
                                # dit is een eerdere inschrijving / bestelling
                                pass
                            else:
                                inschrijving.mogelijke_kortingen.append(korting)
                                inschrijving.heeft_mogelijke_combi_korting = True
                                # self._stdout.write('    gevonden inschrijving: %s' % inschrijving)
                        # for
                # for
        # for

    def _analyseer_kortingen(self, alle_inschrijvingen, gebruikte_kortingen):
        # self._stdout.write('analyseer_kortingen: gebruikte_kortingen: %s' % gebruikte_kortingen)

        totaal_korting_euro = Decimal(0)
        for inschrijving in alle_inschrijvingen:
            if inschrijving.korting:
                procent = inschrijving.korting.percentage / Decimal('100')
                product = self._inschrijving_pk2product[inschrijving.pk]
                totaal_korting_euro += (product.prijs_euro * procent)
        # for

        # self._stdout.write('  totaal_korting: %.2f' % totaal_korting_euro)

        if totaal_korting_euro > self._max_korting_euro:
            self._max_korting_euro = totaal_korting_euro
            self._max_korting_pks = tuple(gebruikte_kortingen)

    def _analyseer_kortingen_recursief(self, alle_inschrijvingen, gebruikte_kortingen):
        # self._stdout.write('zoek_kortingen_recursief: gebruikte_kortingen: %s' % gebruikte_kortingen)
        self._analyseer_kortingen(alle_inschrijvingen, gebruikte_kortingen)

        for inschrijving in alle_inschrijvingen:
            if not inschrijving.korting:
                for korting in inschrijving.mogelijke_kortingen:
                    if korting.pk not in gebruikte_kortingen:
                        gebruikte_kortingen.append(korting.pk)
                        inschrijving.korting = korting
                        self._analyseer_kortingen(alle_inschrijvingen, gebruikte_kortingen)
                        gebruikte_kortingen.remove(korting.pk)
                # for
                inschrijving.korting = None
        # for

    def _analyseer_kortingen_recursief_combi(self, alle_inschrijvingen, gebruikte_kortingen=()):
        # self._stdout.write('zoek_kortingen_recursief_combi: gebruikte_kortingen: %s' % gebruikte_kortingen)

        gebruikte_kortingen = list(gebruikte_kortingen)     # maak een kopie

        # pas een combi-korting toe
        for korting in self._alle_combi_kortingen:
            if korting.pk not in gebruikte_kortingen:
                gebruikte_kortingen.append(korting.pk)

                # pas deze korting toe
                reset_lijst = list()
                for inschrijving in alle_inschrijvingen:
                    if not inschrijving.korting and inschrijving.heeft_mogelijke_combi_korting:
                        if korting in inschrijving.mogelijke_kortingen:
                            inschrijving.korting = korting
                            reset_lijst.append(inschrijving)
                # for

                self._analyseer_kortingen_recursief_combi(alle_inschrijvingen, gebruikte_kortingen)

                for inschrijving in reset_lijst:
                    inschrijving.korting = None
                # for

                gebruikte_kortingen.remove(korting.pk)
        # for

        # alle combi-kortingen als "gebruikt" zetten en de rest doorlopen
        for korting in self._alle_combi_kortingen:
            if korting.pk not in gebruikte_kortingen:
                gebruikte_kortingen.append(korting.pk)
        # for
        self._analyseer_kortingen_recursief(alle_inschrijvingen, gebruikte_kortingen)

    def _kortingen_toepassen(self, alle_inschrijvingen, geef_korting_pks):
        combi_korting_euro = dict()     # [korting.pk] = Decimal
        for inschrijving in alle_inschrijvingen:
            for korting in inschrijving.mogelijke_kortingen:
                if korting.pk in geef_korting_pks:
                    # geef deze korting
                    # self._stdout.write('   gekozen korting: %s' % korting)
                    inschrijving.korting = korting
                    inschrijving.save(update_fields=['korting'])

                    procent = korting.percentage / Decimal(100)
                    product = self._inschrijving_pk2product[inschrijving.pk]
                    # self._stdout.write('   product: %s' % product)
                    product.korting_euro = product.prijs_euro * procent
                    product.save(update_fields=['korting_euro'])
                    # self._stdout.write('   korting_euro: %s' % product.korting_euro)

                    if korting.soort == WEDSTRIJD_KORTING_COMBI:
                        try:
                            combi_korting_euro[korting.pk] += product.korting_euro
                        except KeyError:
                            combi_korting_euro[korting.pk] = product.korting_euro
            # for
        # for

        # voeg alle combi-kortingen samen
        combi_pks = list(combi_korting_euro.keys())
        # self._stdout.write('combi_pks: %s' % repr(combi_pks))
        for inschrijving in alle_inschrijvingen:
            if inschrijving.korting and inschrijving.korting.pk in combi_pks:
                korting_euro = combi_korting_euro[inschrijving.korting.pk]
                product = self._inschrijving_pk2product[inschrijving.pk]
                if korting_euro:
                    # samenvoegen tot de totale korting
                    product.korting_euro = korting_euro
                    product.save(update_fields=['korting_euro'])
                    combi_korting_euro[inschrijving.korting.pk] = None      # niet nog een keer geven
                else:
                    # deze korting op nul zetten
                    inschrijving.korting = None
                    inschrijving.save(update_fields=['korting'])
                    product.korting_euro = Decimal(0)
                    product.save(update_fields=['korting_euro'])
        # for

        for inschrijving in alle_inschrijvingen:
            product = self._inschrijving_pk2product[inschrijving.pk]
            self._stdout.write('product: %s' % product)
            if inschrijving.korting:
                self._stdout.write('korting: %s' % inschrijving.korting)
                # self._stdout.write('korting_euro: %s' % product.korting_euro)
            else:
                self._stdout.write('korting: geen')

    def kies_kortingen_voor_mandje(self, mandje):
        """
            bepaal welke kortingen van toepassing zijn en koppel deze aan de producten in het mandje

            kortingen mogen niet stapelen --> daarom heeft elk product maximaal 1 korting
            als meerdere kortingen van toepassing zijn, dan we geven de hoogste korting
        """

        self._laad_mandje(mandje)
        self._zoek_mogelijke_kortingen()

        alle_inschrijvingen = [inschrijving for inschrijving in self._lid_nr_wedstrijd_pk2inschrijving.values()]

        # self._stdout.write('--- Tijd om te kiezen! ---')
        # self._stdout.write('All inschrijvingen + mogelijke kortingen:')
        # for inschrijving in alle_inschrijvingen:
        #     self._stdout.write("%s" % inschrijving)
        #     self._stdout.write('  heeft_mogelijke_combi_korting: %s' % inschrijving.heeft_mogelijke_combi_korting)
        #     for korting in inschrijving.mogelijke_kortingen:
        #         self._stdout.write('  korting: %s' % korting)
        #     # for
        # # for
        # self._stdout.write('--------------------------')

        self._max_korting_euro = Decimal(0)
        self._max_korting_pks = None
        self._analyseer_kortingen_recursief_combi(alle_inschrijvingen)

        if self._max_korting_pks:
            self._stdout.write('maximale korting is %.2f met kortingen %s' % (float(self._max_korting_euro),
                                                                              repr(self._max_korting_pks)))
            self._kortingen_toepassen(alle_inschrijvingen, self._max_korting_pks)


def wedstrijden_plugin_automatische_kortingen_toepassen(stdout, mandje):
    BepaalAutomatischeKorting(stdout).kies_kortingen_voor_mandje(mandje)


def wedstrijden_plugin_inschrijven(inschrijving: WedstrijdInschrijving):
    """ verwerk een nieuwe inschrijving op een wedstrijdsessie """
    # verhoog het aantal inschrijvingen op deze sessie
    # hiermee geven we een garantie op een plekje
    # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
    sessie = inschrijving.sessie
    sessie.aantal_inschrijvingen += 1
    sessie.save(update_fields=['aantal_inschrijvingen'])

    wedstrijd = inschrijving.wedstrijd
    sporter = inschrijving.sporterboog.sporter

    leeftijd = sporter.bereken_wedstrijdleeftijd(wedstrijd.datum_begin, wedstrijd.organisatie)
    if leeftijd < 18:
        prijs = wedstrijd.prijs_euro_onder18
    else:
        prijs = wedstrijd.prijs_euro_normaal

    return prijs


def wedstrijden_plugin_afmelden(inschrijving):
    """ verwerk een afmelding voor een wedstrijdsessie """
    # verlaag het aantal inschrijvingen op deze sessie
    # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
    sessie = inschrijving.sessie
    sessie.aantal_inschrijvingen -= 1
    sessie.save(update_fields=['aantal_inschrijvingen'])

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Afgemeld voor de wedstrijd\n" % stamp_str

    # inschrijving.sessie en inschrijving.klasse kunnen niet op None gezet worden
    inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD
    inschrijving.log += msg
    inschrijving.save(update_fields=['status', 'log'])


def wedstrijden_plugin_verwijder_reservering(stdout, inschrijving):
    # zet de inschrijving om in status=afgemeld of verwijderd
    # dit heeft de voorkeur over het echt verwijderen van inschrijvingen,
    # want als er wel een betaling volgt dan kunnen we die nergens aan koppelen
    oude_status = inschrijving.status

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')

    if inschrijving.status == WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF:
        msg = "[%s] Afgemeld voor de wedstrijd en reservering verwijderd\n" % stamp_str
        inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD
    else:
        msg = "[%s] Reservering voor wedstrijd verwijderd\n" % stamp_str
        inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD

    inschrijving.korting = None
    inschrijving.log += msg
    inschrijving.save(update_fields=['status', 'log', 'korting'])

    # schrijf de sporter uit bij de sessie
    # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
    sessie = inschrijving.sessie
    if sessie.aantal_inschrijvingen > 0:  # voorkom ongelukken: kan negatief niet opslaan
        sessie.aantal_inschrijvingen -= 1
        sessie.save(update_fields=['aantal_inschrijvingen'])

    stdout.write('[INFO] Inschrijving pk=%s status %s --> %s' % (
        inschrijving.pk,
        WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR[oude_status],
        WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))


def wedstrijden_plugin_inschrijving_is_betaald(stdout, product: BestellingProduct):
    """ Deze functie wordt aangeroepen vanuit de achtergrondtaak als een bestelling betaald is,
        of als een bestelling niet betaald hoeft te worden (totaal bedrag nul)
    """
    inschrijving = product.wedstrijd_inschrijving
    inschrijving.ontvangen_euro = product.prijs_euro - product.korting_euro
    inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Betaling ontvangen (euro %s); status is nu definitief\n" % (stamp_str, inschrijving.ontvangen_euro)

    inschrijving.log += msg
    inschrijving.save(update_fields=['ontvangen_euro', 'status', 'log'])

    # stuur een e-mail naar de sporter, als dit niet de koper is
    sporter = inschrijving.sporterboog.sporter
    sporter_account = sporter.account
    koper_account = inschrijving.koper
    if sporter_account != koper_account:
        email = None
        if sporter_account and sporter_account.email_is_bevestigd:
            email = sporter_account.bevestigde_email
        else:
            if mailer_email_is_valide(sporter.email):
                email = sporter.email

        if email:
            # maak de e-mail en stuur deze naar sporter.

            aanwezig = datetime.datetime.combine(inschrijving.sessie.datum, inschrijving.sessie.tijd_begin)
            aanwezig -= datetime.timedelta(minutes=inschrijving.wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn)

            context = {
                'voornaam': sporter.voornaam,
                'koper_volledige_naam': koper_account.volledige_naam(),
                'reserveringsnummer': settings.TICKET_NUMMER_START__WEDSTRIJD + inschrijving.pk,
                'wed_titel': inschrijving.wedstrijd.titel,
                'wed_adres': inschrijving.wedstrijd.locatie.adres_oneliner(),
                'wed_datum': inschrijving.sessie.datum,
                'wed_klasse': inschrijving.wedstrijdklasse.beschrijving,
                'wed_org_ver': inschrijving.wedstrijd.organiserende_vereniging,
                'aanwezig_tijd': aanwezig.strftime('%H:%M'),
                'contact_email': inschrijving.wedstrijd.contact_email,
                'contact_tel': inschrijving.wedstrijd.contact_telefoon,
                'geen_account': sporter.account is None,
                'naam_site': settings.NAAM_SITE,
            }

            if inschrijving.wedstrijd.organisatie == ORGANISATIE_IFAA:
                context['wed_klasse'] += ' [%s]' % inschrijving.wedstrijdklasse.afkorting

            mail_body = render_email_template(context, EMAIL_TEMPLATE_INFO_INSCHRIJVING_WEDSTRIJD)

            mailer_queue_email(email,
                               'Inschrijving op wedstrijd',
                               mail_body)

            stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
            msg = "[%s] Informatieve e-mail is gestuurd naar sporter %s\n" % (stamp_str, sporter.lid_nr)
            inschrijving.log += msg
            inschrijving.save(update_fields=['log'])

            stdout.write('[INFO] Informatieve e-mail is gestuurd naar sporter %s' % sporter.lid_nr)
        else:
            msg = "[%s] Kan geen informatieve e-mail sturen naar sporter %s (geen e-mail beschikbaar)\n" % (
                        sporter.lid_nr, stamp_str)
            inschrijving.log += msg
            inschrijving.save(update_fields=['log'])

            stdout.write('[INFO] Kan geen informatieve e-mail sturen naar sporter %s (geen e-mail beschikbaar)' %
                         sporter.lid_nr)


def wedstrijden_plugin_beschrijf_product(inschrijving):
    """
        Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
    """
    beschrijving = list()

    tup = ('Reserveringsnummer', settings.TICKET_NUMMER_START__WEDSTRIJD + inschrijving.pk)
    beschrijving.append(tup)

    tup = ('Wedstrijd', inschrijving.wedstrijd.titel)
    beschrijving.append(tup)

    tup = ('Bij vereniging', inschrijving.wedstrijd.organiserende_vereniging)
    beschrijving.append(tup)

    sessie = inschrijving.sessie
    tup = ('Sessie', '%s vanaf %s' % (sessie.datum, sessie.tijd_begin.strftime('%H:%M')))
    beschrijving.append(tup)

    aanwezig = datetime.datetime.combine(inschrijving.sessie.datum, inschrijving.sessie.tijd_begin)
    aanwezig -= datetime.timedelta(minutes=inschrijving.wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn)
    tup = ('Aanwezig zijn om', aanwezig.strftime('%H:%M'))
    beschrijving.append(tup)

    sporterboog = inschrijving.sporterboog
    tup = ('Sporter', '%s' % sporterboog.sporter.lid_nr_en_volledige_naam())
    beschrijving.append(tup)

    sporter_ver = sporterboog.sporter.bij_vereniging
    if sporter_ver:
        ver_naam = sporter_ver.ver_nr_en_naam()
    else:
        ver_naam = 'Onbekend'
    tup = ('Lid bij vereniging', ver_naam)
    beschrijving.append(tup)

    if inschrijving.wedstrijd.organisatie == ORGANISATIE_IFAA:
        tup = ('Schietstijl', '%s' % sporterboog.boogtype.beschrijving)
    else:
        tup = ('Boog', '%s' % sporterboog.boogtype.beschrijving)
    beschrijving.append(tup)

    if inschrijving.wedstrijd.organisatie == ORGANISATIE_IFAA:
        tup = ('Wedstrijdklasse', '%s [%s]' % (inschrijving.wedstrijdklasse.beschrijving,
                                               inschrijving.wedstrijdklasse.afkorting))
    else:
        tup = ('Wedstrijdklasse', '%s' % inschrijving.wedstrijdklasse.beschrijving)
    beschrijving.append(tup)

    tup = ('Locatie', inschrijving.wedstrijd.locatie.adres_oneliner())
    beschrijving.append(tup)

    tup = ('E-mail organisatie', inschrijving.wedstrijd.contact_email)
    beschrijving.append(tup)

    tup = ('Telefoon organisatie', inschrijving.wedstrijd.contact_telefoon)
    beschrijving.append(tup)

    return beschrijving


def wedstrijden_beschrijf_korting(inschrijving):

    korting_str = None
    korting_redenen = list()

    if inschrijving.korting:
        korting = inschrijving.korting

        if korting.soort == WEDSTRIJD_KORTING_SPORTER:
            korting_str = "Persoonlijke korting: %d%%" % korting.percentage

        elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
            korting_str = "Verenigingskorting: %d%%" % korting.percentage

        elif korting.soort == WEDSTRIJD_KORTING_COMBI:              # pragma: no branch
            korting_str = "Combinatiekorting: %d%%" % korting.percentage
            korting_redenen = [wedstrijd.titel for wedstrijd in korting.voor_wedstrijden.all()]

    return korting_str, korting_redenen

# end of file
