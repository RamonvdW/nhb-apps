# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.models import RegiocompetitieSporterBoog
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Sporter.operations import get_sporter


class SporterVoorkeurRkView(UserPassesTestMixin, TemplateView):

    """ Hiermee kan de sporter zijn voorkeur voor het RK instellen. """

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rol.ROL_SPORTER

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de sporter op de knop drukt om
            zijn voorkeur voor het RK aan te passen """

        account = get_account(request)
        sporter = get_sporter(account)

        keuze = request.POST.get('keuze', '?')[:1]      # afkappen voor de veiligheid
        pk = request.POST.get('deelnemer', '?')[:7]     # afkappen voor de veiligheid

        try:
            pk = int(pk)
            deelnemer = RegiocompetitieSporterBoog.objects.get(pk=pk, sporterboog__sporter=sporter)
        except (ValueError, TypeError, RegiocompetitieSporterBoog.DoesNotExist):
            raise Http404('Niet gevonden')

        # check competitie fase
        comp = deelnemer.regiocompetitie.competitie
        comp.bepaal_fase()
        if comp.fase_indiv > 'G':
            raise Http404('Mag niet wijzigen')

        now = timezone.now()
        when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        if keuze == 'N':
            # sporter wil niet meedoen
            if deelnemer.inschrijf_voorkeur_rk_bk:
                msg = '[%s] Voorkeur RK aangepast door sporter: niet meedoen\n' % when_str
                deelnemer.inschrijf_voorkeur_rk_bk = False
                deelnemer.logboekje += msg
                deelnemer.save(update_fields=['inschrijf_voorkeur_rk_bk', 'logboekje'])

        elif keuze == 'J':
            # sporter wil wel meedoen
            if not deelnemer.inschrijf_voorkeur_rk_bk:
                msg = '[%s] Voorkeur RK aangepast door sporter: wel meedoen\n' % when_str
                deelnemer.inschrijf_voorkeur_rk_bk = True
                deelnemer.logboekje += msg
                deelnemer.save(update_fields=['inschrijf_voorkeur_rk_bk', 'logboekje'])

        url = reverse('Sporter:profiel')
        return HttpResponseRedirect(url)


# end of file
