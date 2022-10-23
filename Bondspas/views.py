# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.utils.formats import date_format
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import GESLACHT_ANDERS
from Functie.rol import rol_get_huidige, Rollen
from Plein.menu import menu_dynamics
from Sporter.models import Sporter, get_sporter_voorkeuren
from Sporter.leeftijdsklassen import (bereken_leeftijdsklasse_wa,
                                      bereken_leeftijdsklasse_nhb,
                                      bereken_leeftijdsklasse_ifaa)
from PIL import Image, ImageFont, ImageDraw
from PIL.PngImagePlugin import PngInfo
import io
import datetime
import base64
import os


TEMPLATE_BONDSPAS_TONEN = 'bondspas/bondspas-tonen.dtl'


def maak_bondspas_regels(lid_nr, jaar):
    """ Bepaal de regels tekst die op de bondspas moeten komen voor deze specifieke sporter
    """
    regels = list()

    sporter = Sporter.objects.get(lid_nr=lid_nr)
    voorkeur = get_sporter_voorkeuren(sporter)

    regels.append(("lid_nr", str(sporter.lid_nr)))
    regels.append(("WA_id", '12345'))    # sporter.wa_id

    regels.append(("Naam", sporter.volledige_naam()))
    regels.append(("Geboren", date_format(sporter.geboorte_datum, "j F Y")))

    if sporter.bij_vereniging:
        regels.append(("Vereniging", sporter.bij_vereniging.ver_nr_en_naam()))
    else:
        regels.append(("Vereniging", "onbekend :-("))

    # TODO: opleidingen
    regels.append(("Opleidingen", "n.v.t."))

    # TODO: speelsterkte
    regels.append(("Speelsterkte", "n.v.t."))

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

    regels.append(('Wedstrijdklassen', ''))

    lkl_wa = bereken_leeftijdsklasse_wa(wedstrijdleeftijd_wa, wedstrijdgeslacht)
    regels.append(("WA", lkl_wa))

    lkl_nhb = bereken_leeftijdsklasse_nhb(wedstrijdleeftijd_wa, wedstrijdgeslacht_nhb)
    if lkl_nhb != lkl_wa or True:
        regels.append(("NHB", lkl_nhb))

    lkl_ifaa_1 = bereken_leeftijdsklasse_ifaa(wedstrijdleeftijd_ifaa_voor_verjaardag, wedstrijdgeslacht)
    lkl_ifaa_2 = bereken_leeftijdsklasse_ifaa(wedstrijdleeftijd_ifaa_vanaf_verjaardag, wedstrijdgeslacht)

    if lkl_ifaa_1 == lkl_ifaa_2:
        regels.append(("IFAA", lkl_ifaa_1))
    else:
        schakel_str = date_format(sporter.geboorte_datum, "j F")
        regels.append(("IFAA tot %s" % schakel_str, lkl_ifaa_1))
        regels.append(("IFAA vanaf %s" % schakel_str, lkl_ifaa_2))

    return regels


def teken_barcode(lid_nr, draw, end_x, end_y, font):
    """
        Barcode volgens "Code 39", zonder checksum
        See https://en.wikipedia.org/wiki/Code_39
    """
    lid_nr = str(lid_nr)

    # meerdere 1-en en 0-en maken een dikke balk (ratio 1:3)
    sym_start_stop = "100010111011101"
    sym_between = "0"
    sym_digits = {
        "0": "101000111011101",
        "1": "111010001010111",
        "2": "101110001010111",
        "3": "111011100010101",
        "4": "101000111010111",
        "5": "111010001110101",
        "6": "101110001110101",
        "7": "101000101110111",
        "8": "111010001011101",
        "9": "101110001011101",
    }

    code39 = sym_start_stop + sym_between
    for digit in lid_nr:
        code39 += sym_digits[digit]
        code39 += sym_between
    # for
    code39 += sym_start_stop

    # teken de lijntjes van de barcode
    pixels = 2
    y = end_y
    width = len(code39) * pixels
    x = end_x - width
    for code in code39:
        if code == "1":
            draw.rectangle(((x, y - 60), (x + pixels - 1, y)), fill=(0, 0, 0))
        x += pixels
    # for

    # teken de cijfers onder de barcode
    margin = 10
    digit_count = len(lid_nr)
    digit_width = draw.textlength("8", font=font)
    digit_step = round((width - 2 * margin - digit_count * digit_width) / (digit_count - 1))
    digit_step += digit_width
    digit_x = end_x - width + margin
    for digit in lid_nr:
        draw.text((digit_x, y), digit, (0, 0, 0), font=font, anchor="la")
        digit_x += digit_step
    # for


