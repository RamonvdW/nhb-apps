# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Kind of mandatory customization, otherwise staticfiles.json will be written in STATIC_ROOT
    but read from whatever current working directory the webserver.
"""

from django.conf import settings
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage, StaticFilesStorage
from django.templatetags.static import static
import os


class MHManifestStaticFilesStorage(ManifestStaticFilesStorage):

    def __init__(self, *args, **kwargs):
        static_dir = os.path.join(settings.APPS_DIR, settings.STATIC_ROOT)
        manifest_storage = StaticFilesStorage(location=static_dir)
        super().__init__(*args, manifest_storage=manifest_storage, **kwargs)


def static_safe(resource: str) -> str:
    """ geef een url terug naar de static resource
        in:  'app/static/resource' of 'webwinkel_fotos/resource'
        out: '/static/sub/resource.hash'
    """

    try:
        url = static(resource)
    except ValueError:
        # hier komen als ManifestStaticFilesStorage de resource niet herkend
        url = static('plein/oeps.webp')

    return url


# end of file
