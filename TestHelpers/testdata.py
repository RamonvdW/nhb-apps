# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Routines om de database te vullen met een test set die gebruikt wordt in vele van de test cases """

from django.test import Client
from django.core import management
from django.utils import timezone
from Account.models import Account, account_create
from BasisTypen.models import BoogType, TeamType
from Competitie.models import (Competitie, CompetitieKlasse, DeelCompetitie, LAAG_BK, LAAG_RK,
                               RegioCompetitieSchutterBoog,
                               RegiocompetitieTeam, RegiocompetitieTeamPoule)
from Competitie.operations import competities_aanmaken
from Competitie.test_competitie import zet_competitie_fase
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from NhbStructuur.models import NhbRegio, NhbCluster, NhbVereniging
from Score.models import Score, SCORE_TYPE_INDIV_AG
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from bs4 import BeautifulSoup
import datetime
import pyotp
import io

# fixtures zijn overwogen, maar zijn lastig te onderhouden en geven geen recente datums (zoals voor VHPG)


class TestData(object):
    """
        Maak een standaard set data aan die in veel tests gebruikt kan worden

        gebruik:
            from django.test import TestCase
            from TestHelpers import testdata

            class MyTests(TestCase):

                @classmethod
                def setUpTestData(cls):
                    cls.testdata = testdata.TestData()
    """

    OTP_CODE = "test"
    WACHTWOORD = "qewretrytuyi"  # sterk genoeg default wachtwoord

    url_inschrijven = '/vereniging/leden-aanmelden/competitie/%s/'  # comp_pk
    url_account_login = '/account/login/'
    url_check_otp = '/functie/otp-controle/'
    url_activeer_functie = '/functie/activeer-functie/%s/'
    url_wissel_van_rol = '/functie/wissel-van-rol/'
    url_volgende_ronde = '/bondscompetities/regio/%s/team-ronde/'   # deelcomp_pk

    def __init__(self):
        self.account_admin = None
        self.account_bb = None

        # verenigingen
        self.account_sec = dict()               # [ver_nr] = Account
        self.account_hwl = dict()               # [ver_nr] = Account

        self.functie_sec = dict()               # [ver_nr] = Functie
        self.functie_hwl = dict()               # [ver_nr] = Functie

        # leden
        self.ver_sporters = dict()              # [ver_nr] = list(Sporter)

        # competities
        self.comp18 = None                      # Competitie
        self.deelcomp18_bk = None               # DeelCompetitie
        self.deelcomp18_rk = dict()             # [rayon_nr] DeelCompetitie
        self.deelcomp18_regio = dict()          # [regio_nr] DeelCompetitie

        self.comp25 = None                      # Competitie
        self.deelcomp25_bk = None               # DeelCompetitie
        self.deelcomp25_rk = dict()             # [rayon_nr] DeelCompetitie
        self.deelcomp25_regio = dict()          # [regio_nr] DeelCompetitie

        # competitie accounts
        self.comp18_account_bko = None          # Account
        self.comp18_account_rko = dict()        # [rayon_nr] = Account
        self.comp18_account_rcl = dict()        # [regio_nr] = Account

        self.comp25_account_bko = None          # Account
        self.comp25_account_rko = dict()        # [rayon_nr] = Account
        self.comp25_account_rcl = dict()        # [regio_nr] = Account

        # competitie functies
        self.comp18_functie_bko = None          # Functie
        self.comp18_functie_rko = dict()        # [rayon_nr] = Functie
        self.comp18_functie_rcl = dict()        # [regio_nr] = Functie

        self.comp25_functie_bko = None          # Functie
        self.comp25_functie_rko = dict()        # [rayon_nr] = Functie
        self.comp25_functie_rcl = dict()        # [regio_nr] = Functie

        self.regio_cluster = dict()             # [regio_nr] = NhbCluster (alleen regio 101 en 107)

        # all inschrijvingen
        self.comp18_deelnemers = list()
        self.comp25_deelnemers = list()

        # inschrijvingen zonder team voorkeur
        self.comp18_deelnemers_geen_team = list()
        self.comp25_deelnemers_geen_team = list()

        # inschrijvingen met team voorkeur
        self.comp18_deelnemers_team = list()
        self.comp25_deelnemers_team = list()

        # aangemaakte teams
        self.comp18_regioteams = list()
        self.comp25_regioteams = list()

        # aangemaakte poules
        self.comp18_poules = list()
        self.comp25_poules = list()

        self._accounts_beheerders = list()      # 1 per vereniging, voor BKO, RKO, RCL

    @staticmethod
    def _dump_resp(resp):                                                       # pragma: no cover
        print("status code:", resp.status_code)
        print(repr(resp))
        if resp.status_code == 302:
            print("redirect to url:", resp.url)
        content = str(resp.content)
        if len(content) < 50:
            print("very short content:", content)
        else:
            soup = BeautifulSoup(content, features="html.parser")
            print(soup.prettify())

    def _login(self, client, account):
        resp = client.post(self.url_account_login,
                           {'login_naam': account.username,
                            'wachtwoord': self.WACHTWOORD})
        if resp.status_code != 302:
            raise ValueError('Login as HWL failed')                             # pragma: no cover

        # pass OTP
        resp = client.post(self.url_check_otp,
                           {'otp_code': pyotp.TOTP(account.otp_code).now()})
        if resp.status_code != 302 or resp.url != self.url_wissel_van_rol:      # pragma: no cover
            self._dump_resp(resp)
            raise ValueError('OTP check voor HWL failed')

    def _wissel_naar_functie(self, client, functie):
        # wissel naar HWL
        resp = client.post(self.url_activeer_functie % functie.pk)
        if resp.status_code != 302:                                             # pragma: no cover
            self._dump_resp(resp)
            raise ValueError('Wissel naar functie HWL failed')

    @staticmethod
    def _verwerk_mutaties(show_warnings=True, show_all=False):
        # vraag de achtergrond taak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if show_all:                                                            # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

        elif show_warnings:
            lines = f1.getvalue() + '\n' + f2.getvalue()
            for line in lines.split('\n'):
                if line.startswith('[WARNING] '):                               # pragma: no cover
                    print(line)
            # for

    def regio_teamcompetitie_ronde_doorzetten(self, deelcomp):
        """
            Trigger de site om de team ronde van een specifieke competitie door te zetten naar de volgende ronde
        """
        regio_nr = deelcomp.nhb_regio.regio_nr
        if deelcomp.competitie.afstand == 18:
            account = self.comp18_account_rcl[regio_nr]
            functie = self.comp18_functie_rcl[regio_nr]
        else:
            account = self.comp25_account_rcl[regio_nr]
            functie = self.comp25_functie_rcl[regio_nr]

        # wordt RCL van de deelcompetitie
        client = Client()
        self._login(client, account)
        self._wissel_naar_functie(client, functie)

        url = self.url_volgende_ronde % deelcomp.pk
        client.post(url, {'snel': 1})

        self._verwerk_mutaties()

    def maak_accounts(self):
        """
            Maak de standaard accounts aan die voor de meeste testen nodig zijn:
                account_admin:  met IT beheer rechten
                account_bb:     met BB rechten

            vhpg is geaccepteerd, dus je kan meteen inloggen op deze accounts met:

                self.e2e_login_and_pass_otp(self.testdata.account_bb)
                self.e2e_wisselnaarrol_bb()
                self.e2e_check_rol('BB')
        """
        # admin
        self.account_admin = self._create_account('admin', 'admin@test.com', 'Admin')
        self.account_admin.is_staff = True
        self.account_admin.is_superuser = True
        self.account_admin.save()

        # maak een BB aan, nodig voor de competitie
        self.account_bb = self._create_account('bb', 'bb@test.com', 'Bond')
        self.account_bb.is_BB = True
        self.account_bb.save()

        self._accepteer_vhpg_voor_alle_accounts()

    def _create_account(self, username, email, voornaam):
        """
            Maak een Account met AccountEmail aan in de database van de website
        """
        account_create(username, voornaam, '', self.WACHTWOORD, email, email_is_bevestigd=True)
        account = Account.objects.get(username=username)

        # zet OTP actief (een test kan deze altijd weer uit zetten)
        account.otp_code = "whatever"
        account.otp_is_actief = True
        account.save()

        return account

    @staticmethod
    def _accepteer_vhpg_voor_alle_accounts():
        """
            Accepteer de VHPG voor alle accounts
        """

        bestaande_account_pks = list(VerklaringHanterenPersoonsgegevens
                                     .objects
                                     .values_list('account__pk', flat=True))

        now = timezone.now()
        bulk = list()
        for account in Account.objects.all():
            if account.pk not in bestaande_account_pks:
                vhpg = VerklaringHanterenPersoonsgegevens(
                            account=account,
                            acceptatie_datum=now)
                bulk.append(vhpg)
                if len(bulk) > 500:         # pragma: no cover
                    VerklaringHanterenPersoonsgegevens.objects.bulk_create(bulk)
                    bulk = list()
        # for

        if len(bulk):
            VerklaringHanterenPersoonsgegevens.objects.bulk_create(bulk)

    def _maak_verenigingen(self):
        """
            Maak in regios 101..107 elk vier verenigingen aan
            Maak in regios 108..116 elk twee verenigingen aan
            Maak in regio 100 twee verenigingen aan

            ver_nr = regio_nr * 10 + volgnummer
                     1053 is dus 3e vereniging in regio 105

            de eerste 3 verenigingen in regio's 101 en 108 gaan in het eerste cluster van die regio
        """
        cluster_regios = list()
        curr_rayon = 0

        bulk = list()
        for regio in NhbRegio.objects.select_related('rayon').order_by('regio_nr'):
            if regio.regio_nr in (101, 107):
                cluster_regios.append(regio)

            aantal = 2
            if 101 <= regio.regio_nr <= 107:
                aantal = 4

            for nr in range(aantal):
                ver_nr = regio.regio_nr * 10 + nr + 1

                # vereniging 0, 1, 2 gaan in een cluster, 3 niet
                if nr >= 3:
                    cluster = None

                ver = NhbVereniging(
                            ver_nr=ver_nr,
                            naam="Club %s" % ver_nr,
                            plaats="Regio %s dorp %s" % (regio.regio_nr, nr+1),
                            regio=regio,
                            # geen secretaris lid
                            geen_wedstrijden=regio.is_administratief)

                bulk.append(ver)
            # for
        # for

        NhbVereniging.objects.bulk_create(bulk)     # 48x
        # print('TestData: created %sx NhbVereniging' % len(bulk))

        for regio in cluster_regios:
            cluster = NhbCluster.objects.filter(regio=regio).order_by('letter')[0]
            self.regio_cluster[regio.regio_nr] = cluster
            for ver in NhbVereniging.objects.filter(regio=regio).order_by('ver_nr')[:3]:
                ver.clusters.add(cluster)
            # for
        # for

    def _maak_leden(self):
        """
            Maak voor elke vereniging een aantal leden aan: een mix van alle wedstrijdklassen en boogtypen.

            Aspirant <13, Aspirant 13-14, Cadet 15-17, Junior 18-20, Senior 21-49, Master 50-59, Veteraan 60+
        """

        huidige_jaar = timezone.now().year
        lid_sinds_datum = datetime.date(year=huidige_jaar - 1, month=11, day=12)

        soorten = [
            # wedstrijdleeftijd, geslacht, voornaam, boogtype
            (10, 'M', 'Asp10', 'R'),
            (10, 'V', 'Asp10', 'R'),
            (11, 'M', 'Asp11', 'R'),
            (12, 'V', 'Asp12', 'R'),
            (13, 'M', 'Asp13', 'R'),
            (14, 'M', 'Cad14', 'R'),
            (14, 'M', 'Cad14b', 'C'),
            (14, 'M', 'Cad15', 'c'),            # kleine letter: geen voorkeur voor de competitie
            (15, 'V', 'Cad15', 'R'),
            (15, 'M', 'Cad15b', 'BB'),
            (15, 'V', 'Cad15b', 'C'),
            (16, 'M', 'Cad16', 'R'),
            (16, 'M', 'Cad16b', 'C'),
            (16, 'M', 'Cad16c', 'BB'),
            (17, 'V', 'Cad17', 'R'),            # account
            (17, 'V', 'Cad17b', 'C'),
            (17, 'V', 'Cad17c', 'BB'),
            (18, 'M', 'Jun18', 'R'),
            (18, 'M', 'Jun18b', 'C'),
            (18, 'M', 'Jun18c', 'BB'),
            (18, 'V', 'Jun18', 'BB'),
            (19, 'V', 'Jun19', 'R'),
            (19, 'V', 'Jun19b', 'C'),           # account
            (20, 'M', 'Jun20', 'R'),
            (20, 'M', 'Jun20b', 'LB'),
            (21, 'V', 'Sen21', 'R'),
            (21, 'V', 'Sen21b', 'C'),
            (22, 'M', 'Sen22', 'R'),
            (22, 'M', 'Sen22b', 'C'),
            (22, 'M', 'Sen23', 'r'),            # kleine letter: geen voorkeur voor de competitie
            (31, 'V', 'Sen31', 'R'),
            (32, 'M', 'Sen32', 'C'),
            (32, 'M', 'Sen32b', 'BB'),          # account
            (33, 'V', 'Sen33', 'R'),
            (33, 'V', 'Sen33b', 'BB'),
            (34, 'M', 'Sen34', 'LB'),           # Sen34 = HWL
            (35, 'V', 'Sen35', 'R'),
            (36, 'M', 'Sen36', 'C'),
            (36, 'M', 'Sen36b', 'BB'),
            (37, 'V', 'Sen37', 'R'),
            (38, 'M', 'Sen38', 'LB'),
            (39, 'V', 'Sen39', 'R'),            # Sen39 = BKO/RKO/RCL
            (40, 'M', 'Sen40', 'C'),
            (41, 'V', 'Sen41', 'R'),
            (42, 'M', 'Sen42', 'R'),
            (42, 'M', 'Sen42b', 'C'),
            (49, 'V', 'Sen49', 'R'),
            (49, 'V', 'Sen49b', 'BB'),
            (50, 'M', 'Mas50', 'R'),            # Mas50 = SEC
            (51, 'V', 'Mas51', 'R'),            # account
            (51, 'V', 'Mas51b', 'C'),
            (51, 'V', 'Mas52', 'r'),            # kleine letter: geen voorkeur voor de competitie
            (59, 'M', 'Mas59', 'R'),
            (59, 'M', 'Mas59b', 'LB'),
            (60, 'V', 'Vet60', 'R'),
            (60, 'V', 'Vet60b', 'C'),
            (60, 'V', 'Vet60c', 'LB'),          # account
            (61, 'M', 'Vet61', 'C'),
            (61, 'M', 'Vet61b', 'C'),
            (80, 'V', 'Vet80', 'R'),
        ]

        geslacht_voornaam2boogtype = dict()
        for _, geslacht, voornaam, boogtype in soorten:
            try:
                _ = geslacht_voornaam2boogtype[geslacht + voornaam]
            except KeyError:
                geslacht_voornaam2boogtype[geslacht + voornaam] = boogtype
            else:
                raise IndexError('TestData: combinatie geslacht %s + voornaam %s komt meerdere keren voor' % (geslacht, voornaam))      # pragma: no cover
        # for

        lid_nr = 300000
        bulk = list()
        for ver in NhbVereniging.objects.all():
            self.ver_sporters[ver.ver_nr] = list()

            for wleeftijd, geslacht, voornaam, _ in soorten:
                lid_nr += 1
                achternaam = "Lid%s van Club%s" % (ver.ver_nr, lid_nr)
                geboortedatum = datetime.date(year=huidige_jaar - wleeftijd, month=3, day=24)

                sporter = Sporter(
                        lid_nr=lid_nr,
                        voornaam=voornaam,
                        achternaam=achternaam,
                        unaccented_naam=voornaam + ' ' + achternaam,
                        email='lid%s@testdata.zz',
                        geboorte_datum=geboortedatum,
                        geslacht=geslacht,
                        para_classificatie='',
                        is_actief_lid=True,
                        sinds_datum=lid_sinds_datum,
                        bij_vereniging=ver,
                        # account
                        lid_tot_einde_jaar=huidige_jaar)
                bulk.append(sporter)
            # for
        # for

        Sporter.objects.bulk_create(bulk)
        # print('TestData: Created %sx Sporter' % len(bulk))
        del bulk

        # maak voor elke Sporter nu de SporterBoog records aan
        boogtypen = list(BoogType.objects.all())

        bulk_voorkeuren = list()
        bulk_sporter = list()
        for sporter in (Sporter
                        .objects
                        .select_related('account',
                                        'bij_vereniging')
                        .all()):

            gewenst_boogtype = geslacht_voornaam2boogtype[sporter.geslacht + sporter.voornaam]

            # voorkeuren
            voorkeuren = SporterVoorkeuren(
                                sporter=sporter)

            if gewenst_boogtype.islower():
                voorkeuren.voorkeur_meedoen_competitie = False
                gewenst_boogtype = gewenst_boogtype.upper()

            # alle junioren willen een eigen blazoen
            if gewenst_boogtype == 'R' and sporter.voornaam.startswith('Jun'):
                voorkeuren.voorkeur_eigen_blazoen = True

            bulk_voorkeuren.append(voorkeuren)
            if len(bulk_voorkeuren) > 500:
                SporterVoorkeuren.objects.bulk_create(bulk_voorkeuren)
                bulk_voorkeuren = list()

            # sporterboog
            for boogtype in boogtypen:
                sporterboog = SporterBoog(
                                    sporter=sporter,
                                    # heeft_interesse=True
                                    # voor_wedstrijd=False
                                    boogtype=boogtype)

                if boogtype.afkorting == gewenst_boogtype:
                    sporterboog.voor_wedstrijd = True

                bulk_sporter.append(sporterboog)

                if len(bulk_sporter) > 500:
                    SporterBoog.objects.bulk_create(bulk_sporter)
                    bulk_sporter = list()
            # for
        # for

        if len(bulk_voorkeuren):
            SporterVoorkeuren.objects.bulk_create(bulk_voorkeuren)
        del bulk_voorkeuren

        if len(bulk_sporter):
            SporterBoog.objects.bulk_create(bulk_sporter)
        del bulk_sporter

    def _maak_accounts_en_functies(self):
        """
            Maak voor elke verenigingen drie functies aan: SEC, HWL, WL

            Maak voor bepaalde leden van de vereniging een account aan
            Koppel deze accounts aan de rollen SEC en HWL
        """

        voornamen = ('Sen34', 'Sen39', 'Mas50',                         # Beheerders: SEC, HWL, WL
                     'Cad17', 'Jun19b', 'Sen32b', 'Mas51', 'Vet60c')    # Sporter accounts

        # maak voor elke vereniging een paar accounts aan
        bulk = list()
        for sporter in Sporter.objects.filter(voornaam__in=voornamen):
            account = Account(
                            username=str(sporter.lid_nr),
                            otp_code=self.OTP_CODE,
                            otp_is_actief=True)
            account.set_password(self.WACHTWOORD)
            bulk.append(account)
        # for

        Account.objects.bulk_create(bulk)
        # print('TestData: created %sx Accounts' % len(bulk))
        del bulk

        # koppel de accounts aan de sporters
        username2account = dict()
        for account in Account.objects.all():
            username2account[account.username] = account
        # for

        for sporter in (Sporter
                        .objects
                        .select_related('bij_vereniging')
                        .filter(voornaam__in=voornamen)):

            account = username2account[str(sporter.lid_nr)]
            sporter.account = account
            sporter.save(update_fields=['account'])

            ver_nr = sporter.bij_vereniging.ver_nr
            if sporter.voornaam == 'Sen34':
                self.account_hwl[ver_nr] = account
            elif sporter.voornaam == 'Mas50':
                self.account_sec[ver_nr] = account
            elif sporter.voornaam == 'Sen39':
                self._accounts_beheerders.append(account)
            else:
                self.ver_sporters[ver_nr].append(sporter)
        # for

        # maak de functies aan
        bulk = list()
        for ver in NhbVereniging.objects.all():
            for rol, beschrijving in (('SEC', 'Secretaris vereniging %s'),
                                      ('HWL', 'Hoofdwedstrijdleider %s'),
                                      ('WL', 'Wedstrijdleider %s')):
                func = Functie(
                            # accounts
                            beschrijving=beschrijving % ver.ver_nr,
                            rol=rol,
                            # bevestigde_email=''
                            # nieuwe_email=''
                            nhb_ver=ver)

                if rol == 'SEC':
                    func.bevestigde_email = 'secretaris.club%s@testdata.zz' % ver.ver_nr

                bulk.append(func)
            # for
        # for

        Functie.objects.bulk_create(bulk)
        # print('TestData: created %sx Functie' % len(bulk))
        del bulk

        # koppel de functies aan de accounts
        for functie in (Functie
                        .objects
                        .select_related('nhb_ver')
                        .filter(rol__in=('SEC', 'HWL'))):
            ver_nr = functie.nhb_ver.ver_nr
            if functie.rol == 'SEC':
                self.functie_sec[ver_nr] = functie
                functie.accounts.add(self.account_sec[ver_nr])
            else:
                self.functie_hwl[ver_nr] = functie
                functie.accounts.add(self.account_hwl[ver_nr])
        # for

    def maak_clubs_en_sporters(self):
        # print('TestData: maak_clubs_en_leden. Counters: NhbVereniging=%s, Sporter=%s' % (
        #                     NhbVereniging.objects.count(), Sporter.objects.count()))
        self._maak_verenigingen()
        self._maak_leden()
        self._maak_accounts_en_functies()
        self._accepteer_vhpg_voor_alle_accounts()

    @staticmethod
    def maak_sporterboog_aanvangsgemiddelden(afstand, ver_nr):
        """ Maak voor de helft van de SporterBoog een AG aan in voorgaand seizoen
            deze kunnen gebruikt worden voor de klassegrenzen en inschrijven.
        """
        ag = 6000       # 6.0
        ag += ver_nr

        bulk = list()
        for sporterboog in SporterBoog.objects.filter(sporter__bij_vereniging__ver_nr=ver_nr):
            # even pk get an AG
            if sporterboog.pk % 1 == 0:
                ag = 6000 if ag > 9800 else ag + 25
                score = Score(type=SCORE_TYPE_INDIV_AG,
                              sporterboog=sporterboog,
                              waarde=ag,
                              afstand_meter=afstand)
                bulk.append(score)

                if len(bulk) > 500:                 # pragma: no cover
                    Score.objects.bulk_create(bulk)
                    bulk = list()
        # for

        if len(bulk):
            Score.objects.bulk_create(bulk)

        # TODO: maak ScoreHist records

    def maak_bondscompetities(self, begin_jaar=None):

        competities_aanmaken(begin_jaar)

        for comp in Competitie.objects.all():
            if comp.afstand == '18':
                self.comp18 = comp
            else:
                self.comp25 = comp
        # for

        for deelcomp in (DeelCompetitie
                         .objects
                         .select_related('competitie',
                                         'nhb_rayon',
                                         'nhb_regio')
                         .all()):
            is_18 = deelcomp.competitie.afstand == '18'

            if deelcomp.laag == LAAG_BK:
                if is_18:
                    self.deelcomp18_bk = deelcomp
                else:
                    self.deelcomp25_bk = deelcomp

            elif deelcomp.laag == LAAG_RK:
                rayon_nr = deelcomp.nhb_rayon.rayon_nr
                if is_18:
                    self.deelcomp18_rk[rayon_nr] = deelcomp
                else:
                    self.deelcomp25_rk[rayon_nr] = deelcomp

            else:   # if deelcomp.laag == LAAG_REGIO:
                regio_nr = deelcomp.nhb_regio.regio_nr
                if is_18:
                    self.deelcomp18_regio[regio_nr] = deelcomp
                else:
                    self.deelcomp25_regio[regio_nr] = deelcomp
        # for

        # zorg dat er accounts gekoppeld zijn aan de functies BKO, RKO, RCL
        accounts = self._accounts_beheerders[:]

        for functie in (Functie
                        .objects
                        .select_related('nhb_regio', 'nhb_rayon')
                        .filter(rol__in=('RCL', 'RKO', 'BKO'))):

            is_18 = functie.comp_type == '18'

            account = accounts.pop(0)
            functie.accounts.add(account)

            if functie.rol == 'RCL':
                regio_nr = functie.nhb_regio.regio_nr
                if is_18:
                    self.comp18_functie_rcl[regio_nr] = functie
                    self.comp18_account_rcl[regio_nr] = account
                else:
                    self.comp25_functie_rcl[regio_nr] = functie
                    self.comp25_account_rcl[regio_nr] = account

            elif functie.rol == 'RKO':
                rayon_nr = functie.nhb_rayon.rayon_nr
                if is_18:
                    self.comp18_functie_rko[rayon_nr] = functie
                    self.comp18_account_rko[rayon_nr] = account
                else:
                    self.comp25_functie_rko[rayon_nr] = functie
                    self.comp25_account_rko[rayon_nr] = account

            else:  # elif functie.rol == 'BKO':
                if is_18:
                    self.comp18_functie_bko = functie
                    self.comp18_account_bko = account
                else:
                    self.comp25_functie_bko = functie
                    self.comp25_account_bko = account

        # for

    def maak_inschrijven_competitie(self, afstand=18, ver_nr=None):
        """ Schrijf alle leden van de vereniging in voor de competitie, voor een specifieke vereniging

            afstand = 18 / 25
            ver_nr = regio_nr * 10 + volgnummer
        """

        if afstand == 18:
            comp = self.comp18 if afstand == 18 else self.comp25
            deelnemers = self.comp18_deelnemers
        else:
            comp = self.comp25
            deelnemers = self.comp25_deelnemers

        url = self.url_inschrijven % comp.pk

        # zet competitie fase B zodat we in mogen schrijven
        zet_competitie_fase(comp, 'B')

        client = Client()

        # log in als HWL van deze vereniging
        self._login(client, self.account_hwl[ver_nr])

        # wissel naar HWL
        self._wissel_naar_functie(client, self.functie_hwl[ver_nr])

        data = dict()
        data['wil_in_team'] = 1
        pks = list()
        for sporterboog in (SporterBoog
                            .objects
                            .select_related('sporter',
                                            'boogtype')
                            .filter(sporter__bij_vereniging__ver_nr=ver_nr,
                                    voor_wedstrijd=True)):

            # lid_100004_boogtype_1
            pk1 = sporterboog.sporter.pk
            pk2 = sporterboog.boogtype.pk
            aanmelding = 'lid_%s_boogtype_%s' % (pk1, pk2)
            data[aanmelding] = 1

            pks.append(sporterboog.pk)
        # for

        resp = client.post(url, data)
        if resp.status_code != 302:             # pragma: no cover
            self._dump_resp(resp)
            raise ValueError('Inschrijven van sporters failed')

        new_deelnemers = (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'klasse')
                          .filter(sporterboog__pk__in=pks))
        deelnemers.extend(new_deelnemers)

    def maak_inschrijven_teamcompetitie(self, afstand, ver_nr):
        """ Schrijf teams in voor de teamcompetitie, voor een specifiek vereniging

            afstand = 18 / 25
            ver_nr = regio_nr * 10 + volgnummer
        """

        ver = NhbVereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        regio_nr = ver.regio.regio_nr

        if afstand == 18:
            deelcomp = self.deelcomp18_regio[regio_nr]
            deelnemers = self.comp18_deelnemers
            deelnemers_team = self.comp18_deelnemers_team
            deelnemers_geen_team = self.comp18_deelnemers_geen_team
            regioteams = self.comp18_regioteams
        else:
            deelcomp = self.deelcomp25_regio[regio_nr]
            deelnemers = self.comp25_deelnemers
            deelnemers_team = self.comp25_deelnemers_team
            deelnemers_geen_team = self.comp25_deelnemers_geen_team
            regioteams = self.comp25_regioteams

        # verdeel de deelnemers per boogtype
        deelnemers_per_boog = dict()   # [boogtype.afkorting] = list(deelnemer)

        for deelnemer in deelnemers:
            if deelnemer.inschrijf_voorkeur_team:
                # print('deelnemer: %s (indiv ag: %s, team ag: %s)' % (deelnemer, deelnemer.ag_voor_indiv, deelnemer.ag_voor_team))
                afkorting = deelnemer.sporterboog.boogtype.afkorting
                try:
                    deelnemers_per_boog[afkorting].append(deelnemer)
                except KeyError:
                    deelnemers_per_boog[afkorting] = [deelnemer]

                deelnemers_team.append(deelnemer)
            else:
                deelnemers_geen_team.append(deelnemer)
        # for

        # zet 1x BB en 1x LB in een recurve team
        deelnemers_per_boog['R'].append(deelnemers_per_boog['BB'].pop(0))
        deelnemers_per_boog['R'].append(deelnemers_per_boog['LB'].pop(0))

        afkorting2teamtype = dict()
        for teamtype in TeamType.objects.all():
            afkorting2teamtype[teamtype.afkorting] = teamtype
        # for

        bulk = list()
        for afkorting, deelnemers in deelnemers_per_boog.items():
            aantal = len(deelnemers)
            while aantal > 0:
                aantal -= 4
                next_nr = len(bulk) + 1
                team = RegiocompetitieTeam(
                            deelcompetitie=deelcomp,
                            vereniging=ver,
                            volg_nr=next_nr,
                            team_type=afkorting2teamtype[afkorting],
                            team_naam='%s-%s-%s' % (ver_nr, next_nr, afkorting))
                bulk.append(team)
            # while
        # for

        RegiocompetitieTeam.objects.bulk_create(bulk)

        # alle teams moeten in een klasse (maakt niet veel uit welke)
        team_klasse = CompetitieKlasse.objects.exclude(team=None).filter(competitie=deelcomp.competitie)[0]

        # koppel de sporters aan het team
        for team in (RegiocompetitieTeam
                     .objects
                     .select_related('team_type')
                     .filter(deelcompetitie=deelcomp,
                             vereniging=ver)):

            # selecteer een aantal deelnemers voor dit team (1, 2, 3 of 4 sporters)
            afkorting = team.team_type.afkorting
            deelnemers = deelnemers_per_boog[afkorting][:4]
            deelnemers_per_boog[afkorting] = deelnemers_per_boog[afkorting][len(deelnemers):]

            # bereken de team sterkte
            team.aanvangsgemiddelde = sum([deelnemer.ag_voor_team for deelnemer in deelnemers])
            team.klasse = team_klasse
            team.save(update_fields=['aanvangsgemiddelde', 'klasse'])

            team.gekoppelde_schutters.set(deelnemers)

            regioteams.append(team)
        # for

    def maak_poules(self, deelcomp):
        """ Maak poules en vul deze met teams """

        if deelcomp.competitie.afstand == '18':
            regioteams = self.comp18_regioteams
            poules = self.comp18_poules
        else:
            regioteams = self.comp25_regioteams
            poules = self.comp25_poules

        # maak per boogtype 1 poule aan
        done = list()
        bulk = list()
        for team in regioteams:
            if team.deelcompetitie == deelcomp:
                afkorting = team.team_type.afkorting
                if afkorting not in done:
                    poule = RegiocompetitieTeamPoule(
                                    deelcompetitie=deelcomp,
                                    # teams,
                                    beschrijving="Poule %s team type %s" % (deelcomp, team.team_type.beschrijving))

                    bulk.append(poule)
                    done.append(afkorting)
        # for

        RegiocompetitieTeamPoule.objects.bulk_create(bulk)

        for poule in (RegiocompetitieTeamPoule
                      .objects
                      .select_related('deelcompetitie',
                                      'deelcompetitie__competitie')
                      .filter(deelcompetitie=deelcomp)):

            pks = list()
            for team in regioteams:
                if team.deelcompetitie == deelcomp:
                    if poule.beschrijving.endswith(team.team_type.beschrijving):
                        pks.append(team.pk)
            # for

            pks = pks[:8]       # maximaal 8 teams in een poule
            poule.teams.set(pks)

            poules.append(poule)
        # for


def account_vhpg_is_geaccepteerd(account):
    """ onthoud dat de vhpg net geaccepteerd is door de gebruiker
    """
    # Deze functie wordt aangeroepen vanuit een POST handler
    # concurrency beveiliging om te voorkomen dat 2 records gemaakt worden
    obj, created = (VerklaringHanterenPersoonsgegevens
                    .objects
                    .update_or_create(account=account,
                                      defaults={'acceptatie_datum': timezone.now()}))


# end of file
