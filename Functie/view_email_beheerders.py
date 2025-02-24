# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.models import Functie
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving

TEMPLATE_OVERZICHT_EMAILS_SEC_HWL = 'functie/emails-sec-hwl.dtl'
TEMPLATE_OVERZICHT_EMAILS_BEHEERDERS = 'functie/emails-beheerders.dtl'


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
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO):
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

        elif self.rol_nu == Rol.ROL_RKO:
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


class OverzichtEmailsCompetitieBeheerdersView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de BB, BKO, RKO en geeft een knip-en-plak-baar overzicht van
        van de e-mailadressen van alle RCLs.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT_EMAILS_BEHEERDERS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # alle competitie beheerders + HWL
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ, Rol.ROL_BKO, Rol.ROL_RKO)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ):
            # geef alle e-mailadressen
            context['geo_str'] = "van de BKO's, RKO's en RCL's Indoor en 25m1pijl"
            emails = (Functie
                      .objects
                      .filter(rol__in=('BKO', 'RKO', 'RCL'))
                      .exclude(bevestigde_email='')
                      .distinct('bevestigde_email')
                      .values_list('bevestigde_email', flat=True))
            alle = (Functie
                    .objects
                    .filter(rol__in=('BKO', 'RKO', 'RCL'))
                    .exclude(bevestigde_email='')
                    .order_by('comp_type',
                              'rol',
                              'rayon__rayon_nr',
                              'regio__regio_nr'))

        elif self.rol_nu == Rol.ROL_BKO:
            # geef e-mailadressen RKO + RCL voor specifieke competitie
            context['geo_str'] = "van de RKO's en RCL's"
            if self.functie_nu.is_indoor():
                context['geo_str'] += ' van de Indoor'
            else:
                context['geo_str'] += ' van de 25m1pijl'

            emails = (Functie
                      .objects
                      .filter(rol__in=('RKO', 'RCL'),
                              comp_type=self.functie_nu.comp_type)
                      .exclude(bevestigde_email='')
                      .distinct('bevestigde_email')
                      .values_list('bevestigde_email', flat=True))
            alle = (Functie
                    .objects
                    .filter(rol__in=('RKO', 'RCL'),
                            comp_type=self.functie_nu.comp_type)
                    .exclude(bevestigde_email='')
                    .order_by('rayon__rayon_nr',
                              'regio__regio_nr'))

        else:   # self.rol_nu == Rollen.ROL_RKO:
            # geef e-mailadressen RCL voor specifieke competitie
            context['geo_str'] = "van de RCL's"
            rayon_nr = self.functie_nu.rayon.rayon_nr
            if self.functie_nu.is_indoor():
                context['geo_str'] += ' van de Indoor in Rayon %s' % rayon_nr
            else:
                context['geo_str'] += ' van de 25m1pijl in Rayon %s' % rayon_nr

            emails = (Functie
                      .objects
                      .filter(rol='RCL',
                              comp_type=self.functie_nu.comp_type,
                              regio__rayon_nr=rayon_nr)
                      .exclude(bevestigde_email='')
                      .distinct('bevestigde_email')
                      .values_list('bevestigde_email', flat=True))
            alle = (Functie
                    .objects
                    .filter(rol='RCL',
                            comp_type=self.functie_nu.comp_type,
                            regio__rayon_nr=rayon_nr)
                    .exclude(bevestigde_email='')
                    .order_by('regio__regio_nr',
                              'comp_type'))

        context['aantal'] = len(emails)
        context['emails'] = "; ".join(emails)
        context['alle'] = alle

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Functie:lijst-beheerders'), 'Beheerders'),
            (None, 'E-mailadressen beheerders')
        )

        return context


# end of file
