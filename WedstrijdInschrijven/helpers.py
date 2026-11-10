# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.utils import timezone
from datetime import timedelta

def inschrijving_open_of_404(wedstrijd):
    """ Controleer dat de wedstrijd nog open is voor inschrijving.
        Zo niet, genereer dan fout 404
    """

    if wedstrijd.extern_beheerd:
        raise Http404('Externe inschrijving')

    now_date = timezone.now().date()
    wedstrijd.inschrijven_voor = wedstrijd.datum_begin - timedelta(days=wedstrijd.inschrijven_tot)
    is_voor_sluitingsdatum = now_date < wedstrijd.inschrijven_voor

    if not is_voor_sluitingsdatum:
        raise Http404('Inschrijving is gesloten')


# end of file
