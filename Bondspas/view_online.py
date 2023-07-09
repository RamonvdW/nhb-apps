# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.shortcuts import render, reverse
from django.views.generic import View
from django.utils.formats import date_format
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import GESLACHT_ANDERS
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Opleidingen.models import OpleidingDiploma
from Plein.menu import menu_dynamics
from Sporter.models import Sporter, get_sporter_voorkeuren
from Sporter.leeftijdsklassen import (bereken_leeftijdsklasse_wa,
                                      bereken_leeftijdsklasse_khsn,
                                      bereken_leeftijdsklasse_ifaa)
from PIL import Image, ImageFont, ImageDraw
from PIL.TiffImagePlugin import ImageFileDirectory_v2
import io
import datetime
import base64
import os


TEMPLATE_BONDSPAS_TONEN = 'bondspas/toon-bondspas-sporter.dtl'
TEMPLATE_BONDSPAS_VAN_TONEN = 'bondspas/toon-bondspas-van.dtl'

EXIF_TAG_COPYRIGHT = 0x8298
EXIF_TAG_TITLE = 0x010D     # DocumentName
# EXIF_TAG_TITLE = 0x010E     # ImageDescription


def maak_bondspas_regels(lid_nr, jaar):
    """ Bepaal de regels tekst die op de bondspas moeten komen voor deze specifieke sporter
    """
    regels = list()

    sporter = Sporter.objects.get(lid_nr=lid_nr)
    voorkeur = get_sporter_voorkeuren(sporter)

    regels.append(("lid_nr", str(sporter.lid_nr)))
    regels.append(("WA_id", sporter.wa_id))

    regels.append(("Naam", sporter.volledige_naam()))
    regels.append(("Geboren", date_format(sporter.geboorte_datum, "j F Y")))

    if sporter.bij_vereniging:
        regels.append(("Vereniging", sporter.bij_vereniging.ver_nr_en_naam()))
    else:
        regels.append(("Vereniging", "onbekend :-("))

    # para classificatie
    if sporter.para_classificatie:
        regels.append(("Para classificatie", sporter.para_classificatie))

    # opleidingen
    opleiding_codes = dict()        # [code] =
    for code, afkorting_voor_pas, _, vervangt_codes in settings.OPLEIDING_CODES:
        opleiding_codes[code] = (afkorting_voor_pas, vervangt_codes)
    # for

    afkortingen = list()
    diplomas = OpleidingDiploma.objects.filter(sporter=sporter, toon_op_pas=True).order_by('code')
    alle_codes = [diploma.code for diploma in diplomas]
    for diploma in diplomas:
        try:
            afkorting_voor_pas, vervangt_codes = opleiding_codes[diploma.code]
        except KeyError:
            # onbekend diploma
            pass
        else:
            onderdruk = any([code in alle_codes for code in vervangt_codes])
            if not onderdruk:
                afkortingen.append(afkorting_voor_pas)
    # for
    if len(afkortingen):
        regels.append(("Opleidingen", ", ".join(afkortingen)))
    else:
        regels.append(("Opleidingen", "n.v.t."))

    # speelsterkte
    afkortingen = list()
    afkortingen_basis = list()
    prev_disc = None
    for sterkte in sporter.speelsterkte_set.order_by('volgorde'):    # laagste eerst = beste eerst
        if sterkte.discipline != prev_disc:
            if sterkte.volgorde >= 600:
                afkortingen_basis.append(sterkte.pas_code)
            else:
                afkortingen.append(sterkte.pas_code)
            prev_disc = sterkte.discipline
    # for

    # toon de basis codes alleen als er geen hogere codes zijn
    # iemand met "meesterschutter" hoeft geen beginnen awards meer te zien
    if len(afkortingen) == 0:
        afkortingen = afkortingen_basis

    if len(afkortingen):
        msg = ", ".join(afkortingen)
        if len(msg) > 30:
            pos = msg.find(', ', int(len(msg)/2))
            regels.append(("Speelsterkte", msg[:pos+1]))  # inclusief komma
            regels.append(("", msg[pos+2:]))
        else:
            regels.append(("Speelsterkte", msg))
    else:
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
        wedstrijdgeslacht_khsn = voorkeur.wedstrijd_geslacht
    else:
        # geslacht X, geen keuze gemaakt --> neem mannen
        wedstrijdgeslacht = 'M'
        wedstrijdgeslacht_khsn = GESLACHT_ANDERS

    regels.append(('Wedstrijdklassen', ''))

    lkl_wa = bereken_leeftijdsklasse_wa(wedstrijdleeftijd_wa, wedstrijdgeslacht)
    regels.append(("WA", lkl_wa))

    lkl_khsn = bereken_leeftijdsklasse_khsn(wedstrijdleeftijd_wa, wedstrijdgeslacht_khsn)
    if lkl_khsn != lkl_wa:
        regels.append(("KHSN", lkl_khsn))

    lkl_ifaa_1 = bereken_leeftijdsklasse_ifaa(wedstrijdleeftijd_ifaa_voor_verjaardag, wedstrijdgeslacht)
    lkl_ifaa_2 = bereken_leeftijdsklasse_ifaa(wedstrijdleeftijd_ifaa_vanaf_verjaardag, wedstrijdgeslacht)

    if lkl_ifaa_1 == lkl_ifaa_2:
        regels.append(("IFAA", lkl_ifaa_1))
    else:
        schakel_str = date_format(sporter.geboorte_datum, "j F")
        regels.append(("IFAA tot %s" % schakel_str, lkl_ifaa_1))
        regels.append(("IFAA vanaf %s" % schakel_str, lkl_ifaa_2))

    return regels


