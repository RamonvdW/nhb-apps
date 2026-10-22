# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from DataApi.models import DataApiLidmaatschap
from DataApi.operations import dataapi_opschonen
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer
import datetime


class TestDataApiOpschonen(E2EHelpers, TestCase):

    """ tests voor de DataApi applicatie, operation opschonen """

    def setUp(self):
        pass

    def test_opschonen(self):
        now = datetime.datetime.now()
        last_week = now - datetime.timedelta(days=7)
        historical = now - datetime.timedelta(days=settings.DDI_LMS_KEEP_HISTORY_DAYS + 2)

        out = OutputBuffer()
        dataapi_opschonen(out)
        self.assertTrue("[INFO] Opschonen DataApi: 0 lidmaatschappen worden verwijderd" in out.getvalue())

        # maak een actief lms, dat moet blijven
        DataApiLidmaatschap.objects.create(
                lid_nr=100002,
                ver_nr=1000,
                aanmeld_datum='2000-01-01',
                afmeld_datum='',
                geboorte_datum='01-01-1990',
                geslacht='V',
                land_iso='NL',
                postcode='4444CC')

        DataApiLidmaatschap.objects.all().update(mutatie_datum='1900-01-01')
        out = OutputBuffer()
        dataapi_opschonen(out)
        self.assertTrue("[INFO] Opschonen DataApi: 0 lidmaatschappen worden verwijderd" in out.getvalue())

        # maak recent afgelopen lms, dat moet blijven
        DataApiLidmaatschap.objects.create(
                lid_nr=100003,
                ver_nr=1000,
                aanmeld_datum='2000-01-01',
                afmeld_datum=last_week.strftime('%Y-%m-%d'),
                geboorte_datum='01-01-1990',
                geslacht='V',
                land_iso='NL',
                postcode='4444CC')

        DataApiLidmaatschap.objects.all().update(mutatie_datum='1900-01-01')
        out = OutputBuffer()
        dataapi_opschonen(out)
        self.assertTrue("[INFO] Opschonen DataApi: 0 lidmaatschappen worden verwijderd" in out.getvalue())

        # maak een record dat verwijderd kan worden, maar is recent nog gewijzigd, dus blijft
        DataApiLidmaatschap.objects.create(
                lid_nr=100004,
                ver_nr=1000,
                aanmeld_datum='2000-01-01',
                afmeld_datum=historical.strftime('%Y-%m-%d'),
                geboorte_datum='01-01-1990',
                geslacht='V',
                land_iso='NL',
                postcode='4444CC')

        # mutatiedatum houdt verwijderen tegen
        out = OutputBuffer()
        dataapi_opschonen(out)
        self.assertTrue("[INFO] Opschonen DataApi: 0 lidmaatschappen worden verwijderd" in out.getvalue())

        # zet de mutatiedatum terug: nu wordt het record echt verwijderd
        DataApiLidmaatschap.objects.all().update(mutatie_datum='1900-01-01')
        out = OutputBuffer()
        dataapi_opschonen(out)
        self.assertTrue("[INFO] Opschonen DataApi: 1 lidmaatschappen worden verwijderd" in out.getvalue())


# end of file