def maak_bondspas_image(lid_nr, jaar, regels):
    fpath = os.path.join(settings.STATIC_ROOT, 'bondspas', 'achtergrond_bondspas.png')
    image = Image.open(fpath)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(settings.BONDSPAS_FONT, size=18)
    font_bold = ImageFont.truetype(settings.BONDSPAS_FONT_BOLD, size=25)
    color_black = (0, 0, 0)
    color_grijs = (221, 217, 215)       # reverse engineered

    # het grijze kader waarin de tekst moet komen
    # coördinaten: (0,0) = top-left
    _, _, width, height = image.getbbox()
    kader_y1 = 239          # bovenkant
    kader_y2 = 469          # onderkant
    kader_x1 = 2            # border is 2 pixels
    kader_x2 = width - 2

    # zet een marge van 10 pixels
    kader_y1 += 10
    kader_y2 -= 10
    kader_x1 += 30
    kader_x2 -= 30

    # teken het grijze vlak opnieuw
    # er zou geen kleurverschil moeten zijn
    draw.rectangle(((kader_x1, kader_y1), (kader_x2, kader_y2)), fill=color_grijs)

    # bondsnummer en WA id
    lid_nr = regels[0][1]
    wa_id = regels[1][1]
    regels = regels[2:]

    text_width, text_height = draw.textsize(lid_nr, font=font_bold)
    bondsnr_width = draw.textlength("Bondsnummer: ", font=font)
    bondsnr_x = kader_x2 - text_width - bondsnr_width
    bondsnr_y = kader_y1 - text_height

    if len(wa_id):
        # zet de teksten "World archery ID" en "Bondsnummer" onder elkaar
        draw.text((bondsnr_x, bondsnr_y), "World Archery ID: " + wa_id, color_black, font=font, anchor="ls")
        bondsnr_y -= text_height

    # bondsnummer
    # text anchors: https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
    draw.text((bondsnr_x, bondsnr_y), "Bondsnummer: ", color_black, font=font, anchor="ls")
    draw.text((bondsnr_x + bondsnr_width, bondsnr_y), lid_nr, color_black, font=font_bold, anchor="ls")

    # barcode
    teken_barcode(lid_nr, draw, kader_x2, bondsnr_y - 3 * text_height, font)

    # switch naar een kleiner font
    del font_bold
    font = ImageFont.truetype(settings.BONDSPAS_FONT, size=17)
    _, text_height = draw.textsize(lid_nr, font=font)

    text_spacing = text_height + 5
    wkl_indent = 30     # pixels

    # bepaal hoe breed de eerste kolom moet worden
    header_width = 1
    header_width_wkl = 1
    wkl = False
    for header, _ in regels:

        header += ': '
        text_width = draw.textlength(header, font=font)

        if wkl:
            text_width += wkl_indent
            header_width = max(header_width, text_width)
            header_width_wkl = max(header_width_wkl, text_width)
        else:
            header_width = max(header_width, text_width)

        if header == "Wedstrijdklassen: ":
            wkl = True
    # for

    next_y = kader_y1
    wkl = False
    for header, regel in regels:
        header += ': '

        if wkl:
            draw.text((kader_x1 + header_width - header_width_wkl + wkl_indent, next_y), header, color_black, font=font)
        else:
            draw.text((kader_x1, next_y), header, color_black, font=font)

        draw.text((kader_x1 + header_width, next_y), regel, color_black, font=font)
        next_y += text_spacing

        if header == "Wedstrijdklassen: ":
            wkl = True
    # for

    metadata = PngInfo()
    metadata.add_text("Copyright", "de Nederlandse Handboog Bonds (NHB)")
    metadata.add_text("Title", "Bondspas %s voor lid %s" % (jaar, lid_nr))

    output = io.BytesIO()
    image.save(output, format='PNG', pnginfo=metadata)
    output.seek(0)
    return output.getvalue()


class ToonBondspasView(UserPassesTestMixin, View):

    """ Deze view kan de bondspas tonen, of een scherm met 'even wachten, we zoeken je pas op' """

    template_name = TEMPLATE_BONDSPAS_TONEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        # bepaal het jaar voor de wedstrijdklasse
        now = timezone.localtime(timezone.now())
        jaar = now.year

        account = self.request.user
        lid_nr = account.username

        regels = maak_bondspas_regels(lid_nr, jaar)

        png_data = maak_bondspas_image(lid_nr, jaar, regels)

        context['bondspas_base64'] = base64.b64encode(png_data).decode()

        context['kruimels'] = (
            (None, 'Bondspas'),
        )

        # toon een pagina die wacht op de download
        menu_dynamics(request, context)
        return render(request, self.template_name, context)


# end of file
