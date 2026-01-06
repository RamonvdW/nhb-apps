# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning QR codes voor OTP controle """

from django.conf import settings
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from qrcode.main import QRCode
from qrcode.image.svg import SvgPathImage
import xml.etree.ElementTree as Tree
import logging
import pyotp
import io

my_logger = logging.getLogger('MH.Account')


# the QR code versie bepaalt het aantal data plekken in de code
# zie qrcode.com/en/about/version.html voor het bepalen van de juiste versie
#
# uri formaat: 'otpauth://totp/ISSUER:ACCOUNT?secret=SECRET&issuer=ISSUER'
#
# we hebben ~132 tekens nodig:
#  - account naam (typisch 6 tekens, max 50 tekens)
#  - issue name = website URL (~30 tekens, max 50 tekens), komt 2x voor
#  - otp secret (32 tekens)
#  - uri overhead toe (~32 tekens)
#
# met account=6 en issuer=30 --> 6 + 30 + 30 + 32 + 32 = 130 tekens
#
# versie 7, medium ECC: 122 bytes --> 45x45 image
# versie 8, medium ECC: 152 bytes --> 49x49 image
QRCODE_VERSION = 8


class SvgEmbeddedInHtmlImage(SvgPathImage):
    def _write(self, stream):
        Tree.ElementTree(self._img).write(stream,
                                          encoding="utf-8",
                                          xml_declaration=False,
                                          default_namespace=None,
                                          method='html')


def make_qr_code_image(text):
    """
    Generates an image object (from the qrcode library) representing the QR code for the given text.
    Any invalid argument is silently converted into the default value for that argument.
    """
    qr = QRCode(
                version=QRCODE_VERSION,
                image_factory=SvgEmbeddedInHtmlImage,
                box_size=12, border=1)      # controls SVG image size
    qr.add_data(force_str(text))
    return qr.make_image()


def qrcode_get(account):
    """ Genereer een QR code voor het account
        de QR code wordt als html-embedded SVG plaatje terug gegeven
    """
    otp = pyotp.TOTP(account.otp_code)
    uri = otp.provisioning_uri(name=account.username,
                               issuer_name=settings.OTP_ISSUER_NAME)

    if len(uri) > 150:
        my_logger.error('Account.operations.maak_qrcode: te lange uri (%s): %s' % (len(uri), repr(uri)))

    stream = io.BytesIO()
    make_qr_code_image(uri).save(stream, kind="SVG")
    html = stream.getvalue().decode('utf-8')
    return mark_safe(html)

# end of file
