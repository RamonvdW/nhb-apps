# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Sporter.models import Sporter
from Registreer.definities import REGISTRATIE_FASE_AFGEWEZEN
from Registreer.models import GastRegistratie


class Command(BaseCommand):
    help = "Analyseer gast registraties"

    @staticmethod
    def _zoek_matches(gast):
        gast.ophef = 0

        # zoek naar overeenkomst in CRM
        try:
            eigen_lid_nr = int(gast.eigen_lid_nummer)
        except ValueError:
            pks1 = list()
        else:
            pks1 = list(Sporter
                        .objects
                        .exclude(is_gast=True)
                        .filter(lid_nr=eigen_lid_nr)
                        .values_list('pk', flat=True))

        if gast.wa_id:
            pks2 = list(Sporter
                        .objects
                        .exclude(is_gast=True)
                        .filter(wa_id=gast.wa_id)
                        .values_list('pk', flat=True))
        else:
            pks2 = list()

        pks3 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(achternaam__iexact=gast.achternaam)
                    .values_list('pk', flat=True))

        pks4 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(voornaam__iexact=gast.voornaam)
                    .values_list('pk', flat=True))

        pks5 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(geboorte_datum=gast.geboorte_datum)
                    .values_list('pk', flat=True))

        pks6 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(email__iexact=gast.email)
                    .values_list('pk', flat=True))

        match_count = dict()    # [pk] = count
        for pk in pks1 + pks2 + pks3 + pks4 + pks5 + pks6:
            try:
                match_count[pk] += 1
            except KeyError:
                match_count[pk] = 1
        # for

        best = list()
        for pk, count in match_count.items():
            tup = (count, pk)
            best.append(tup)
        # for
        best.sort(reverse=True)     # hoogste eerst

        beste_pks = [pk for count, pk in best[:10] if count > 1]
        matches = (Sporter
                   .objects
                   .select_related('account',
                                   'bij_vereniging')
                   .filter(pk__in=beste_pks))
        for match in matches:
            match.is_match_geboorte_datum = match.geboorte_datum == gast.geboorte_datum
            match.is_match_email = match.email.lower() == gast.email.lower()
            match.is_match_lid_nr = gast.eigen_lid_nummer == str(match.lid_nr)
            match.is_match_geslacht = gast.geslacht == match.geslacht
            match.is_match_voornaam = gast.voornaam.upper() in match.voornaam.upper()
            match.is_match_achternaam = gast.achternaam.upper() in match.achternaam.upper()

            if match.bij_vereniging:
                match.vereniging_str = match.bij_vereniging.ver_nr_en_naam()
                match.is_match_vereniging = gast.club.upper() in match.vereniging_str.upper()

                match.plaats_str = match.bij_vereniging.plaats
                match.is_match_plaats = (gast.club_plaats.upper().replace('-', ' ') in
                                         match.plaats_str.upper().replace('-', ' '))
            else:
                match.is_match_vereniging = False
                match.is_match_plaats = False

            match.heeft_account = (match.account is not None)

            if match.is_match_geboorte_datum:
                gast.ophef += 1
            if match.is_match_email:
                gast.ophef += 5
            if match.is_match_lid_nr:
                gast.ophef += 5
            if match.is_match_voornaam:
                gast.ophef += 1
            if match.is_match_achternaam:
                gast.ophef += 1
            if match.is_match_geslacht:
                gast.ophef += 1
            if match.is_match_vereniging:
                gast.ophef += 1
            if match.is_match_plaats:
                gast.ophef += 1
            if match.heeft_account:
                gast.ophef += 5
        # for

        return matches

    def handle(self, *args, **options):
        self.stdout.write('nr     geb   email lid   naam1 naam2 gesl  ver1  ver2  acc')
        for gast in GastRegistratie.objects.all():

            if gast.fase == REGISTRATIE_FASE_AFGEWEZEN:
                self.stdout.write('%6s (afgewezen)' % gast.lid_nr)
            else:
                self.stdout.write('%6s' % gast.lid_nr)

            matches = self._zoek_matches(gast)
            for match in matches:
                self.stdout.write('%-6s %-5s %-5s %-5s %-5s %-5s %-5s %-5s %-5s %-5s' %
                                    ('', match.is_match_geboorte_datum, match.is_match_email,
                                     match.is_match_lid_nr, match.is_match_voornaam, match.is_match_achternaam,
                                     match.is_match_geslacht, match.is_match_vereniging, match.is_match_plaats,
                                     match.heeft_account))


# end of file
