# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieSporterBoog
from Competitie.seizoenen import get_comp_pk
from Geo.models import Regio
from HistComp.operations import get_hist_url
from Overig.helpers import make_valid_hashtag
from Sporter.operations import get_request_regio_nr
from Vereniging.models import Vereniging


TEMPLATE_COMPUITSLAGEN_REGIO_INDIV = 'compuitslagen/regio-indiv.dtl'


class UitslagenRegioIndivView(TemplateView):

    """ Django class-based view voor de individuele uitslagen van de regiocompetitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_REGIO_INDIV

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comp = None

    def dispatch(self, request, *args, **kwargs):
        """ converteer het seizoen naar een competitie
            stuur oude seizoenen door naar histcomp """
        try:
            comp_pk = get_comp_pk(kwargs['comp_pk_of_seizoen'])
            self.comp = (Competitie
                         .objects
                         .prefetch_related('boogtypen')
                         .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            url_hist = get_hist_url(kwargs['comp_pk_of_seizoen'], 'indiv', 'regio', kwargs['comp_boog'][:2])
            if url_hist:
                return HttpResponseRedirect(url_hist)
        else:
            self.comp.bepaal_fase()

        return super().dispatch(request, *args, **kwargs)

    def _maak_filter_knoppen(self, context, gekozen_regio_nr, comp_boog):
        """ filter optie voor de regio """

        # boogtype filters
        boogtypen = self.comp.boogtypen.order_by('volgorde')

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            boogtype.opt_text = boogtype.beschrijving
            boogtype.sel = 'boog_' + boogtype.afkorting
            if boogtype.afkorting.upper() == comp_boog.upper():
                context['comp_boog'] = boogtype
                # geen url --> knop disabled
                boogtype.selected = True

            boogtype.url_part = boogtype.afkorting.lower()
        # for

        # regio filters
        if context['comp_boog']:
            regios = (Regio
                      .objects
                      .select_related('rayon')
                      .filter(is_administratief=False)
                      .order_by('rayon__rayon_nr', 'regio_nr'))

            context['regio_filters'] = regios

            for regio in regios:
                regio.opt_text = 'Regio %s' % regio.regio_nr
                regio.sel = 'regio_%s' % regio.regio_nr
                if regio.regio_nr == gekozen_regio_nr:
                    context['regio'] = regio
                    regio.selected = True

                regio.url_part = str(regio.regio_nr)
            # for

        # vereniging filters
        if context['comp_boog']:
            vers = (Vereniging
                    .objects
                    .select_related('regio')
                    .filter(regio__regio_nr=gekozen_regio_nr)
                    .order_by('ver_nr'))

            for ver in vers:
                ver.sel = 'ver_%s' % ver.ver_nr
                ver.zoom_url = reverse('CompUitslagen:uitslagen-vereniging-indiv-n',
                                       kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                               'comp_boog': '~1',       # volg boogtype filter
                                               'ver_nr': ver.ver_nr})
            # for

            context['ver_filters'] = vers

    @staticmethod
    def _lijstjes_toevoegen_aan_uitslag(objs, objs1, objs2, needs_closure, klasse_str):
        rank = 0
        aantal = 0
        is_first = True
        prev_obj = None
        for obj in objs1 + objs2:
            aantal += 1
            if prev_obj is None or prev_obj.gemiddelde != obj.gemiddelde:
                rank = aantal
            prev_obj = obj

            obj.rank = rank
            objs.append(obj)

            if is_first:
                obj.break_klasse = True
                obj.needs_closure = needs_closure
                obj.klasse_str = klasse_str
                obj.klasse_hashtag = make_valid_hashtag(obj.klasse_str)
                obj.aantal_in_groep = 2 + len(objs1) + len(objs2)
                is_first = False
        # for

        needs_closure = not is_first
        return needs_closure

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if not self.comp:
            raise Http404('Competitie niet gevonden')

        context['comp'] = self.comp

        comp_boog = kwargs['comp_boog'][:2]     # afkappen voor de veiligheid

        # regio_nr is optioneel (eerste binnenkomst zonder regio nummer)
        try:
            regio_nr = kwargs['regio_nr'][:3]   # afkappen voor de veiligheid
            regio_nr = int(regio_nr)
        except KeyError:
            # bepaal welke (initiële) regio bij de huidige gebruiker past
            regio_nr = get_request_regio_nr(self.request)
        except ValueError:
            raise Http404('Verkeerde regionummer')

        # voorkom 404 voor leden in de administratieve regio
        if regio_nr == 100:
            regio_nr = 101

        try:
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie',
                                        'regio')
                        .get(competitie=self.comp,
                             competitie__is_afgesloten=False,
                             regio__regio_nr=regio_nr))
        except Regiocompetitie.DoesNotExist:
            raise Http404('Competitie niet gevonden')

        context['deelcomp'] = deelcomp

        self._maak_filter_knoppen(context, regio_nr, comp_boog)

        context['url_filters'] = reverse('CompUitslagen:uitslagen-regio-indiv-n',
                                         kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                                 'comp_boog': '~1',
                                                 'regio_nr': '~2'})

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .filter(regiocompetitie=deelcomp)
                      .select_related('sporterboog__sporter',
                                      'bij_vereniging',
                                      'indiv_klasse__boogtype')
                      .filter(indiv_klasse__boogtype=boogtype)
                      .order_by('indiv_klasse__volgorde',
                                '-gemiddelde',          # hoogste eerst
                                '-ag_voor_indiv',       # hoogste eerst (gebruik: bij 0 scores)
                                'pk'))                  # consistente volgorde, vooral in klasse onbekend

        objs = list()
        objs1 = list()      # primary lijst (genoeg scores)
        objs2 = list()      # secundaire lijst (te weinig scores)
        klasse = -1
        klasse_str = None
        needs_closure = False
        for deelnemer in deelnemers:

            if klasse != deelnemer.indiv_klasse.volgorde:
                if klasse_str:
                    needs_closure = self._lijstjes_toevoegen_aan_uitslag(objs, objs1, objs2, needs_closure, klasse_str)
                objs1 = list()
                objs2 = list()
                klasse_str = deelnemer.indiv_klasse.beschrijving
                klasse = deelnemer.indiv_klasse.volgorde

            sporter = deelnemer.sporterboog.sporter
            deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
            deelnemer.ver_str = str(deelnemer.bij_vereniging)

            # in plaats van allemaal 0,000 willen we het AG tonen tijdens de inschrijffase
            if self.comp.fase_indiv < 'F':
                deelnemer.gemiddelde = deelnemer.ag_voor_indiv

            # zet sporters met te weinig scores in een secundair lijst die volgt op de primaire lijst
            if True and deelcomp.is_afgesloten and deelnemer.aantal_scores < self.comp.aantal_scores_voor_rk_deelname:
                # eindstand en te weinig scores
                objs2.append(deelnemer)
            else:
                objs1.append(deelnemer)
        # for

        self._lijstjes_toevoegen_aan_uitslag(objs, objs1, objs2, needs_closure, klasse_str)

        context['deelnemers'] = objs
        context['heeft_deelnemers'] = (len(objs) > 0)
        context['canonical'] = reverse('CompUitslagen:uitslagen-regio-indiv',       # TODO: keep?
                                       kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url(),
                                               'comp_boog': comp_boog})

        context['robots'] = 'nofollow'   # prevent crawling filter result pages

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': self.comp.maak_seizoen_url()}),
                self.comp.beschrijving.replace(' competitie', '')),
            (None, 'Regio individueel')
        )

        return context


# end of file