def teken_barcode(lid_nr, draw, begin_x, end_y, font):
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

    _, _, digit_width, digit_height = draw.textbbox((0, 0), "8", font=font)

    # teken de lijntjes van de barcode
    pixels = 3
    y = end_y - digit_height - 10
    width = len(code39) * pixels
    x = begin_x
    for code in code39:
        if code == "1":
            draw.rectangle(((x, y - 80), (x + pixels - 1, y)), fill=(0, 0, 0))
        x += pixels
    # for

    # teken de cijfers onder de barcode
    margin = 10
    digit_count = len(lid_nr)
    digit_step = round((width - 2 * margin - digit_count * digit_width) / (digit_count - 1))
    digit_step += digit_width
    digit_x = begin_x
    for digit in lid_nr:
        draw.text((digit_x, y), digit, (0, 0, 0), font=font, anchor="la")
        digit_x += digit_step
    # for


def maak_bondspas_image(lid_nr, jaar, regels):
    fpath = os.path.join(settings.INSTALL_PATH, 'Bondspas', 'files', 'achtergrond_bondspas.jpg')
    image = Image.open(fpath)
    _, _, width, height = image.getbbox()

    # image = image.resize((960, 1353))        # standard size = 1280 x 1804
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(settings.BONDSPAS_FONT, size=40)
    font_bold = ImageFont.truetype(settings.BONDSPAS_FONT_BOLD, size=45)
    color_black = (0, 0, 0)
    # color_grijs = (221, 217, 215)       # reverse engineered

    # het grijze kader waarin de tekst moet komen
    # coördinaten: (0,0) = top-left
    grijze_kader_x1 = 0            # border is 2 pixels
    grijze_kader_x2 = width
    grijze_kader_y1 = 833          # bovenkant
    grijze_kader_y2 = 1507         # onderkant

    # controleer waar het grijze vlak komt
    # color_grijs = (200, 200, 200)
    # draw.rectangle(((grijze_kader_x1, grijze_kader_y1), (grijze_kader_x2, grijze_kader_y2)), fill=color_grijs)

    # witte_kader_x1 = 0
    witte_kader_x2 = width
    witte_kader_y1 = grijze_kader_y2 + 1
    witte_kader_y2 = witte_kader_y1 + 225

    # controleer waar het witte vlak komt
    # color_grijs = (200, 200, 200)
    # draw.rectangle(((witte_kader_x1+20, witte_kader_y1), (witte_kader_x2-20, witte_kader_y2)), fill=color_grijs)

    # zwart kader ronde het hele plaatje
    draw.rectangle(((0, 0), (image.width - 1, image.height - 1)), width=2, fill=None, outline=color_black)

    # zet een marge van 10 pixels
    grijze_kader_y1 += 30
    # kader_y2 -= 20
    grijze_kader_x1 += 50
    grijze_kader_x2 -= 50

    witte_kader_y_midden = witte_kader_y1 + int((witte_kader_y2 - witte_kader_y1) / 2)
    witte_kader_x1 = grijze_kader_x1

    # bondsnummer en WA id
    lid_nr = regels[0][1]
    wa_id = regels[1][1]
    regels = regels[2:]

    _, _, text_width, text_height = draw.textbbox((0, 0),
                                                  lid_nr, font=font_bold)

    wa_id_x = bondsnr_x = witte_kader_x1
    wa_id_y = witte_kader_y_midden + 25

    if len(wa_id):
        bondsnr_y = witte_kader_y_midden - 25
    else:
        bondsnr_y = witte_kader_y_midden

    # bondsnummer
    # text anchors: https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
    bondsnr_width = draw.textlength("Bondsnummer: ", font=font)
    draw.text((bondsnr_x, bondsnr_y),
              "Bondsnummer: ", color_black, font=font, anchor="lb")
    draw.text((bondsnr_x + bondsnr_width, bondsnr_y),
              lid_nr, color_black, font=font_bold, anchor="lb")

    if len(wa_id):
        draw.text((wa_id_x, wa_id_y),
                  "World Archery ID: " + wa_id, color_black, font=font, anchor="lt")

    # barcode
    # 480 plaatst deze midden boven de logo's van WA en IFAA
    teken_barcode(lid_nr, draw, witte_kader_x2 - 480, witte_kader_y_midden + 70, font)

    # switch naar een kleiner font
    font = ImageFont.truetype(settings.BONDSPAS_FONT, size=40)
    font_bold = ImageFont.truetype(settings.BONDSPAS_FONT_BOLD, size=40)
    _, _, _, text_height = draw.textbbox((0, 0), lid_nr, font=font)

    text_spacing = text_height + 15
    wkl_indent = 30     # pixels

    # bepaal hoe breed de eerste kolom moet worden
    header_width = 1
    header_width_wkl = 1
    wkl = False
    for header, _ in regels:

        header += ': '
        text_width = draw.textlength(header, font=font_bold)

        if wkl:
            text_width += wkl_indent
            header_width = max(header_width, text_width)
            header_width_wkl = max(header_width_wkl, text_width)
        else:
            header_width = max(header_width, text_width)

        if header == "Wedstrijdklassen: ":
            wkl = True
    # for

    next_y = grijze_kader_y1
    wkl = False
    for header, regel in regels:
        if header:
            header += ': '
            if wkl:
                draw.text((grijze_kader_x1 + header_width - header_width_wkl + wkl_indent, next_y),
                          header, color_black, font=font_bold)
            else:
                draw.text((grijze_kader_x1, next_y),
                          header, color_black, font=font)

        draw.text((grijze_kader_x1 + header_width, next_y),
                  regel, color_black, font=font)
        next_y += text_spacing

        if header == "Wedstrijdklassen: ":
            wkl = True
    # for

    ifd = ImageFileDirectory_v2()
    ifd[EXIF_TAG_COPYRIGHT] = "Koninklijke HandboogSport Nederland (KHSN)"
    ifd[EXIF_TAG_TITLE] = "Bondspas %s voor lid %s" % (jaar, lid_nr)

    exif_out = io.BytesIO()
    ifd.save(exif_out)
    exif_bytes = b"Exif\x00\x00" + exif_out.getvalue()

    output = io.BytesIO()
    image.save(output, format='JPEG', exif=exif_bytes, quality='web_medium')
    output.seek(0)
    return output.getvalue()


