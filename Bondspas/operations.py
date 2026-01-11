# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.utils.formats import date_format
from BasisTypen.definities import GESLACHT_ANDERS
from Bondspas.models import BondspasJaar
from Opleiding.models import OpleidingDiploma
from Sporter.leeftijdsklassen import (bereken_leeftijdsklasse_wa,
                                      bereken_leeftijdsklasse_khsn,
                                      bereken_leeftijdsklasse_ifaa)
from Sporter.operations import get_sporter_voorkeuren
from PIL import Image, ImageFont, ImageDraw
from PIL.TiffImagePlugin import ImageFileDirectory_v2
import datetime
import io
from os import path as os_path


EXIF_TAG_COPYRIGHT = 0x8298
EXIF_TAG_TITLE = 0x010D     # DocumentName
# EXIF_TAG_TITLE = 0x010E     # ImageDescription


def bepaal_jaar_bondspas() -> int:
    """ bepaal het jaar voor op de bondspas """

    # bondspas is het nieuwste jaar
    bondspas = (BondspasJaar
                .objects
                .exclude(zichtbaar=False)
                .order_by('-jaar')        # hoogste eerst
                .first())
    if bondspas:
        # gevonden
        jaar_pas = bondspas.jaar
    else:
        # niet gevonden
        # toon de pas van vorige jaar
        now = timezone.localtime(timezone.now())
        jaar_pas = now.year - 1

    return jaar_pas


def maak_bondspas_regels(sporter, jaar_pas):
    """ Bepaal de regels tekst die op de bondspas moeten komen voor deze specifieke sporter
    """
    regels = []

    voorkeur = get_sporter_voorkeuren(sporter)

    regels.append(("lid_nr", str(sporter.lid_nr)))      # moet [0] zijn
    regels.append(("WA_id", sporter.wa_id))             # moet [1] zijn

    if sporter.is_erelid:
        regels.append(("Speciale status", "Erelid"))

    regels.append(("Naam", "%s (%s)" % (sporter.volledige_naam(), sporter.geslacht)))
    regels.append(("Geboortedatum", date_format(sporter.geboorte_datum, "j F Y")))

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
    prev_cat_disc = None
    for sterkte in sporter.speelsterkte_set.order_by('volgorde'):    # laagste eerst = beste eerst
        cat_disc = sterkte.discipline
        if sterkte.category == 'Cadet':
            # toon cadet codes totdat er een senior code geregistreerd is
            cat_disc += 'Senior'
        else:
            cat_disc += sterkte.category    # Senior / Master

        if cat_disc != prev_cat_disc:
            if sterkte.volgorde >= 600:
                afkortingen_basis.append(sterkte.pas_code)
            else:
                afkortingen.append(sterkte.pas_code)
            prev_cat_disc = cat_disc
    # for

    # toon de basis codes alleen als er geen hogere codes zijn
    # iemand met "meesterschutter" hoeft geen beginner-awards meer te zien
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

    wedstrijdleeftijd_wa = sporter.bereken_wedstrijdleeftijd_wa(jaar_pas)

    wedstrijd_datum = datetime.date(year=jaar_pas,
                                    month=sporter.geboorte_datum.month,
                                    day=sporter.geboorte_datum.day)
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

    regels.append(('Wedstrijdklassen', ''))     # sectie titel

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


def plaatje_teken_barcode(lid_nr, draw, begin_x, end_y, font):
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


def plaatje_teken(jaar_pas, regels):

    fpath = os_path.join(settings.INSTALL_PATH, 'Bondspas', 'files', 'achtergrond_bondspas-%s.jpg' % jaar_pas)
    image = Image.open(fpath)

    _, _, width, height = image.getbbox()
    # standard size = 1418 x 2000

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(settings.BONDSPAS_FONT, size=40)
    font_bold = ImageFont.truetype(settings.BONDSPAS_FONT_BOLD, size=45)
    font_bold_groter = ImageFont.truetype(settings.BONDSPAS_FONT_BOLD, size=55)
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

    wa_id_x = lid_nr_x = witte_kader_x1
    wa_id_y = witte_kader_y_midden + 25

    if len(wa_id):
        lid_nr_y = witte_kader_y_midden - 25
    else:
        lid_nr_y = witte_kader_y_midden

    # bondsnummer
    # text anchors: https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
    lid_nr_width = draw.textlength("Bondsnummer: ", font=font)
    draw.text((lid_nr_x, lid_nr_y),
              "Bondsnummer: ", color_black, font=font, anchor="lb")
    draw.text((lid_nr_x + lid_nr_width, lid_nr_y+5),
              lid_nr, color_black, font=font_bold_groter, anchor="lb")

    # WA id
    if len(wa_id):
        draw.text((wa_id_x, wa_id_y),
                  "World Archery ID: " + wa_id, color_black, font=font, anchor="lt")

    # barcode
    # 480 plaatst deze midden boven de logo's van WA en IFAA
    plaatje_teken_barcode(lid_nr, draw, witte_kader_x2 - 480, witte_kader_y_midden + 70, font)

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

        if header.startswith("Wedstrijdklassen"):
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

        if header.startswith("Wedstrijdklassen"):
            wkl = True
    # for

    return image


def maak_bondspas_jpeg_en_pdf(jaar_pas, lid_nr, regels):

    image = plaatje_teken(jaar_pas, regels)

    # maak de JPEG
    ifd = ImageFileDirectory_v2()
    ifd[EXIF_TAG_COPYRIGHT] = "Koninklijke HandboogSport Nederland (KHSN)"
    ifd[EXIF_TAG_TITLE] = "Bondspas %s voor lid %s" % (jaar_pas, lid_nr)

    exif_out = io.BytesIO()
    ifd.save(exif_out)
    exif_bytes = b"Exif\x00\x00" + exif_out.getvalue()

    jpeg = io.BytesIO()
    image.save(
            jpeg,
            format='JPEG',
            exif=exif_bytes,
            quality='web_medium')
    jpeg.seek(0)
    out_jpeg = jpeg.getvalue()

    # maak de PDF
    px_w, px_h = image.size
    # height = 2000 pixels
    # target: A6 = 105 x 148 mm == 1.434 x 5.827 inch
    # resolution in dpi = 2000 / 5.827
    dpi = px_h / (148 / 25.4)  # 25.4 = mm to inches
    pdf = io.BytesIO()
    image.save(
            pdf,
            format="PDF",
            resolution=dpi,
            title="Bondspas %s" % jaar_pas,
            author="Koninklijke HandboogSport Nederland (KHSN) - www.handboogsport.nl",
            creator="%s - %s" % (settings.AFSCHRIFT_SITE_NAAM, settings.AFSCHRIFT_SITE_URL),
            subject="Bondspas %s voor lid %s" % (jaar_pas, lid_nr))
    pdf.seek(0)
    out_pdf = pdf.getvalue()

    return out_jpeg, out_pdf


# end of file
