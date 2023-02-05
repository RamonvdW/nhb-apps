# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via BestelMutatie
"""

from django.conf import settings
from django.utils import timezone
from django.utils.formats import date_format
from django.core.management.base import BaseCommand
from BasisTypen.definities import GESLACHT_ANDERS
from Sporter.models import Sporter, get_sporter_voorkeuren
from Sporter.leeftijdsklassen import (bereken_leeftijdsklasse_wa,
                                      bereken_leeftijdsklasse_nhb,
                                      bereken_leeftijdsklasse_ifaa)
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes, colors
import datetime


class Command(BaseCommand):     # pragma: no cover

    help = "Betaal mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument('lid_nr', type=int)

    def maak_pdf(self, jaar, lid_nr, pdf_naam):

        sporter = Sporter.objects.get(lid_nr=lid_nr)
        voorkeur = get_sporter_voorkeuren(sporter)
        wedstrijdleeftijd_wa = sporter.bereken_wedstrijdleeftijd_wa(jaar)

        wedstrijd_datum = datetime.date(year=jaar, month=sporter.geboorte_datum.month, day=sporter.geboorte_datum.day)
        wedstrijdleeftijd_ifaa_vanaf_verjaardag = sporter.bereken_wedstrijdleeftijd_ifaa(wedstrijd_datum)
        if sporter.geboorte_datum.day == sporter.geboorte_datum.month == 1:
            # sporter is jarig op 1 januari, dus het hele jaar dezelfde wedstrijdleeftijd
            wedstrijdleeftijd_ifaa_voor_verjaardag = wedstrijdleeftijd_ifaa_vanaf_verjaardag
        else:
            wedstrijdleeftijd_ifaa_voor_verjaardag = wedstrijdleeftijd_ifaa_vanaf_verjaardag - 1

        if voorkeur.wedstrijd_geslacht_gekozen:
            # geslacht M/V of
            # geslacht X + keuze voor M/V gemaakt
            wedstrijdgeslacht = voorkeur.wedstrijd_geslacht
            wedstrijdgeslacht_nhb = voorkeur.wedstrijd_geslacht
        else:
            # geslacht X, geen keuze gemaakt --> neem mannen
            wedstrijdgeslacht = 'M'
            wedstrijdgeslacht_nhb = GESLACHT_ANDERS

        geboorte_jaar = sporter.geboorte_datum.year
        naam_str = sporter.volledige_naam()
        geboren_str = date_format(sporter.geboorte_datum, "j F Y")

        lkl_wa = bereken_leeftijdsklasse_wa(wedstrijdleeftijd_wa, wedstrijdgeslacht)

        lkl_nhb = bereken_leeftijdsklasse_nhb(wedstrijdleeftijd_wa, wedstrijdgeslacht_nhb)

        lkl_ifaa_1 = bereken_leeftijdsklasse_ifaa(wedstrijdleeftijd_ifaa_voor_verjaardag, wedstrijdgeslacht)
        lkl_ifaa_2 = bereken_leeftijdsklasse_ifaa(wedstrijdleeftijd_ifaa_vanaf_verjaardag, wedstrijdgeslacht)

        c = canvas.Canvas(pdf_naam, pagesize=pagesizes.A6)
        c.setAuthor("de Nederlandse Handboog Bonds (NHB) - www.handboogsport.nl")
        c.setTitle("Bondspas %s" % jaar)
        c.setSubject("Bondspas %s voor lid %s" % (jaar, sporter.lid_nr))
        c.setCreator("%s - %s" % (settings.AFSCHRIFT_SITE_NAAM, settings.AFSCHRIFT_SITE_URL))

        page_w, page_h = pagesizes.A6

        # begin met het achtergrondplaatje
        c.drawImage("Bondspas/management/commands/achtergrond_bondspas.png", 0, 0, width=page_w, height=page_h)

        regels = list()
        regels.append("Naam: %s" % naam_str)
        regels.append("Geboren: %s" % geboren_str)
        regels.append("WA wedstrijden: %s" % lkl_wa)

        if lkl_nhb != lkl_wa:
            regels.append("NHB wedstrijden: %s" % lkl_nhb)

        if lkl_ifaa_1 == lkl_ifaa_2:
            regels.append("IFAA wedstrijden: %s" % lkl_ifaa_1)
        else:
            schakel_str = date_format(sporter.geboorte_datum, "j F")
            regels.append("IFAA wedstrijden tot %s: %s" % (schakel_str, lkl_ifaa_1))
            regels.append("IFAA wedstrijden vanaf %s: %s" % (schakel_str, lkl_ifaa_2))

        if sporter.bij_vereniging:
            ver_str = sporter.bij_vereniging.ver_nr_en_naam()
            regels.append("Vereniging: %s" % ver_str)
        else:
            regels.append("Vereniging: onbekend :-(")

        # schuif op naar het begin van het kader waar de tekst moet komen
        kader_y1 = 290      # bovenkant
        kader_y2 = 190      # onderkant
        kader_marge_x = 15
        kader_marge_y = 5

        # bovenaan komt het bondsnummer
        bondsnr_x = 240
        bondsnr_y = kader_y1 - kader_marge_y - 5
        c.setFont("Helvetica-Bold", 14)
        c.drawString(bondsnr_x, bondsnr_y, str(sporter.lid_nr))
        c.setFont("Helvetica", 9)
        c.drawRightString(bondsnr_x, bondsnr_y, "Bondsnummer: ")

        # verplaats de origin naar de lijn van het bondsnummer
        c.translate(kader_marge_x, bondsnr_y)
        text_spacing_y = 13

        next_y = -1
        for regel in regels:
            c.drawString(0, next_y * text_spacing_y, regel)
            next_y -= 1

        c.showPage()
        c.save()

        self.stdout.write('[INFO] Gemaakt: %s' % pdf_naam)

    def handle(self, *args, **options):

        # bepaal het jaar voor de wedstrijdklasse
        now = timezone.now()
        jaar = now.year
        if now.month == 1 and now.day < 15:
            jaar -= 1

        lid_nr = options['lid_nr']
        pdf_naam = 'bondspas_%s.pdf' % lid_nr
        self.maak_pdf(jaar, lid_nr, pdf_naam)

# end of file
