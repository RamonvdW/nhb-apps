# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.db.models import Count
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving
from Functie.models import Functie
from Locatie.definities import BAAN_TYPE_BUITEN, BAAN_TYPE_EXTERN, BAANTYPE2STR
from Vereniging.models import Vereniging, Secretaris

TEMPLATE_LIJST = 'vereniging/lijst.dtl'
TEMPLATE_LIJST_DETAILS = 'vereniging/lijst-details.dtl'

TEMPLATE_CONTACT_GEEN_BEHEERDERS = 'vereniging/contact-geen-beheerders.dtl'


class LijstView(UserPassesTestMixin, TemplateView):

    """ Via deze view worden kan
            de BB een lijst van alle verenigingen zien
            een BKO, RKO of RCL de lijst van verenigingen zien, in zijn werkgebied
            de SEC, HWL of WL een lijst van verenigingen in hun regio zien
    """

    template_name = TEMPLATE_LIJST
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.is_staff = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)

        if self.rol_nu == Rol.ROL_BB:
            account = get_account(self.request)
            self.is_staff = account.is_staff

        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ, Rol.ROL_MO, Rol.ROL_CS,
                               Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                               Rol.ROL_HWL, Rol.ROL_SEC)

    def _get_verenigingen(self):

        # vul een kleine cache om vele database verzoeken te voorkomen
        hwl_functies = dict()   # [ver_nr] = Functie()
        functie2count = dict()  # [functie.pk] = aantal
        for functie in (Functie
                        .objects
                        .select_related('vereniging')
                        .annotate(accounts_count=Count('accounts'))
                        .all()):
            if functie.rol == 'HWL':
                hwl_functies[functie.vereniging.ver_nr] = functie

            functie2count[functie.pk] = functie.accounts_count
        # for

        if self.rol_nu == Rol.ROL_RKO:
            # toon de lijst van verenigingen in het rayon van de RKO
            # het rayonnummer is verkrijgbaar via de regiocompetitie van de functie
            return (Vereniging
                    .objects
                    .select_related('regio',
                                    'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .filter(regio__rayon=self.functie_nu.rayon)
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('regio__regio_nr',
                              'ver_nr'))

        if self.rol_nu == Rol.ROL_BB and self.is_staff:
            # landelijke lijst + telling aantal leden
            objs = (Vereniging
                    .objects
                    .select_related('regio',
                                    'regio__rayon')
                    .prefetch_related('wedstrijdlocatie_set',
                                      'functie_set',
                                      'clusters')
                    .annotate(sporter_set_count=Count('sporter'))
                    .order_by('regio__regio_nr',
                              'ver_nr'))

            for obj in objs:
                obj.aantal_leden = obj.sporter_set_count
                obj.aantal_beheerders = 0
                for functie in obj.functie_set.all():
                    obj.aantal_beheerders += functie2count[functie.pk]
                # for
            # for
            return objs

        if self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO, Rol.ROL_MWZ, Rol.ROL_MO, Rol.ROL_CS):
            # toon de landelijke lijst)
            return (Vereniging
                    .objects
                    .select_related('regio',
                                    'regio__rayon')
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('regio__regio_nr',
                              'ver_nr'))

        # toon de lijst van verenigingen in de regio
        if self.rol_nu == Rol.ROL_RCL:
            # het regionummer is verkrijgbaar via de regiocompetitie van de functie
            objs = (Vereniging
                    .objects
                    .filter(regio=self.functie_nu.regio)
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('ver_nr'))
        else:
            # rol_nu == Rollen.ROL_HWL / ROL_SEC
            # het regionummer is verkrijgbaar via de vereniging
            objs = (Vereniging
                    .objects
                    .filter(regio=self.functie_nu.vereniging.regio)
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('ver_nr'))

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toon_rayon'] = True
        context['toon_regio'] = True
        context['toon_cluster'] = False
        context['toon_details'] = True
        context['toon_ledental'] = self.is_staff

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['landelijk'] = self.rol_nu in (Rol.ROL_BB, Rol.ROL_BKO)

        if self.rol_nu == Rol.ROL_BB:
            context['contact_geen_beheerders'] = reverse('Vereniging:contact-geen-beheerders')

        if self.rol_nu == Rol.ROL_RKO:
            context['toon_rayon'] = False

        if self.rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL, Rol.ROL_SEC):
            context['toon_rayon'] = False
            context['toon_regio'] = False

        context['verenigingen'] = verenigingen = self._get_verenigingen()

        # voeg de url toe voor de "details" knoppen
        for ver in verenigingen:

            ver.details_url = reverse('Vereniging:lijst-details',
                                      kwargs={'ver_nr': ver.ver_nr})

            for loc in (ver
                        .wedstrijdlocatie_set           # FUTURE: kost een query -> aparte ophalen in dict
                        .exclude(zichtbaar=False)):
                if loc.baan_type == BAAN_TYPE_EXTERN:
                    ver.heeft_externe_locaties = True
                elif loc.baan_type == BAAN_TYPE_BUITEN:
                    ver.buiten_locatie = loc
                else:
                    ver.locatie = loc
            # for

            ver.cluster_letters = ''

            if ver.clusters.count() > 0:
                context['toon_cluster'] = True
                letters = [cluster.letter for cluster in ver.clusters.all()]
                letters.sort()
                ver.cluster_letters = ",".join(letters)

                if not context['toon_regio']:
                    # verander in 101a,b
                    ver.cluster_letters = str(ver.regio.regio_nr) + ver.cluster_letters
        # for

        if self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ, Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL):
            context['url_sec_hwl'] = reverse('Functie:emails-sec-hwl')

        context['kruimels'] = (
            (None, 'Verenigingen'),
        )

        return context


class DetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van een locatie gewijzigd worden """

    # class variables shared by all instances
    template_name = TEMPLATE_LIJST_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ,
                               Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                               Rol.ROL_HWL, Rol.ROL_WL, Rol.ROL_SEC)

    @staticmethod
    def _get_vereniging_locaties_or_404(**kwargs):
        try:
            ver_nr = int(kwargs['ver_nr'][:6])    # afkappen voor de veiligheid
            ver = Vereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        except Vereniging.DoesNotExist:
            raise Http404('Geen valide vereniging')

        clusters = list()
        for cluster in ver.clusters.order_by('letter').all():
            clusters.append(str(cluster))
        # for
        if len(clusters) > 0:
            ver.sorted_cluster_names = clusters

        # zoek de locaties erbij
        binnen_locatie = None
        buiten_locatie = None
        externe_locaties = list()
        for loc in ver.wedstrijdlocatie_set.exclude(zichtbaar=False):
            if loc.baan_type == BAAN_TYPE_EXTERN:
                externe_locaties.append(loc)
            elif loc.baan_type == BAAN_TYPE_BUITEN:
                buiten_locatie = loc
            else:
                # BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT, BAAN_TYPE_BINNEN_BUITEN of BAAN_TYPE_ONBEKEND
                binnen_locatie = loc
        # for

        return binnen_locatie, buiten_locatie, externe_locaties, ver

    @staticmethod
    def get_all_names(functie):
        return [account.volledige_naam() for account in functie.accounts.all()]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        binnen_locatie, buiten_locatie, externe_locaties, ver = self._get_vereniging_locaties_or_404(**kwargs)
        context['locatie'] = binnen_locatie
        context['buiten_locatie'] = buiten_locatie
        context['externe_locaties'] = externe_locaties
        context['ver'] = ver

        for locatie in externe_locaties:
            locatie.geen_naam = locatie.naam.strip() == ""
            locatie.geen_plaats = locatie.plaats.strip() == ""
            locatie.geen_disciplines = locatie.disciplines_str() == ""
        # for

        # zoek de beheerders erbij
        qset = Functie.objects.filter(vereniging=ver).prefetch_related('accounts')
        try:
            functie_sec = qset.filter(rol='SEC')[0]
        except IndexError:
            # only in autotest environment
            raise Http404('Rol ontbreekt')

        if ver.is_extern:
            functie_hwl = functie_wl = None
        else:
            try:
                functie_hwl = qset.filter(rol='HWL')[0]
                functie_wl = qset.filter(rol='WL')[0]
            except IndexError:
                # only in autotest environment
                raise Http404('Rol ontbreekt')

        context['sec_names'] = self.get_all_names(functie_sec)
        context['sec_email'] = functie_sec.bevestigde_email

        if len(context['sec_names']) == 0:
            context['geen_sec'] = True
            try:
                sec = Secretaris.objects.prefetch_related('sporters').get(vereniging=functie_sec.vereniging)
            except Secretaris.DoesNotExist:
                pass
            else:
                if sec.sporters.count() > 0:            # pragma: no branch
                    context['sec_names'] = [sporter.volledige_naam() for sporter in sec.sporters.all()]
                    context['geen_sec'] = False

        if functie_hwl:
            context['toon_hwl'] = True
            context['hwl_names'] = self.get_all_names(functie_hwl)
            context['hwl_email'] = functie_hwl.bevestigde_email
        else:
            context['toon_hwl'] = False

        if functie_wl:
            context['toon_wl'] = True
            context['wl_names'] = self.get_all_names(functie_wl)
            context['wl_email'] = functie_wl.bevestigde_email
        else:
            context['toon_wl'] = False

        if binnen_locatie:
            # beschrijving voor de template
            binnen_locatie.baan_type_str = BAANTYPE2STR[binnen_locatie.baan_type]

            # lijst van verenigingen voor de template
            binnen_locatie.other_ver = binnen_locatie.verenigingen.exclude(ver_nr=ver.ver_nr).order_by('ver_nr')

        if buiten_locatie:
            context['disc'] = [
                ('disc_outdoor', 'Outdoor', buiten_locatie.discipline_outdoor),
                # ('disc_indoor', 'Indoor', buiten_locatie.discipline_indoor),
                ('disc_25m1p', '25m 1pijl', buiten_locatie.discipline_25m1pijl),
                ('disc_veld', 'Veld', buiten_locatie.discipline_veld),
                ('disc_3d', '3D', buiten_locatie.discipline_3d),
                ('disc_run', 'Run archery', buiten_locatie.discipline_run),
                ('disc_clout', 'Clout', buiten_locatie.discipline_clout),
            ]

        context['kruimels'] = (
            (reverse('Vereniging:lijst'), 'Verenigingen'),
            (None, 'Details')
        )

        return context


class GeenBeheerdersView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de BB contactgegevens ophalen van verenigingen zonder gekoppelde beheerders """

    # class variables shared by all instances
    template_name = TEMPLATE_CONTACT_GEEN_BEHEERDERS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        sec_count = dict()
        hwl_count = dict()
        alle_ver = list()
        sec_email = dict()      # [ver_nr] = email
        for func in (Functie
                     .objects
                     .select_related('vereniging')
                     .filter(rol__in=('SEC', 'HWL'))
                     .exclude(vereniging__geen_wedstrijden=True)
                     .exclude(vereniging__is_extern=True)
                     .annotate(aantal_accounts=Count('accounts'))
                     .order_by('vereniging__ver_nr')):

            ver = func.vereniging
            ver_nr = ver.ver_nr
            if func.rol == 'SEC':
                sec_count[ver_nr] = func.aantal_accounts
                if func.bevestigde_email:
                    sec_email[ver_nr] = func.bevestigde_email
            else:
                hwl_count[ver_nr] = func.aantal_accounts

            if ver not in alle_ver:
                alle_ver.append(ver)
        # for

        context['geen_sec'] = geen_sec = list()
        context['geen_hwl'] = geen_hwl = list()

        for ver in alle_ver:
            ver_nr = ver.ver_nr

            try:
                ver.functie_sec_email = sec_email[ver_nr]
            except KeyError:
                ver.functie_sec_email = '??'

            try:
                count = sec_count[ver_nr]
            except KeyError:
                count = 0
            if count == 0:
                geen_sec.append(ver)
                ver.nr_geen_sec = len(geen_sec)

            try:
                count += hwl_count[ver_nr]
            except KeyError:        # pragma: no cover
                count = 0
            if count == 0:
                geen_hwl.append(ver)
                ver.nr_geen_hwl = len(geen_hwl)
        # for

        context['kruimels'] = (
            (reverse('Vereniging:lijst'), 'Verenigingen'),
            (None, 'Zonder beheerders')
        )

        return context


# end of file
