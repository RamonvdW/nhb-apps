# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Plein.menu import menu_dynamics
from Sporter.models import Sporter
from .models import HistCompetitie, HistCompetitieIndividueel
from decimal import Decimal
import csv


TEMPLATE_HISTCOMP_INTERLAND = 'hist/interland.dtl'

RESULTS_PER_PAGE = 100

KLASSEN_VOLGORDE = ("Recurve", "Compound", "Barebow", "Instinctive", "Longbow")


MINIMALE_LEEFTIJD_JEUGD_INTERLAND = 13      # alles jonger wordt niet getoond
MAXIMALE_LEEFTIJD_JEUGD_INTERLAND = 20      # boven deze leeftijd Senior


class InterlandView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de resultaten van de 25m1pijl die nodig zijn voor de Interland """

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_INTERLAND
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    @staticmethod
    def maak_data(context):

        # maak een cache aan van leden
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

        context['klassen'] = list()

        # zoek het nieuwste seizoen beschikbaar
        qset = HistCompetitie.objects.filter(comp_type='25').order_by('-seizoen').distinct('seizoen')
        if len(qset) > 0:
            # neem de data van het nieuwste seizoen
            context['seizoen'] = seizoen = qset[0].seizoen

            # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
            # dit is het tweede jaar van het seizoen
            context['wedstrijd_jaar'] = wedstrijd_jaar = int(seizoen.split('/')[1])

            for klasse in (HistCompetitie
                           .objects
                           .filter(comp_type='25', seizoen=seizoen, is_team=False)):
                context['klassen'].append(klasse)

                klasse.url_download = reverse('HistComp:interland-als-bestand',
                                              kwargs={'klasse_pk': klasse.pk})

                # zoek alle records erbij met minimaal 5 scores
                klasse.indiv = list()

                for indiv in (HistCompetitieIndividueel
                              .objects
                              .filter(histcompetitie=klasse,
                                      gemiddelde__gt=Decimal('0.000'))
                              .order_by('-gemiddelde')):

                    if indiv.tel_aantal_scores() >= settings.INTERLAND_25M_MINIMUM_SCORES_VOOR_DEELNAME:

                        # zoek de sporter erbij
                        try:
                            sporter = lid_nr2sporter[indiv.schutter_nr]
                        except KeyError:
                            sporter = None

                        if sporter:
                            indiv.sporter = sporter
                            indiv.wedstrijd_leeftijd = sporter.bereken_wedstrijdleeftijd_wa(wedstrijd_jaar)
                            if indiv.wedstrijd_leeftijd >= MINIMALE_LEEFTIJD_JEUGD_INTERLAND:
                                if indiv.wedstrijd_leeftijd <= MAXIMALE_LEEFTIJD_JEUGD_INTERLAND:
                                    indiv.leeftijd_str = "Jeugd (%s)" % indiv.wedstrijd_leeftijd
                                else:
                                    indiv.leeftijd_str = "Senior"

                                klasse.indiv.append(indiv)
            # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self.maak_data(context)

        context['kruimels'] = (
            (None, 'Interland lijst'),
        )

        menu_dynamics(self.request, context)
        return context


class InterlandAlsBestandView(InterlandView):

    """ Deze klasse wordt gebruikt om de interland deelnemers lijst
        te downloaden als csv bestand
    """

    def get(self, request, *args, **kwargs):

        try:
            klasse_pk = int(kwargs['klasse_pk'][:6])            # afkappen voor de veiligheid
            klasse = HistCompetitie.objects.get(pk=klasse_pk)
        except (ValueError, HistCompetitie.DoesNotExist):
            raise Http404('Klasse niet gevonden')

        context = dict()
        self.maak_data(context)

        indivs = None
        for context_klasse in context['klassen']:
            if context_klasse.pk == klasse.pk:
                indivs = context_klasse.indiv
                break   # from the for
        # for

        if indivs is None:
            raise Http404('Geen sporters gevonden')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="interland.csv"'

        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings
        writer.writerow(['Gemiddelde', 'Klasse', 'Geslacht', 'Lid', 'Naam', 'Vereniging'])

        for indiv in indivs:
            writer.writerow([indiv.gemiddelde,
                             indiv.leeftijd_str,
                             indiv.sporter.geslacht,
                             indiv.sporter.lid_nr,
                             indiv.sporter.volledige_naam(),
                             indiv.sporter.bij_vereniging])
        # for

        return response

# end of file
