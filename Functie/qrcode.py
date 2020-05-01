# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning QR codes voor OTP controle """

from django.conf import settings
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
import io
import pyotp
import qrcode
from qrcode.image.svg import SvgPathImage
import xml.etree.ElementTree as ET


# the QR code versie bepaalt het aantal data plekken in de code
# zie qrcode.com/en/about/version.html voor het bepalen van de juiste versie
#
# we hebben nodig: account naam (max 50 tekens) + website URL (max 50 tekens) = 100 tekens
# de URI encoding voegt nog wat overhead toe (~20 tekens)
#
# versie 7, medium ECC: 122 bytes --> 45x45 image
# versie 8, medium ECC: 152 bytes --> 49x49 image
QRCODE_VERSION = 8


class SvgEmbeddedInHtmlImage(SvgPathImage):
    def _write(self, stream):
        self._img.append(self.make_path())
        ET.ElementTree(self._img).write(stream,
                                        encoding="utf-8",
                                        xml_declaration=False,
                                        default_namespace=None,
                                        method='html')


def make_qr_code_image(text):
    """
    Generates an image object (from the qrcode library) representing the QR code for the given text.
    Any invalid argument is silently converted into the default value for that argument.
    """
    qr = qrcode.QRCode(
                version=QRCODE_VERSION,
                image_factory=SvgEmbeddedInHtmlImage)
    qr.add_data(force_text(text))
    return qr.make_image()


def qrcode_get(account):
    """ Genereer een QR code voor het account
        de QR code wordt als html-embedded SVG plaatje terug gegeven
    """
    uri = pyotp.TOTP(account.otp_code).provisioning_uri(name=account.username,
                                                        issuer_name=settings.OTP_ISSUER_NAME)
    #print("provisioning uri: %s" % repr(uri))
    stream = io.BytesIO()
    make_qr_code_image(uri).save(stream, kind="SVG")
    html = stream.getvalue().decode('utf-8')
    return mark_safe(html)

# end of file
