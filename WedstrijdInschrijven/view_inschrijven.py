# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.db.models import ObjectDoesNotExist
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bestelling.operations import bestel_mutatieverzoek_inschrijven_wedstrijd, mandje_tel_inhoud
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Kalender.definities import MAAND2URL
from Sporter.models import SporterBoog
from Wedstrijden.models import Wedstrijd, WedstrijdInschrijving
from WedstrijdInschrijven.helpers import inschrijving_open_of_404

TEMPLATE_WEDSTRIJDEN_TOEGEVOEGD_AAN_MANDJE = 'wedstrijdinschrijven/inschrijven-toegevoegd-aan-mandje.dtl'


class ToevoegenAanMandjeView(UserPassesTestMixin, View):

    """ Met deze view wordt het toevoegen van een wedstrijd aan het mandje van de koper afgehandeld """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rol.ROL_NONE

    def post(self, request, *args, **kwargs):
        wedstrijd_str = request.POST.get('wedstrijd', '')[:7]       # afkappen voor de veiligheid
        sporterboog_str = request.POST.get('sporterboog', '')[:7]   # afkappen voor de veiligheid
        sessie_str = request.POST.get('sessie', '')[:7]             # afkappen voor de veiligheid
        klasse_str = request.POST.get('klasse', '')[:7]             # afkappen voor de veiligheid
        goto_str = request.POST.get('goto', '')[:7]                 # afkappen voor de veiligheid

        try:
            wedstrijd_pk = int(wedstrijd_str)
            sporterboog_pk = int(sporterboog_str)
            sessie_pk = int(sessie_str)
            klasse_pk = int(klasse_str)
        except (ValueError, TypeError):
            raise Http404('Slecht verzoek')

        try:
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
            sessie = wedstrijd.sessies.get(pk=sessie_pk)
            klasse = sessie.wedstrijdklassen.get(pk=klasse_pk)
            sporterboog = (SporterBoog
                           .objects
                           .select_related('sporter',
                                           'sporter__bij_vereniging')
                           .get(pk=sporterboog_pk))
        except ObjectDoesNotExist:
            raise Http404('Onderdeel van verzoek niet gevonden')

        inschrijving_open_of_404(wedstrijd)

        sporter = sporterboog.sporter
        if sporter.is_overleden or not sporter.is_actief_lid or not sporter.bij_vereniging:
            raise Http404('Niet actief lid')

        account_koper = get_account(request)

        now = timezone.now()
        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan het mandje van %s\n" % (stamp_str, account_koper.get_account_full_name())

        # maak de inschrijving aan
        inschrijving = WedstrijdInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=klasse,
                            sporterboog=sporterboog,
                            koper=account_koper,
                            log=msg)

        try:
            # voorkom dubbele records
            with transaction.atomic():
                inschrijving.save()
        except IntegrityError:          # pragma: no cover
            # er is niet voldaan aan de uniqueness constraint (sessie, sporterboog)
            # ga uit van user-error (dubbelklik op knop) en skip de rest gewoon
            pass
        else:
            # zet dit verzoek door naar de achtergrondtaak
            snel = str(request.POST.get('snel', ''))[:1]
            bestel_mutatieverzoek_inschrijven_wedstrijd(account_koper, inschrijving, snel == '1')

            mandje_tel_inhoud(self.request, account_koper)

            if wedstrijd.eis_kwalificatie_scores:
                url = reverse('WedstrijdInschrijven:inschrijven-kwalificatie-scores',
                              kwargs={'inschrijving_pk': inschrijving.pk})
                return HttpResponseRedirect(url)

        # render de pagina "toegevoegd aan mandje"

        context = dict()

        wedstrijd = inschrijving.wedstrijd
        sporterboog = inschrijving.sporterboog

        url_maand = reverse('Kalender:simpel',
                            kwargs={'jaar_of_maand': 'maand',
                                    'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})

        inschrijven_str = 'Inschrijven'
        url = reverse('Wedstrijden:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk})

        if goto_str == 'S':
            inschrijven_str += ' Sporter'

        elif goto_str == 'G':
            inschrijven_str += ' Groepje'

        elif goto_str == 'F':
            inschrijven_str += ' Familie'
            # ga terug naar de familie pagina met dezelfde sporter geselecteerd
            url = reverse('WedstrijdInschrijven:inschrijven-familie-lid-boog',
                          kwargs={'wedstrijd_pk': wedstrijd.pk,
                                  'lid_nr': sporterboog.sporter.lid_nr,
                                  'boog_afk': sporterboog.boogtype.afkorting.lower()})

        context['url_verder'] = url
        context['url_mandje'] = reverse('Bestelling:toon-inhoud-mandje')

        context['kruimels'] = (
            (url_maand, 'Wedstrijdkalender'),
            (reverse('Wedstrijden:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (url, inschrijven_str),
            (None, 'Toegevoegd aan mandje')
        )

        return render(request, TEMPLATE_WEDSTRIJDEN_TOEGEVOEGD_AAN_MANDJE, context)


# end of file
