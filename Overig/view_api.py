# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponse
from django.views import View
from BasisTypen.definities import ORGANISATIE_IFAA, ORGANISATIE_WA
from BasisTypen.models import BoogType
from Competitie.models import RegiocompetitieSporterBoog
from HistComp.models import HistCompRegioIndiv, HistCompSeizoen
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.definities import WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF, WEDSTRIJD_DISCIPLINES
from Wedstrijden.models import WedstrijdInschrijving
from codecs import BOM_UTF8
import csv

CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'


class ApiCsvLijstView(View):

    @staticmethod
    def get(request, *args, **kwargs):
        """ Geeft een lijst met evenementen/wedstrijden/opleidingen terug

            # aantal_dagen_terug: 1..1000 dagen
            aantal_dagen_vooruit: 1..36 dagen

            verplichte parameter: token
        """

        token = request.GET.get('token', '')
        if token not in settings.OVERIG_API_TOKENS:
            token = None

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="mh-info-leden.csv"'

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=",")

        # geef alleen een antwoord als een valide token opgegeven is
        if token:
            afkortingen = list(BoogType.objects.order_by('volgorde').values_list('afkorting', flat=True))
            boog2beschrijving = dict()
            for tup in BoogType.objects.order_by('volgorde').values_list('afkorting', 'organisatie', 'beschrijving'):
                afkorting, organisatie, beschrijving = tup
                if organisatie == ORGANISATIE_WA:
                    boog2beschrijving[afkorting] = beschrijving + ' (WA)'
                elif organisatie == ORGANISATIE_IFAA:
                    boog2beschrijving[afkorting] = beschrijving + ' (IFAA)'
                else:       # pragma: no cover
                    boog2beschrijving[afkorting] = beschrijving + ' (??)'
            # for

            lid2ver_nr = dict()         # [lid_nr] = ver_nr
            lid2leeftijd = dict()       # [lid_nr] = leeftijd
            lid2account = dict()        # [lid_nr] = 0/1
            lid2bogen = dict()          # [lid_nr] = [afkorting, ..]
            lid2comp18 = dict()         # [lid_nr] = n
            lid2comp25 = dict()         # [lid_nr] = n
            lid2wedstrijd = dict()      # [lid_nr] = disc2count[discipline] = aantal
            alle_lid_nrs = list()

            # informatie over de leden ophalen
            for sporter in (Sporter
                            .objects
                            .select_related('bij_vereniging')
                            .filter(is_actief_lid=True)
                            .exclude(bij_vereniging=None)
                            .order_by('lid_nr')):

                alle_lid_nrs.append(sporter.lid_nr)
                lid2ver_nr[sporter.lid_nr] = sporter.bij_vereniging.ver_nr
                lid2leeftijd[sporter.lid_nr] = sporter.bereken_leeftijd()

                if sporter.account:
                    lid2account[sporter.lid_nr] = 1
                else:
                    lid2account[sporter.lid_nr] = 0
            # for

            # informatie over de gekozen bogen ophalen
            for tup in (SporterBoog
                        .objects
                        .select_related('sporter',
                                        'boogtype')
                        .values_list('sporter__lid_nr',
                                     'boogtype__afkorting')):
                lid_nr, afkorting = tup
                try:
                    bogen = lid2bogen[lid_nr]
                except KeyError:
                    lid2bogen[lid_nr] = bogen = list()
                bogen.append(afkorting)
            # for

            # informatie over historische competitie deelname
            seizoenen = list(HistCompSeizoen
                             .objects
                             .exclude(is_openbaar=False)
                             .order_by('-seizoen')
                             .distinct('seizoen')
                             .values_list('seizoen', flat=True))[:2]
            seizoen_pks = list(HistCompSeizoen.objects.filter(seizoen__in=seizoenen).values_list('pk', flat=True))
            for tup in (HistCompRegioIndiv
                        .objects
                        .filter(seizoen__pk__in=seizoen_pks)
                        .select_related('seizoen',
                                        'sporter')
                        .values_list('seizoen__comp_type',
                                     'sporter_lid_nr')):
                comp_type, lid_nr = tup
                if comp_type == '18':
                    lid2comp18[lid_nr] = lid2comp18.get(lid_nr, 0) + 1
                elif comp_type == '25':     # pragma: no branch
                    lid2comp25[lid_nr] = lid2comp25.get(lid_nr, 0) + 1
            # for

            # informatie over de huidige competitie deelname
            for tup in (RegiocompetitieSporterBoog
                        .objects
                        .select_related('regiocompetitie__competitie',
                                        'sporterboog__sporter')
                        .exclude(aantal_scores=0)
                        .values_list('regiocompetitie__competitie__afstand',
                                     'sporterboog__sporter__lid_nr')):
                comp_type, lid_nr = tup
                if comp_type == '18':
                    lid2comp18[lid_nr] = lid2comp18.get(lid_nr, 0) + 1
                elif comp_type == '25':     # pragma: no branch
                    lid2comp25[lid_nr] = lid2comp25.get(lid_nr, 0) + 1
            # for

            # wedstrijd deelname
            for tup in (WedstrijdInschrijving
                        .objects
                        .filter(status=WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF)
                        .select_related('wedstrijd',
                                        'sporterboog__sporter')
                        .values_list('sporterboog__sporter__lid_nr',
                                     'wedstrijd__discipline')):
                lid_nr, discipline = tup
                disc2count = lid2wedstrijd.get(lid_nr, dict())
                disc2count[discipline] = disc2count.get(discipline, 0) + 1
                lid2wedstrijd[lid_nr] = disc2count
            # for

            # output de informatie
            headers = ['VerNr', 'Leeftijd', 'MH-account']

            headers.extend([boog2beschrijving[afkorting]
                            for afkorting in afkortingen])

            headers.append('Indoor competities')
            headers.append('25m1pijl competities')

            headers.extend([descr + ' wedstrijden'
                            for _, descr in WEDSTRIJD_DISCIPLINES])

            writer.writerow(headers)
            has_no_data = 'null'

            for lid_nr in alle_lid_nrs:
                regel = [lid2ver_nr[lid_nr],
                         lid2leeftijd[lid_nr],
                         lid2account[lid_nr]]

                bogen = lid2bogen.get(lid_nr, [])
                for afkorting in afkortingen:
                    if afkorting in bogen:
                        regel.append(1)
                    else:
                        regel.append(0)
                # for

                comp18 = lid2comp18.get(lid_nr, 0)
                regel.append(str(comp18))

                comp25 = lid2comp25.get(lid_nr, 0)
                regel.append(str(comp25))

                disc2count = lid2wedstrijd.get(lid_nr, None)
                if disc2count is None:
                    print('no mathces for %s; account = %s' % (lid_nr, lid2account[lid_nr]))
                    if lid2account[lid_nr] > 0:
                        disc2count = dict()     # toon 0-en

                if disc2count is None:          # let op: "is None" is nodig, anders ook hierin bij lege dict
                    for discipline, _ in WEDSTRIJD_DISCIPLINES:
                        regel.append(has_no_data)
                    # for
                else:
                    for discipline, _ in WEDSTRIJD_DISCIPLINES:
                        count = disc2count.get(discipline, 0)
                        regel.append(count)
                    # for

                writer.writerow(regel)
            # for

        return response


# end of file
