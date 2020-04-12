# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# zet de boog/bogen waarmee de Schutter wil schieten
# aan de hand van de competitie historie


from django.core.management.base import BaseCommand
from BasisTypen.models import BoogType
from HistComp.models import HistCompetitieIndividueel
from Schutter.models import SchutterBoog
from NhbStructuur.models import NhbLid


TOEGESTANE_KLASSEN = ('Recurve', 'Compound', 'Barebow', 'Longbow', 'Instinctive Bow')


class Command(BaseCommand):
    help = "Doorzoek historische competitie voor schutter boogtype voorkeur"
    verbose = False

    def _get_nhblid(self, schutter_nr):
        try:
            return self.schutternr2nhblid[schutter_nr]
        except KeyError:
            pass

        try:
            nhblid = NhbLid.objects.get(nhb_nr=schutter_nr)
        except NhbLid.DoesNotExist:
            nhblid = None

        self.schutternr2nhblid[schutter_nr] = nhblid
        return nhblid

    def _zet_schutterboog_voorkeur(self):
        """ Zet het type boog waarmee de schutter schiet aan de hand van de HistCompetitieIndividueel uitslagen.
            De klasse waarin de schutter uitkwam bepaalt de boog waarmee hij schiet.
        """
        boogtype = dict()
        for obj in BoogType.objects.all():
            boogtype[obj.afkorting] = obj
        # for

        records = 0
        nieuw = 0
        al_aan = 0

        self.schutternr2nhblid = dict()
        done = list()   # (schutter_nr, boogtype)

        for obj in HistCompetitieIndividueel.objects.all():
            records += 1
            if obj.totaal > 0 and obj.boogtype in boogtype:
                tup = (obj.schutter_nr, obj.boogtype)
                if tup not in done:
                    done.append(tup)

                    nhblid = self._get_nhblid(obj.schutter_nr)
                    boogtype_obj = boogtype[obj.boogtype]
                    if nhblid:
                        # haal het voorkeur record op, of maak een nieuwe aan
                        try:
                            schutterboog = SchutterBoog.objects.get(nhblid=nhblid, boogtype=boogtype_obj)
                        except SchutterBoog.DoesNotExist:
                            # nieuw record nodig
                            schutterboog = SchutterBoog()
                            schutterboog.nhblid = nhblid
                            schutterboog.boogtype = boogtype_obj
                            schutterboog.voor_wedstrijd = True
                            schutterboog.save()
                            nieuw += 1
                        else:
                            if not schutterboog.voor_wedstrijd:
                                schutterboog.voor_wedstrijd = True
                                schutterboog.save()
                                nieuw += 1
                            else:
                                al_aan += 1
        # for

        leden = 0
        geen_lid = 0
        for _, nhblid in self.schutternr2nhblid.items():
            if nhblid:
                leden += 1
            else:
                geen_lid += 1
        # for

        print("Samenvatting: %s records doorzocht; %s verschillende leden gevonden in de uitslag; %s geen lid meer; %s bogen al gekozen voor wedstrijden; %s aangezet" % (records, leden, geen_lid, al_aan, nieuw))

    def handle(self, *args, **options):
        self._zet_schutterboog_voorkeur()


# end of file

