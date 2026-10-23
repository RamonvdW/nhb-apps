# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Account.models import Account
from Competitie.models import CompetitieMatch
from Score.definities import SCORE_WAARDE_VERWIJDERD
from Score.models import Score, ScoreHist, Uitslag
from Sporter.models import SporterBoog
from Vereniging.definities import TYPE_EXTERNE_SCORES_CENTAUR
from Vereniging.models import Vereniging, ExterneScores
import requests


class ExterneScoresCentaur:

    def __init__(self, stdout, account: Account, ext: ExterneScores, match: CompetitieMatch):
        self.stdout = stdout
        self._door_account = account
        self._when = timezone.now()
        self._ext: ExterneScores = ext
        self._match: CompetitieMatch = match
        self._token: str = ''
        self._externe_uitslag = list()

    def _get_of_maak_match_uitslag(self):
        # maak de uitslag aan indien nog niet gedaan
        if not self._match.uitslag:
            uitslag = Uitslag.objects.create(
                        max_score=300 if self._match.competitie.is_indoor() else 250,
                        afstand=18 if self._match.competitie.is_indoor() else 25)
            self._match.uitslag = uitslag
            self._match.save(update_fields=['uitslag'])

        return self._match.uitslag

    def _fetch_token(self):
        """ Haal een authenticatie-token op bij het externe scores systeem """
        _func = 'ExterneScoresCentaur._fetch_token'

        headers = {'Content-Type': 'application/json'}
        data = {"username": self._ext.username, "password": self._ext.password}

        try:
            resp = requests.post(
                            self._ext.url_auth,
                            headers=headers,
                            json=data)
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
            self.stdout.write("[ERROR] {%s} Onverwachte fout tijdens authenticatie: %s" % (_func, exc))
            return

        if resp.status_code != 200:
            self.stdout.write("[ERROR] {%s} Onverwachte status tijdens authenticatie: %s" % (_func, resp.status_code))
            return

        data = resp.json()
        # self.stdout.write('[DEBUG] {%s} resp data=%s' % (_func, repr(data)))

        token = data.get('token', '')
        if not token:
            self.stdout.write('[ERROR] {%s} Geen token gekregen tijdens authenticatie: data=%s' % (_func, repr(data)))
            return

        self.stdout.write('[INFO] {%s} token ontvangen (len=%s)' % (_func, len(token)))
        self._token = token

    def _fetch_uitslag(self):
        """ Haal de uitslag op bij het externe scores systeem """
        _func = 'ExterneScoresCentaur._fetch_uitslag'

        self._externe_uitslag = list()

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self._token,
        }
        data = {
            'verenigingsnummer': self._match.vereniging.ver_nr,
            'date': self._match.datum_wanneer.strftime('%Y-%m-%d'),
            'starttime': self._match.tijd_begin_wedstrijd.strftime('%H:%M')
        }

        # self.stdout.write('[DEBUG] {%s} data=%s' % (_func, repr(data)))

        try:
            resp = requests.post(
                            self._ext.url_ophalen,
                            headers=headers,
                            json=data)
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
            self.stdout.write("[ERROR] {%s} Onverwachte fout tijdens ophalen: %s" % (_func, exc))
            return

        if resp.status_code != 200:
            self.stdout.write("[ERROR] {%s} Onverwachte status tijdens ophalen: %s" % (_func, resp.status_code))
            return

        data = resp.json()
        # self.stdout.write('[DEBUG] {%s} resp data=%s' % (_func, repr(data)))

        uitslag = data.get('results', None)
        if not uitslag:
            self.stdout.write('[ERROR] {%s} Geen results in data %s' % (_func, repr(data)))
            return

        if not isinstance(uitslag, list):
            self.stdout.write('[ERROR] {%s} results in data is geen lijst %s' % (_func, repr(data)))
            return

        self._externe_uitslag = uitslag

    def _uitslag_opslaan(self):
        """ sla de opgeslaagde uitslag op """
        _func = 'ExterneScoresCentaur._uitslag_opslaan'

        uitslag = self._get_of_maak_match_uitslag()

        # maak een look-up tabel voor alle scores in de huidige uitslag
        lid_nr_boogtype2score = dict()
        for score in (uitslag
                      .scores
                      .select_related('sporterboog',
                                      'sporterboog__boogtype',
                                      'sporterboog__sporter')
                      .all()):

            boogtype = score.sporterboog.boogtype
            sporter = score.sporterboog.sporter
            lid_nr_boogtype2score[(str(sporter.lid_nr), boogtype.beschrijving)] = score
        # for

        in_uitslag = list()     # (lid_nr, boogtype)
        bulk_hist = list()

        self.stdout.write('[INFO] Uitslag bevat %s regels' % len(self._externe_uitslag))
        for result_d in self._externe_uitslag:
            # self.stdout.write('[DEBUG] %s result_d: %s' % (_func, repr(result_d)))

            score_str = str(result_d.get('score', ''))[:6]      # afkappen voor de veiligheid
            lid_nr_str = result_d.get('lidnummer', '')[:6]      # afkappen voor de veiligheid
            boogtype_str = result_d.get('boogtype', '')[:15]    # afkappen voor de veiligheid (Traditional = 11)

            try:
                waarde = int(str(score_str))
            except ValueError:
                waarde = None

            if not waarde or waarde < 1 or waarde > uitslag.max_score:
                # overslaan
                self.stdout.write('[ERROR] {%s} slechte score waarde: %s' % (_func, repr(score_str)))
                continue

            tup = (lid_nr_str, boogtype_str)
            in_uitslag.append(tup)
            score = lid_nr_boogtype2score.get(tup, None)

            if score:
                # bestaande regel in de uitslag
                # pas de uitslag aan, indien nodig
                assert isinstance(score, Score)
                if score.waarde != waarde:
                    self.stdout.write('[INFO] {%s} bijgewerkte score: %s --> %s' % (_func, score, waarde))
                    hist = ScoreHist(
                                score=score,
                                oude_waarde=score.waarde,
                                nieuwe_waarde=waarde,
                                when=self._when,
                                door_account=self._door_account,
                                notitie="Download externe uitslag wedstrijd")
                    bulk_hist.append(hist)

                    score.waarde = waarde
                    score.save(update_fields=['waarde'])
                # else: zelfde score --> niets doen
            else:
                # nieuw toevoegen
                try:
                    sporterboog = SporterBoog.objects.get(sporter__lid_nr=lid_nr_str,
                                                          boogtype__beschrijving=boogtype_str)
                except (ValueError, SporterBoog.DoesNotExist):
                    # garbage --> ignore
                    self.stdout.write('[ERROR] {%s} Kan sporterboog niet vinden: lid_nr=%s, boogtype=%s' % (
                                        _func, repr(lid_nr_str), repr(boogtype_str)))
                else:
                    score = Score(sporterboog=sporterboog,
                                  waarde=waarde,
                                  afstand_meter=uitslag.afstand)
                    score.save()
                    uitslag.scores.add(score)

                    hist = ScoreHist(
                                score=score,
                                oude_waarde=0,
                                nieuwe_waarde=waarde,
                                when=self._when,
                                door_account=self._door_account,
                                notitie="Download externe uitslag wedstrijd")
                    bulk_hist.append(hist)
        # for

        # verwijder iedereen uit de uitslag die er niet meer in voorkomt
        for tup, score in lid_nr_boogtype2score.items():
            if tup not in in_uitslag:
                # verwijder deze score uit de uitslag, maar behoud de geschiedenis
                self.stdout.write('[INFO] {%s} verwijder uit uitslag: %s' % (_func, score))

                hist = ScoreHist(
                            score=score,
                            oude_waarde=score.waarde,
                            nieuwe_waarde=SCORE_WAARDE_VERWIJDERD,
                            when=self._when,
                            door_account=self._door_account,
                            notitie="Download externe uitslag wedstrijd")
                bulk_hist.append(hist)

                score.waarde = SCORE_WAARDE_VERWIJDERD
                score.save(update_fields=['waarde'])
        # for

        ScoreHist.objects.bulk_create(bulk_hist)

    def ophalen(self):
        # stap 1: authenticatie --> token
        self._fetch_token()
        if not self._token:
            return

        # stap 2: datum + tijd + token --> uitslag
        self._fetch_uitslag()

        # stap 3: opslaan
        if len(self._externe_uitslag):
            self._uitslag_opslaan()


def comp_scores_uitslag_extern_ophalen(stdout, door_account: Account, ver: Vereniging, match: CompetitieMatch):
    ext = ExterneScores.objects.filter(is_actief=True, vereniging=ver).first()
    if not ext:
        stdout.write('[ERROR] Vereniging %s heeft geen externe scores geconfigureerd' % ver.ver_nr)
        return

    if ext.type == TYPE_EXTERNE_SCORES_CENTAUR:
        ophaler = ExterneScoresCentaur(stdout, door_account, ext, match)
        ophaler.ophalen()
        return

    stdout.write('[ERROR] ExterneSscores.type %s niet geimplementeerd' % ext.type)


# end of file
