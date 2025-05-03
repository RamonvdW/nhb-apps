# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Kind of mandatory customization, otherwise staticfiles.json will be written in STATIC_ROOT
    but read from whatever current working directory the webserver.
"""

from django.conf import settings
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage, StaticFilesStorage
import os


class MHManifestStaticFilesStorage(ManifestStaticFilesStorage):

    def __init__(self, *args, **kwargs):
        static_dir = os.path.join(settings.APPS_DIR, settings.STATIC_ROOT)
        manifest_storage = StaticFilesStorage(location=static_dir)
        super().__init__(*args, manifest_storage=manifest_storage, **kwargs)


# end of file
