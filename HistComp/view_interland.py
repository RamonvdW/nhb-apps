# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from HistComp.definities import HISTCOMP_TYPE_25, HIST_INTERLAND_BOGEN, HIST_BOOG2STR
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Sporter.models import Sporter
from decimal import Decimal
from codecs import BOM_UTF8
from types import SimpleNamespace
import csv


TEMPLATE_HISTCOMP_INTERLAND = 'histcomp/interland.dtl'

KLASSEN_VOLGORDE = ("Recurve", "Compound", "Barebow", "Instinctive", "Longbow")

MINIMALE_LEEFTIJD_JEUGD_INTERLAND = 13      # alles jonger wordt niet getoond
MAXIMALE_LEEFTIJD_JEUGD_INTERLAND = 20      # boven deze leeftijd Senior

CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'


class InterlandView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de resultaten van de 25m1pijl die nodig zijn voor de Interland """

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_INTERLAND
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ)

    @staticmethod
    def maak_data(context):

        # maak een cache aan van leden
        # deze hebben we nodig om de wedstrijdleeftijd te berekenen
        lid_nr2sporter = dict()  # [lid_nr] = Sporter
        for sporter in (Sporter
                        .objects
                        .filter(is_actief_lid=True)
                        .select_related('bij_vereniging')
                        .all()):
            lid_nr2sporter[sporter.lid_nr] = sporter
        # for

        context['jeugd_min'] = MINIMALE_LEEFTIJD_JEUGD_INTERLAND
        context['jeugd_max'] = MAXIMALE_LEEFTIJD_JEUGD_INTERLAND
        context['minimum_aantal_scores'] = settings.INTERLAND_25M_MINIMUM_SCORES_VOOR_DEELNAME

        context['seizoen'] = context['wedstrijd_jaar'] = '?'
        context['klassen'] = list()

        # zoek het nieuwste seizoen beschikbaar
        qset = HistCompSeizoen.objects.filter(comp_type=HISTCOMP_TYPE_25).order_by('-seizoen').distinct('seizoen')
        if len(qset) > 0:
            # neem de data van het nieuwste seizoen
            seizoen = qset[0]
            context['seizoen'] = seizoen_str = seizoen.seizoen

            # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
            # dit is het tweede jaar van het seizoen
            context['wedstrijd_jaar'] = wedstrijd_jaar = int(seizoen_str.split('/')[1])

            for boog_afkorting in HIST_INTERLAND_BOGEN:
                klasse = SimpleNamespace(
                            boog_type=boog_afkorting,
                            beschrijving=HIST_BOOG2STR[boog_afkorting],
                            url_download=reverse('HistComp:interland-als-bestand',
                                                 kwargs={'boog_type': boog_afkorting}),
                            indiv=list())
                context['klassen'].append(klasse)

                # zoek alle records erbij met minimaal 5 scores
                for indiv in (HistCompRegioIndiv
                              .objects
                              .filter(seizoen=seizoen,
                                      boogtype=boog_afkorting,
                                      gemiddelde__gt=Decimal('0.000'))
                              .order_by('-gemiddelde')):

                    if indiv.tel_aantal_scores() >= settings.INTERLAND_25M_MINIMUM_SCORES_VOOR_DEELNAME:

                        # zoek de sporter erbij
                        try:
                            sporter = lid_nr2sporter[indiv.sporter_lid_nr]
                        except KeyError:
                            # niet op de lijst zetten
                            pass
                        else:
                            indiv.sporter_geslacht = sporter.geslacht       # TODO: wedstrijdgeslacht meenemen

                            indiv.wedstrijd_leeftijd = sporter.bereken_wedstrijdleeftijd_wa(wedstrijd_jaar)
                            if indiv.wedstrijd_leeftijd >= MINIMALE_LEEFTIJD_JEUGD_INTERLAND:
                                if indiv.wedstrijd_leeftijd <= MAXIMALE_LEEFTIJD_JEUGD_INTERLAND:
                                    indiv.leeftijd_str = "Jeugd (%s)" % indiv.wedstrijd_leeftijd
                                else:
                                    indiv.leeftijd_str = "Senior"

                                klasse.indiv.append(indiv)

                            # eventuele overstap meenemen
                            ver = sporter.bij_vereniging
                            if ver:
                                sporter.vereniging_nr = ver.ver_nr
                                sporter.vereniging_naam = ver.naam

            # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self.maak_data(context)

        context['kruimels'] = (
            (None, 'Interland lijst'),
        )

        return context


class InterlandAlsBestandView(InterlandView):

    """ Deze klasse wordt gebruikt om de interland deelnemers lijst
        te downloaden als csv bestand
    """

    def get(self, request, *args, **kwargs):

        afkorting = kwargs['boog_type'][:2]     # afkappen voor de veiligheid
        if afkorting not in HIST_INTERLAND_BOGEN:
            raise Http404('Verkeerd boog type')

        context = dict()
        self.maak_data(context)

        indivs = None
        for klasse in context['klassen']:
            if klasse.boog_type == afkorting:
                indivs = klasse.indiv
                break   # from the for
        # for

        if indivs is None:
            raise Http404('Geen data')

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="interland-%s.csv"' % afkorting.lower()

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings
        writer.writerow(['Gemiddelde', 'Klasse', 'Geslacht', 'Lid nr', 'Naam', 'Vereniging'])

        for indiv in indivs:
            ver_str = '[%s] %s' % (indiv.vereniging_nr, indiv.vereniging_naam)
            if indiv.vereniging_plaats:
                ver_str += ' (%s)' % indiv.vereniging_plaats

            writer.writerow([indiv.gemiddelde,
                             indiv.leeftijd_str,
                             indiv.sporter_geslacht,
                             indiv.sporter_lid_nr,
                             indiv.sporter_naam,
                             ver_str])
        # for

        return response

# end of file
