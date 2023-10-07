# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rollen
from Functie.models import Functie
from Functie.rol import rol_get_huidige_functie

TEMPLATE_OVERZICHT_EMAILS_SEC_HWL = 'functie/emails-sec-hwl.dtl'
TEMPLATE_OVERZICHT_EMAILS_RCL = 'functie/emails-rcl.dtl'


class OverzichtEmailsSecHwlView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de BB, MHZ, BKO, RKO en RCLs en geeft een knip-en-plak-baar overzicht van
        de lidnummers van alle SEC en HWL, zodat hier makkelijk een mailing voor te maken is.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT_EMAILS_SEC_HWL
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # alle competitie beheerders + HWL
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_MWZ, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            context['geo_str'] = ''
            emails = (Functie
                      .objects
                      .filter(rol__in=('HWL', 'SEC'))
                      .exclude(bevestigde_email='')
                      .values_list('bevestigde_email', flat=True))
            alle = (Functie
                    .objects
                    .filter(rol__in=('HWL', 'SEC'))
                    .exclude(bevestigde_email='')
                    .select_related('vereniging')
                    .order_by('vereniging__ver_nr',
                              'rol'))

        elif self.rol_nu == Rollen.ROL_RKO:
            rayon_nr = self.functie_nu.rayon.rayon_nr
            context['geo_str'] = ' in Rayon %s' % rayon_nr
            emails = (Functie
                      .objects
                      .filter(rol__in=('HWL', 'SEC'),
                              vereniging__regio__rayon_nr=rayon_nr)
                      .exclude(bevestigde_email='')
                      .values_list('bevestigde_email', flat=True))
            alle = (Functie
                    .objects
                    .filter(rol__in=('HWL', 'SEC'),
                            vereniging__regio__rayon_nr=rayon_nr)
                    .exclude(bevestigde_email='')
                    .select_related('vereniging')
                    .order_by('vereniging__ver_nr',
                              'rol'))

        else:  # elif self.rol_nu == Rollen.ROL_RCL:
            regio_nr = self.functie_nu.regio.regio_nr
            context['geo_str'] = ' in regio %s' % regio_nr
            emails = (Functie
                      .objects
                      .filter(rol__in=('HWL', 'SEC'),
                              vereniging__regio__regio_nr=regio_nr)
                      .exclude(bevestigde_email='')
                      .values_list('bevestigde_email', flat=True))
            alle = (Functie
                    .objects
                    .filter(rol__in=('HWL', 'SEC'),
                            vereniging__regio__regio_nr=regio_nr)
                    .exclude(bevestigde_email='')
                    .select_related('vereniging')
                    .order_by('vereniging__ver_nr',
                              'rol'))

        context['aantal'] = len(emails)
        context['emails'] = "; ".join(emails)
        context['alle'] = alle

        context['kruimels'] = (
            (reverse('Vereniging:lijst'), 'Verenigingen'),
            (None, 'E-mailadressen SEC en HWL')
        )

        return context


class OverzichtEmailsRclView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de BB, BKO, RKO en geeft een knip-en-plak-baar overzicht van
        van de e-mailadressen van alle RCLs.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT_EMAILS_RCL
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # alle competitie beheerders + HWL
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_MWZ, Rollen.ROL_BKO, Rollen.ROL_RKO)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_MWZ, Rollen.ROL_BKO):
            context['geo_str'] = ''
            emails = (Functie
                      .objects
                      .filter(rol='RCL')
                      .exclude(bevestigde_email='')
                      .distinct('bevestigde_email')
                      .values_list('bevestigde_email', flat=True))
            alle = (Functie
                    .objects
                    .filter(rol='RCL')
                    .exclude(bevestigde_email='')
                    .order_by('regio__regio_nr',
                              'comp_type'))

        else:   # self.rol_nu == Rollen.ROL_RKO:
            rayon_nr = self.functie_nu.rayon.rayon_nr
            context['geo_str'] = ' in Rayon %s' % rayon_nr
            emails = (Functie
                      .objects
                      .filter(rol='RCL',
                              regio__rayon_nr=rayon_nr)
                      .exclude(bevestigde_email='')
                      .distinct('bevestigde_email')
                      .values_list('bevestigde_email', flat=True))
            alle = (Functie
                    .objects
                    .filter(rol='RCL',
                            regio__rayon_nr=rayon_nr)
                    .exclude(bevestigde_email='')
                    .order_by('regio__regio_nr',
                              'comp_type'))

        context['aantal'] = len(emails)
        context['emails'] = "; ".join(emails)
        context['alle'] = alle

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Functie:overzicht'), 'Beheerders'),
            (None, 'E-mailadressen RCLs')
        )

        return context


# end of file
