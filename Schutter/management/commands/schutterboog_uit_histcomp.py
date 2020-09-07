# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# zet de boog/bogen waarmee de Schutter wil schieten en aanvangsgemiddelde
# aan de hand van de competitie historie


from django.core.management.base import BaseCommand
from django.utils import timezone
from BasisTypen.models import BoogType
from HistComp.models import HistCompetitieIndividueel
from Schutter.models import SchutterBoog
from Score.models import aanvangsgemiddelde_opslaan
from NhbStructuur.models import NhbLid
from Competitie.models import AG_NUL
import datetime

TOEGESTANE_KLASSEN = ('Recurve', 'Compound', 'Barebow', 'Longbow', 'Instinctive Bow')


class Command(BaseCommand):
    help = "Doorzoek historische competitie voor informatie over schutterboog"
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

        # maak een cache aan van boogtype
        boogtype_dict = dict()      # [afkorting] = BoogType
        for obj in BoogType.objects.all():
            boogtype_dict[obj.afkorting] = obj
        # for

        # maak een cache aan van nhbleden
        nhblid_dict = dict()        # [nhb_nr] = NhbLid
        for obj in NhbLid.objects.all():
            nhblid_dict[obj.nhb_nr] = obj
        # for

        records = 0
        nieuw = 0
        al_aan = 0
        nieuw_ag = 0
        geen_lid_meer = 0
        leden = 0

        self.schutternr2nhblid = dict()
        done = list()   # (schutter_nr, boogtype)

        for obj in HistCompetitieIndividueel.objects.all():
            records += 1
            if obj.totaal > 0 and obj.boogtype in boogtype_dict:
                boogtype_obj = boogtype_dict[obj.boogtype]
                try:
                    nhblid = nhblid_dict[obj.schutter_nr]
                except KeyError:
                    geen_lid_meer += 1
                else:
                    leden += 1
                    # haal het schutterboog record op, of maak een nieuwe aan
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

                    # zoek het score record erbij
                    if obj.gemiddelde > AG_NUL:
                        if aanvangsgemiddelde_opslaan(
                                schutterboog,
                                int(obj.histcompetitie.comp_type),
                                obj.gemiddelde,
                                None,
                                "Uitslag competitie seizoen %s" % obj.histcompetitie.seizoen):
                            nieuw_ag += 1
        # for

        print("Samenvatting: %s records doorzocht; %s verschillende leden gevonden in de uitslag;"
              " %s geen lid meer; %s bogen al gekozen voor wedstrijden; %s aangezet;"
              " %s aanvangsgemiddelden bepaald" % (records, leden, geen_lid_meer, al_aan, nieuw, nieuw_ag))

    def handle(self, *args, **options):
        self._zet_schutterboog_voorkeur()


# end of file

