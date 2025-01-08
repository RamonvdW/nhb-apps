# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from BasisTypen.definities import ORGANISATIE_IFAA, ORGANISATIE_WA, ORGANISATIES2SHORT_STR
from BasisTypen.models import BoogType
from Sporter.models import SporterBoog


class Command(BaseCommand):
    help = "Toon aantal keuzes voor bogen voor de leden"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.aantal_ifaa_bogen = 0
        self.aantal_wa_bogen = 0
        self.alle_wa_boog_pks = list()
        self.boog_pk2beschrijving = dict()

        for boogtype in BoogType.objects.exclude(buiten_gebruik=True).order_by('pk'):
            if boogtype.organisatie == ORGANISATIE_IFAA:
                self.aantal_ifaa_bogen += 1
            elif boogtype.organisatie == ORGANISATIE_WA:        # pragma: no branch
                self.aantal_wa_bogen += 1
                self.alle_wa_boog_pks.append(boogtype.pk)

            org_str = ORGANISATIES2SHORT_STR[boogtype.organisatie]
            self.boog_pk2beschrijving[boogtype.pk] = org_str + "-" + boogtype.beschrijving
        # for

    @staticmethod
    def _tel_eerste(sporter2bogen):
        eerste = list(sporter2bogen.values())[0]
        post_del = list()
        for lid_nr, bogen in sporter2bogen.items():
            if bogen == eerste:
                post_del.append(lid_nr)
        # for

        aantal_gevonden = len(post_del)
        for lid_nr in post_del:
            del sporter2bogen[lid_nr]
        # for

        return aantal_gevonden, eerste

    def handle(self, *args, **options):
        # bepaal welke sporters actief een keuze gemaakt hebben
        sporter_pks = list(SporterBoog.objects.distinct('sporter__pk').values_list('sporter__pk', flat=True))
        aantal = len(sporter_pks)
        self.stdout.write('%5s sporters in MijnHandboogsport met boog voorkeuren' % aantal)

        sporter2bogen = dict()      # [lid_nr] = [boog1, boog2, ..]
        for sporterboog in SporterBoog.objects.filter(voor_wedstrijd=True).select_related('boogtype', 'sporter'):
            lid_nr = sporterboog.sporter.lid_nr
            pk = sporterboog.boogtype.pk
            try:
                sporter2bogen[lid_nr].append(pk)
            except KeyError:
                sporter2bogen[lid_nr] = [pk]
        # for

        # sorteer de lijsten
        for bogen in sporter2bogen.values():
            bogen.sort()
        # for

        # rapporteer de aantallen
        lines = list()
        while len(sporter2bogen) > 0:
            aantal_gevonden, bogen = self._tel_eerste(sporter2bogen)

            descr = list()
            for boog_pk in bogen:
                descr.append(self.boog_pk2beschrijving[boog_pk])
            # for
            bogen_str = ", ".join(descr)

            perc = (aantal_gevonden * 100.0) / aantal
            line = "%5s (%3.0f%%) %s" % (aantal_gevonden, perc, bogen_str)
            lines.append(line)
        # while

        lines.sort(reverse=True)
        self.stdout.write('Gemaakte keuzes:')
        for line in lines:
            self.stdout.write(line)

# end of file
