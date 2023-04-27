# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views import View


class SiteTijdelijkeUrlView(View):
    """ Op deze view komen de tijdelijke url's uit
        We dispatchen naar de juiste afhandelaar
    """

    @staticmethod
    def get(request, *args, **kwargs):
        # TODO: verwijder deze tijdelijke backwards compatibiliteit in v20 of later
        url_code = kwargs['code']
        url = reverse('TijdelijkeCodes:tijdelijke-url', kwargs={'code': url_code})
        return HttpResponseRedirect(url)

# end of file