class ToonBondspasView(UserPassesTestMixin, View):

    """ Deze view kan de bondspas tonen, of een scherm met 'even wachten, we zoeken je pas op' """

    template_name = TEMPLATE_BONDSPAS_TONEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn. Rol is niet belangrijk.
        return rol_get_huidige(self.request) != Rollen.ROL_NONE

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        # bondspas wordt opgehaald nadat de pagina getoond kan worden
        context['url_dynamic'] = reverse('Bondspas:dynamic-ophalen')

        context['kruimels'] = (
            (None, 'Bondspas'),
        )

        # toon een pagina die wacht op de download
        menu_dynamics(request, context)
        return render(request, self.template_name, context)


class DynamicBondspasOphalenView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn. Rol is niet belangrijk.
        return rol_get_huidige(self.request) != Rollen.ROL_NONE

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de webpagina via een stukje javascript de bondspas ophaalt
            nadat de hele HTML binnen is en de pagina getoond kan worden.

            Dit is een POST by-design, om caching te voorkomen.
        """

        # bepaal het jaar voor de wedstrijdklasse
        now = timezone.localtime(timezone.now())
        jaar = now.year

        account = self.request.user
        lid_nr = account.username

        regels = maak_bondspas_regels(lid_nr, jaar)
        img_data = maak_bondspas_image(lid_nr, jaar, regels)

        # base64 is nodig voor img in html
        # alternatief is javascript laten tekenen op een canvas en base64 maken met dataToUrl
        out = dict()
        out['bondspas_base64'] = base64.b64encode(img_data).decode()

        return JsonResponse(out)


class ToonBondspasBeheerderView(UserPassesTestMixin, View):

    template_name = TEMPLATE_BONDSPAS_VAN_TONEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rollen.ROL_BB

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        try:
            lid_nr = kwargs['lid_nr'][:6]       # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
            _ = Sporter.objects.get(lid_nr=lid_nr)
        except Sporter.DoesNotExist:
            raise Http404('Geen valide parameter')

        # bepaal het jaar voor de wedstrijdklasse
        now = timezone.localtime(timezone.now())
        jaar = now.year

        regels = maak_bondspas_regels(lid_nr, jaar)
        img_data = maak_bondspas_image(lid_nr, jaar, regels)

        # base64 is nodig voor img in html
        context['bondspas_base64'] = base64.b64encode(img_data).decode()

        context['kruimels'] = (
            (reverse('Overig:activiteit'), 'Account activiteit'),
            (None, 'Bondspas tonen'),
        )

        menu_dynamics(request, context)
        return render(request, self.template_name, context)


# end of file
