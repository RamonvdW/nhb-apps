# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Routines om de database te vullen met een test set die gebruikt wordt in vele van de test cases """

from django.test import Client
from django.core import management
from django.utils import timezone
from Account.models import Account, account_create, AccountEmail
from BasisTypen.models import BoogType, TeamType
from Competitie.models import (Competitie, CompetitieKlasse, DeelCompetitie, LAAG_BK, LAAG_RK,
                               RegioCompetitieSchutterBoog,
                               RegiocompetitieTeam, RegiocompetitieTeamPoule,
                               KampioenschapSchutterBoog, KampioenschapTeam)
from Competitie.operations import competities_aanmaken
from Competitie.test_competitie import zet_competitie_fase
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from NhbStructuur.models import NhbRegio, NhbCluster, NhbVereniging
from Score.models import Score, SCORE_TYPE_INDIV_AG, ScoreHist
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from bs4 import BeautifulSoup
from decimal import Decimal
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

    url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/'  # comp_pk
    url_account_login = '/account/login/'
    url_check_otp = '/functie/otp-controle/'
    url_activeer_functie = '/functie/activeer-functie/%s/'
    url_wissel_van_rol = '/functie/wissel-van-rol/'
    url_volgende_ronde = '/bondscompetities/regio/%s/team-ronde/'   # deelcomp_pk

    def __init__(self):
        self.account_admin = None
        self.account_bb = None

        # verenigingen
        self.regio_ver_nrs = dict()             # [regio_nr] = list(ver_nrs)
        self.vereniging = dict()                # [ver_nr] = NhbVereniging()

        self.account_sec = dict()               # [ver_nr] = Account
        self.account_hwl = dict()               # [ver_nr] = Account

        self.functie_sec = dict()               # [ver_nr] = Functie
        self.functie_hwl = dict()               # [ver_nr] = Functie

        # leden
        self.ver_sporters = dict()              # [ver_nr] = list(Sporter)
        self.ver_sporters_met_account = dict()  # [ver_nr] = list(Sporter) met sporter.account != None

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

        self.comp18_klassen_indiv = dict()      # [boogtype afkorting] = [klasse, ...]
        self.comp25_klassen_indiv = dict()      # [boogtype afkorting] = [klasse, ...]

        self.comp18_klassen_team = dict()       # [teamtype afkorting] = [klasse, ...]
        self.comp25_klassen_team = dict()       # [teamtype afkorting] = [klasse, ...]

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

        # aangemaakte RK teams
        self.comp18_kampioenschapteams = list()
        self.comp25_kampioenschapteams = list()

        # regiokampioenen
        self.comp18_regiokampioenen = list()    # [KampioenschapSchutterBoog met kampioen_label != '', ...]
        self.comp25_regiokampioenen = list()    # [KampioenschapSchutterBoog met kampioen_label != '', ...]

        self._accounts_beheerders = list()      # 1 per vereniging, voor BKO, RKO, RCL

        self.afkorting2teamtype = dict()        # [team afkorting] = TeamType()
        self.afkorting2boogtype = dict()        # [boog afkorting] = BoogType()

        for teamtype in TeamType.objects.all():
            self.afkorting2teamtype[teamtype.afkorting] = teamtype
        # for
        del teamtype
        for boogtype in BoogType.objects.all():
            self.afkorting2boogtype[boogtype.afkorting] = boogtype
        # for
        del boogtype

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
                if len(bulk) > 150:         # pragma: no cover
                    VerklaringHanterenPersoonsgegevens.objects.bulk_create(bulk)
                    bulk = list()
        # for

        if len(bulk) > 0:
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

        for ver in bulk:
            self.vereniging[ver.ver_nr] = ver
        # for

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
            # wedstrijdleeftijd, geslacht, voornaam, boogtype, account
            (10, 'M', 'Asp10',  'R',  False),
            (10, 'V', 'Asp10',  'R',  False),
            (11, 'M', 'Asp11',  'R',  False),
            (12, 'V', 'Asp12',  'R',  False),
            (13, 'M', 'Asp13',  'R',  False),
            (14, 'M', 'Cad14',  'R',  False),
            (14, 'M', 'Cad14b', 'C',  False),
            (14, 'M', 'Cad15',  'c',  False),           # kleine letter: geen voorkeur voor de competitie
            (15, 'V', 'Cad15',  'R',  False),
            (15, 'M', 'Cad15b', 'BB', False),
            (15, 'V', 'Cad15b', 'C',  False),
            (16, 'M', 'Cad16',  'R',  False),
            (16, 'M', 'Cad16b', 'C',  False),
            (16, 'M', 'Cad16c', 'BB', False),
            (17, 'V', 'Cad17',  'R',  True),            # account
            (17, 'V', 'Cad17b', 'C',  False),
            (17, 'V', 'Cad17c', 'BB', False),
            (18, 'M', 'Jun18',  'R',  False),
            (18, 'M', 'Jun18b', 'C',  False),
            (18, 'M', 'Jun18c', 'BB', False),
            (18, 'V', 'Jun18',  'BB', False),
            (19, 'V', 'Jun19',  'R',  False),
            (19, 'V', 'Jun19b', 'C',  True),            # account
            (20, 'M', 'Jun20',  'R',  False),
            (20, 'M', 'Jun20b', 'LB', False),
            (21, 'V', 'Sen21',  'R',  False),
            (21, 'V', 'Sen21b', 'C',  False),
            (22, 'M', 'Sen22',  'R',  False),
            (22, 'M', 'Sen22b', 'C',  False),
            (22, 'M', 'Sen23',  'r',  False),           # kleine letter: geen voorkeur voor de competitie
            (31, 'V', 'Sen31',  'R',  False),
            (32, 'M', 'Sen32',  'C',  False),
            (32, 'M', 'Sen32b', 'BB', True),            # account
            (33, 'V', 'Sen33',  'R',  False),
            (33, 'V', 'Sen33b', 'BB', False),
            (34, 'M', 'Sen34',  'LB', True),            # Sen34 = HWL
            (35, 'V', 'Sen35',  'R',  False),
            (36, 'M', 'Sen36',  'C',  False),
            (36, 'M', 'Sen36b', 'BB', False),
            (37, 'V', 'Sen37',  'R',  False),
            (38, 'M', 'Sen38',  'LB', False),
            (39, 'V', 'Sen39',  'R',  True),            # Sen39 = BKO/RKO/RCL
            (40, 'M', 'Sen40',  'C',  False),
            (41, 'V', 'Sen41',  'R',  False),
            (42, 'M', 'Sen42',  'R',  False),
            (42, 'M', 'Sen42b', 'C',  False),
            (49, 'V', 'Sen49',  'R',  False),
            (49, 'V', 'Sen49b', 'BB', False),
            (50, 'M', 'Mas50',  'R',  True),            # Mas50 = SEC
            (51, 'V', 'Mas51',  'R',  True),            # account
            (51, 'V', 'Mas51b', 'C',  False),
            (51, 'V', 'Mas52',  'r',  False),           # kleine letter: geen voorkeur voor de competitie
            (59, 'M', 'Mas59',  'R',  False),
            (59, 'M', 'Mas59b', 'LB', False),
            (60, 'V', 'Vet60',  'R',  False),
            (60, 'V', 'Vet60b', 'C',  False),
            (60, 'V', 'Vet60c', 'LB', True),            # account
            (61, 'M', 'Vet61',  'C',  False),
            (61, 'M', 'Vet61b', 'C',  False),
            (80, 'V', 'Vet80',  'R',  False),
        ]

        geslacht_voornaam2boogtype = dict()
        for _, geslacht, voornaam, boogtype, _ in soorten:
            try:
                _ = geslacht_voornaam2boogtype[geslacht + voornaam]
            except KeyError:
                geslacht_voornaam2boogtype[geslacht + voornaam] = boogtype
            else:
                raise IndexError('TestData: combinatie geslacht %s + voornaam %s komt meerdere keren voor' % (geslacht, voornaam))      # pragma: no cover
        # for

        # maak voor elke vereniging een paar accounts aan
        lid_nr = 300000
        bulk = list()
        for ver in self.vereniging.values():

            try:
                self.regio_ver_nrs[ver.regio.regio_nr].append(ver.ver_nr)
            except KeyError:
                self.regio_ver_nrs[ver.regio.regio_nr] = [ver.ver_nr]

            for _, _, voornaam, _, maak_account in soorten:
                lid_nr += 1

                if maak_account:
                    account = Account(
                                username=str(lid_nr),
                                otp_code=self.OTP_CODE,
                                otp_is_actief=True)
                    account.set_password(self.WACHTWOORD)
                    bulk.append(account)

                    if len(bulk) > 100:                                        # pragma: no branch
                        Account.objects.bulk_create(bulk)

                        # maak e-mails aan
                        bulk2 = list()
                        for account in bulk:
                            # let op: e-mailadres moet overeenkomen met het Sporter.email
                            email = AccountEmail(
                                        account=account,
                                        email_is_bevestigd=True,
                                        bevestigde_email='lid%s@testdata.zz' % account.username)
                            bulk2.append(email)
                        # for

                        AccountEmail.objects.bulk_create(bulk2)
                        del bulk2

                        bulk = list()
            # for
        # for

        if len(bulk) > 0:                           # pragma: no branch
            Account.objects.bulk_create(bulk)

            # maak e-mails aan
            bulk2 = list()
            for account in bulk:
                email = AccountEmail(
                            account=account,
                            email_is_bevestigd=True,
                            bevestigde_email='lid%s@testdata.zz' % account.username)
                bulk2.append(email)
            # for

            AccountEmail.objects.bulk_create(bulk2)
            del bulk2

        del bulk

        # cache de aangemaakte accounts
        lid_nr2account = dict()
        for account in Account.objects.all():
            lid_nr2account[account.username] = account
        # for

        lid_nr = 300000
        bulk = list()
        for ver in self.vereniging.values():

            self.ver_sporters[ver.ver_nr] = list()
            self.ver_sporters_met_account[ver.ver_nr] = list()

            for wleeftijd, geslacht, voornaam, _, _ in soorten:
                lid_nr += 1
                achternaam = "Lid%s van Club%s" % (ver.ver_nr, lid_nr)
                geboortedatum = datetime.date(year=huidige_jaar - wleeftijd, month=3, day=24)

                try:
                    account = lid_nr2account[str(lid_nr)]
                except KeyError:
                    account = None

                sporter = Sporter(
                        lid_nr=lid_nr,
                        voornaam=voornaam,
                        achternaam=achternaam,
                        unaccented_naam=voornaam + ' ' + achternaam,
                        email='lid%s@testdata.zz' % lid_nr,
                        geboorte_datum=geboortedatum,
                        geslacht=geslacht,
                        para_classificatie='',
                        is_actief_lid=True,
                        sinds_datum=lid_sinds_datum,
                        bij_vereniging=ver,
                        account=account,
                        lid_tot_einde_jaar=huidige_jaar)
                bulk.append(sporter)

                if len(bulk) > 250:                                        # pragma: no branch
                    Sporter.objects.bulk_create(bulk)
                    bulk = list()
            # for
        # for

        if len(bulk) > 0:                           # pragma: no branch
            Sporter.objects.bulk_create(bulk)
        del bulk
        del lid_nr2account

        # maak voor elke Sporter nu de SporterBoog records aan
        boogtypen = self.afkorting2boogtype.values()

        bulk_voorkeuren = list()
        bulk_sporter = list()
        for sporter in (Sporter
                        .objects
                        .select_related('account',
                                        'bij_vereniging')
                        .all()):

            ver_nr = sporter.bij_vereniging.ver_nr

            self.ver_sporters[ver_nr].append(sporter)
            if sporter.account:
                self.ver_sporters_met_account[ver_nr].append(sporter)

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
            if len(bulk_voorkeuren) > 100:
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

                if len(bulk_sporter) > 250:
                    SporterBoog.objects.bulk_create(bulk_sporter)
                    bulk_sporter = list()
            # for
        # for

        if len(bulk_voorkeuren):                            # pragma: no branch
            SporterVoorkeuren.objects.bulk_create(bulk_voorkeuren)
        del bulk_voorkeuren

        if len(bulk_sporter):                               # pragma: no branch
            SporterBoog.objects.bulk_create(bulk_sporter)
        del bulk_sporter

    def _maak_accounts_en_functies(self):
        """
            Maak voor elke verenigingen drie functies aan: SEC, HWL, WL

            Maak voor bepaalde leden van de vereniging een account aan
            Koppel deze accounts aan de rollen SEC en HWL
        """

        voornamen = ('Sen34', 'Sen39', 'Mas50')   # Beheerders: HWL, "beheerder", SEC

        for sporter in (Sporter
                        .objects
                        .select_related('bij_vereniging',
                                        'account')
                        .filter(voornaam__in=voornamen)):

            ver_nr = sporter.bij_vereniging.ver_nr

            if sporter.voornaam == 'Sen34':
                self.account_hwl[ver_nr] = sporter.account
            elif sporter.voornaam == 'Mas50':
                self.account_sec[ver_nr] = sporter.account
            else:   # if sporter.voornaam == 'Sen39':
                # voor gebruik als BKO, RKO, RCL
                self._accounts_beheerders.append(sporter.account)
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

                if len(bulk) > 150:                           # pragma: no branch
                    Functie.objects.bulk_create(bulk)
                    bulk = list()
            # for
        # for

        if len(bulk) > 0:                           # pragma: no branch
            Functie.objects.bulk_create(bulk)
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
            deze kunnen gebruikt worden voor de klassengrenzen en inschrijven.
        """
        ag = 6000       # 6.0
        ag += ver_nr

        bulk = list()
        for sporterboog in (SporterBoog
                            .objects
                            .filter(sporter__bij_vereniging__ver_nr=ver_nr,
                                    voor_wedstrijd=True)):
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

                    bulk2 = list()
                    for score in bulk:
                        hist = ScoreHist(score=score,
                                         oude_waarde=0,
                                         nieuwe_waarde=score.waarde,
                                         # when = auto-set
                                         # door_account=None,
                                         notitie='Testdata')
                        bulk2.append(hist)
                    # for
                    ScoreHist.objects.bulk_create(bulk2)
                    del bulk2

                    bulk = list()
        # for

        if len(bulk):                           # pragma: no branch
            Score.objects.bulk_create(bulk)

            bulk2 = list()
            for score in bulk:
                hist = ScoreHist(score=score,
                                 oude_waarde=0,
                                 nieuwe_waarde=score.waarde,
                                 # when = auto-set
                                 # door_account=None,
                                 notitie='Testdata')
                bulk2.append(hist)
            # for
            ScoreHist.objects.bulk_create(bulk2)
            del bulk2

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

        for klasse in (CompetitieKlasse
                       .objects
                       .select_related('competitie',
                                       'indiv__boogtype',
                                       'team__team_type')
                       .all()):

            if klasse.indiv:
                afkorting = klasse.indiv.boogtype.afkorting
                if klasse.competitie.afstand == '18':
                    klassen = self.comp18_klassen_indiv
                else:
                    klassen = self.comp25_klassen_indiv

            else:
                afkorting = klasse.team.team_type.afkorting
                if klasse.competitie.afstand == '18':
                    klassen = self.comp18_klassen_team
                else:
                    klassen = self.comp25_klassen_team

            try:
                klassen[afkorting].append(klasse)
            except KeyError:
                klassen[afkorting] = [klasse]
        # for

    def maak_inschrijvingen_regiocompetitie(self, afstand=18, ver_nr=None):
        """ Schrijf alle leden van de vereniging in voor de competitie, voor een specifieke vereniging

            afstand = 18 / 25
            ver_nr = regio_nr * 10 + volgnummer
        """

        if afstand == 18:
            comp = self.comp18
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
                          .select_related('sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'bij_vereniging',
                                          'indiv_klasse')
                          .filter(deelcompetitie__competitie=comp,
                                  sporterboog__pk__in=pks))

        deelnemers.extend(new_deelnemers)

    def maak_inschrijvingen_regio_teamcompetitie(self, afstand, ver_nr):
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
            klassen = self.comp18_klassen_team
            regioteams = self.comp18_regioteams
        else:
            deelcomp = self.deelcomp25_regio[regio_nr]
            deelnemers = self.comp25_deelnemers
            deelnemers_team = self.comp25_deelnemers_team
            deelnemers_geen_team = self.comp25_deelnemers_geen_team
            klassen = self.comp25_klassen_team
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

        bulk = list()
        for afkorting, deelnemers in deelnemers_per_boog.items():

            # alle teams moeten in een klasse (maakt niet veel uit welke)
            if afkorting in ('R', 'BB'):
                afkorting += '2'        # R2 / BB2
            klasse = klassen[afkorting][0]

            aantal = len(deelnemers)
            while aantal > 0:
                aantal -= 4
                next_nr = len(bulk) + 1

                team = RegiocompetitieTeam(
                            deelcompetitie=deelcomp,
                            vereniging=ver,
                            volg_nr=next_nr,
                            team_type=self.afkorting2teamtype[afkorting],
                            team_naam='%s-%s-%s' % (ver_nr, next_nr, afkorting),
                            klasse=klasse)
                bulk.append(team)
            # while
        # for

        RegiocompetitieTeam.objects.bulk_create(bulk)

        # koppel de sporters aan het team
        for team in (RegiocompetitieTeam
                     .objects
                     .select_related('team_type')
                     .filter(deelcompetitie=deelcomp,
                             vereniging=ver)):

            afkorting = team.team_type.afkorting

            # vertaal team type naar boog type
            if afkorting in ('R2', 'BB2'):
                afkorting = afkorting[:-1]      # R2/BB2 -> R/BB

            # selecteer de volgende 4 sporters voor dit team
            deelnemers = deelnemers_per_boog[afkorting][:4]
            deelnemers_per_boog[afkorting] = deelnemers_per_boog[afkorting][len(deelnemers):]

            # bereken de team sterkte
            team.aanvangsgemiddelde = sum([deelnemer.ag_voor_team for deelnemer in deelnemers])     # TODO: top 3
            team.save(update_fields=['aanvangsgemiddelde'])

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
                      .select_related('deelcompetitie__competitie')
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

    def maak_rk_deelnemers(self, afstand, ver_nr, regio_nr):
        """ Maak de RK deelnemers aan, alsof ze doorgestroomd zijn vanuit de regiocompetitie
            rank en volgorde wordt ingevuld door maak_label_regiokampioenen

            afstand = 18 / 25
            ver_nr = regio_nr * 10 + volgnummer
        """

        ver = self.vereniging[ver_nr]

        if afstand == 18:
            deelcomp_rk = self.deelcomp18_rk[ver.regio.rayon.rayon_nr]
            klassen = self.comp18_klassen_indiv
        else:
            deelcomp_rk = self.deelcomp25_rk[ver.regio.rayon.rayon_nr]
            klassen = self.comp25_klassen_indiv

        ag = 7000       # 7.0
        ag += ver_nr

        max_ag = 9000
        if (regio_nr % 4) == 0:
            max_ag = 9500           # zorg dat de regiokampioenen niet allemaal bovenaan staan

        bulk = list()
        for sporterboog in (SporterBoog
                            .objects
                            .filter(sporter__bij_vereniging__ver_nr=ver_nr,
                                    voor_wedstrijd=True)
                            .select_related('boogtype')):

            ag = 7000 if ag > max_ag else ag + 25

            afk = sporterboog.boogtype.afkorting
            klasse = klassen[afk][0]

            deelnemer = KampioenschapSchutterBoog(
                                deelcompetitie=deelcomp_rk,
                                sporterboog=sporterboog,
                                klasse=klasse,
                                bij_vereniging=sporterboog.sporter.bij_vereniging,
                                kampioen_label='',
                                volgorde=0,
                                rank=0,
                                # bevestiging_gevraagd_op (date/time) = None
                                # deelname=DEELNAME_ONBEKEND
                                gemiddelde=Decimal(ag) / 1000)
            bulk.append(deelnemer)
        # for

        KampioenschapSchutterBoog.objects.bulk_create(bulk)
        del bulk

    def maak_label_regiokampioenen(self, afstand, regio_nr_begin, regio_nr_einde):
        """ label de regiokampioen van elke wedstrijdklasse voor de gevraagde regios en competitie """
        if afstand == 18:
            regiokampioenen = self.comp18_regiokampioenen
        else:
            regiokampioenen = self.comp25_regiokampioenen

        regio_nrs = [regio_nr for regio_nr in range(regio_nr_begin, regio_nr_einde + 1)]

        volgorde_per_klasse = dict()    # [klasse.pk] = teller
        klasse_regio_done = list()      # [(klasse.pk, regio_nr), ...]

        for kampioen in (KampioenschapSchutterBoog
                         .objects
                         .filter(deelcompetitie__competitie__afstand=afstand,
                                 bij_vereniging__regio__regio_nr__in=regio_nrs)
                         .select_related('klasse',
                                         'bij_vereniging__regio')
                         .order_by('-gemiddelde',            # hoogste eerst
                                   'klasse')):

            klasse_pk = kampioen.klasse.pk
            regio_nr = kampioen.bij_vereniging.regio.regio_nr

            try:
                volgorde = volgorde_per_klasse[klasse_pk] + 1
            except KeyError:
                volgorde = 1

            kampioen.rank = kampioen.volgorde = volgorde_per_klasse[klasse_pk] = volgorde

            tup = (klasse_pk, regio_nr)

            if tup not in klasse_regio_done:
                klasse_regio_done.append(tup)

                # verklaar deze sporter kampioen van deze regio
                kampioen.kampioen_label = "Kampioen regio %s" % regio_nr
                regiokampioenen.append(kampioen)

            kampioen.save(update_fields=['kampioen_label', 'rank', 'volgorde'])
        # for

    def maak_inschrijvingen_rk_teamcompetitie(self, afstand, ver_nr, ook_incomplete_teams=True):
        """ maak voor deze vereniging een paar teams aan voor de open RK teams inschrijving """

        ver = NhbVereniging.objects.select_related('regio__rayon').get(ver_nr=ver_nr)
        rayon_nr = ver.regio.rayon.rayon_nr

        if afstand == 18:
            deelcomp_rk = self.deelcomp18_rk[rayon_nr]
            deelnemers = self.comp18_deelnemers
            rk_teams = self.comp18_kampioenschapteams
        else:
            deelcomp_rk = self.deelcomp25_rk[rayon_nr]
            deelnemers = self.comp25_deelnemers
            rk_teams = self.comp25_kampioenschapteams

        # verdeel de deelnemers per boogtype
        deelnemers_per_boog = dict()   # [boogtype.afkorting] = list(deelnemer)

        for deelnemer in deelnemers:
            if deelnemer.inschrijf_voorkeur_team and deelnemer.bij_vereniging.ver_nr == ver_nr:
                # print('deelnemer: %s (indiv ag: %s, team ag: %s)' % (deelnemer, deelnemer.ag_voor_indiv, deelnemer.ag_voor_team))
                afkorting = deelnemer.sporterboog.boogtype.afkorting
                try:
                    deelnemers_per_boog[afkorting].append(deelnemer)
                except KeyError:
                    deelnemers_per_boog[afkorting] = [deelnemer]
        # for

        # zet 1x BB en 1x LB in een recurve team
        if 'BB' in deelnemers_per_boog and len(deelnemers_per_boog['BB']) > 0:
            deelnemers_per_boog['R'].append(deelnemers_per_boog['BB'].pop(0))

        if 'LB' in deelnemers_per_boog and len(deelnemers_per_boog['LB']) > 0:
            deelnemers_per_boog['R'].append(deelnemers_per_boog['LB'].pop(0))

        ag = 21.0
        ag_step = 0.72

        bulk = list()
        nieuwe_teams = list()
        for afkorting, deelnemers in deelnemers_per_boog.items():

            # vertaal boogtype naar teamtype
            if afkorting in ('R', 'BB'):
                afkorting += '2'

            aantal = len(deelnemers)
            while aantal > 0:
                aantal -= 4
                next_nr = len(bulk) + 1

                koppel = deelnemers[:4]
                deelnemers = deelnemers[4:]

                if ook_incomplete_teams or len(koppel) >= 3:
                    # ags = [deelnemer.gemiddelde for deelnemer in koppel]
                    # ags.sort(reverse=True)      # hoogste eerst
                    # ag = sum(ags[:3])           # beste 3
                    ag += ag_step
                    if ag > 28.0:
                        ag_step = -0.84
                    elif ag < 19.0:             # pragma: no cover
                        ag_step = 0.57

                    team = KampioenschapTeam(
                                deelcompetitie=deelcomp_rk,
                                vereniging=ver,
                                volg_nr=next_nr,
                                team_type=self.afkorting2teamtype[afkorting],
                                team_naam='rk-%s-%s-%s' % (ver_nr, next_nr, afkorting),
                                # klasse wordt later bepaald door de BKO
                                aanvangsgemiddelde=ag)

                    bulk.append(team)

                    tup = (team, koppel)
                    nieuwe_teams.append(tup)
            # while
        # for

        KampioenschapTeam.objects.bulk_create(bulk)

        for team, koppel in nieuwe_teams:
            # tijdelijke_schutters = models.ManyToManyField(RegioCompetitieSchutterBoog,
            # gekoppelde_schutters = models.ManyToManyField(KampioenschapSchutterBoog,

            team.tijdelijke_schutters.set(koppel)
            rk_teams.append(team)
        # for

    def geef_rk_team_tijdelijke_sporters_genoeg_scores(self, afstand, ver_nr):
        if afstand == 18:
            rk_teams = self.comp18_kampioenschapteams       # list of KampioenschapTeam
        else:
            rk_teams = self.comp25_kampioenschapteams

        gem = 7.0
        step = 0.12

        for team in rk_teams:
            if team.vereniging.ver_nr == ver_nr:
                for deelnemer in team.tijdelijke_schutters.all():
                    deelnemer.aantal_scores = 6
                    deelnemer.gemiddelde = gem
                    deelnemer.save(update_fields=['aantal_scores', 'gemiddelde'])

                    gem += step
                    if gem > 9.7:
                        step = -0.34
                    elif gem < 5.0:
                        step = 0.23

                    # afronden op 3 decimalen (anders gebeurt dat tijdens opslaan in database)
                    gem = round(gem, 3)
                # for
        # for

    def geef_regio_deelnemers_genoeg_scores_voor_rk(self, afstand):
        if afstand == 18:
            deelnemers = self.comp18_deelnemers
        else:
            deelnemers = self.comp25_deelnemers

        gem = 7.0
        step = 0.12

        for deelnemer in deelnemers:
            deelnemer.aantal_scores = 6
            deelnemer.gemiddelde = gem
            deelnemer.save(update_fields=['aantal_scores', 'gemiddelde'])

            print(deelnemer, gem)
            gem += step
            if gem > 9.7:
                step = -0.34
            elif gem < 5.0:
                step = 0.23

            # afronden op 3 decimalen (anders gebeurt dat tijdens opslaan in database)
            gem = round(gem, 3)
        # for

# end of file
