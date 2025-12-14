# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Routines om de database te vullen met een test set die gebruikt wordt in vele van de test cases """

from django.test import Client
from django.core import management
from django.utils import timezone
from Account.models import Account
from Account.operations import account_create
from BasisTypen.definities import (GESLACHT_ANDERS,
                                   ORGANISATIE_WA, ORGANISATIE_KHSN, ORGANISATIE_IFAA,
                                   MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT,
                                   SCHEIDS_NIET, SCHEIDS_BOND, SCHEIDS_VERENIGING, SCHEIDS_INTERNATIONAAL)
from BasisTypen.operations import get_organisatie_boogtypen, get_organisatie_teamtypen
from Competitie.definities import DEEL_BK, DEELNAME_JA, DEELNAME_NEE, DEELNAME_ONBEKEND, KAMP_RANK_RESERVE
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               Regiocompetitie, RegiocompetitieSporterBoog,
                               RegiocompetitieTeam, RegiocompetitieTeamPoule,
                               Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam)
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_inschrijven
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Geo.models import Rayon, Regio, Cluster
from Locatie.models import WedstrijdLocatie
from Score.definities import AG_DOEL_INDIV
from Score.models import Aanvangsgemiddelde, AanvangsgemiddeldeHist
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from Vereniging.models import Vereniging
from bs4 import BeautifulSoup
from decimal import Decimal
import datetime
import pyotp
import io

# fixtures zijn overwogen, maar zijn lastig te onderhouden en geven geen recente datums (zoals voor VHPG)

MIN_LID_NR = 300000
MIN_VER_NR = 3000


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

    # sterk genoeg default wachtwoord
    WACHTWOORD = "qewretrytuyi"     # noqa

    url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/'  # comp_pk
    url_account_login = '/account/login/'
    url_check_otp = '/account/otp-controle/'
    url_activeer_functie = '/functie/activeer-functie/%s/'
    url_wissel_van_rol = '/functie/wissel-van-rol/'
    url_volgende_ronde = '/bondscompetities/regio/%s/team-ronde/'   # deelcomp_pk

    leden = [
        # wedstrijdleeftijd, geslacht, voornaam, boogtype, flags:
        #                             (account, voorkeur_rk/bk, para_code, voorwerpen, notitie, scheids)
        (10, 'M', 'Asp10',  'R',      (False, True,  '',    False, 0, 0)),
        (10, 'V', 'Asp10',  'R',      (False, True,  '',    False, 0, 0)),
        (11, 'M', 'Asp11',  'R',      (False, True,  '',    False, 0, 0)),
        (12, 'V', 'Asp12',  'R',      (False, True,  '',    False, 0, 0)),
        (13, 'M', 'Asp13',  'R',      (False, True,  '',    False, 0, 0)),
        (14, 'M', 'Cad14',  'R',      (False, True,  '',    False, 0, 0)),
        (14, 'M', 'Cad14b', 'C',      (False, True,  '',    False, 0, 0)),
        (14, 'M', 'Cad15',  'c',      (False, True,  '',    False, 0, 0)),      # kleine c: geen voorkeur competitie
        (15, 'V', 'Cad15',  'R',      (False, True,  '',    False, 0, 0)),
        (15, 'M', 'Cad15b', 'BB',     (False, True,  '',    False, 0, 0)),
        (15, 'V', 'Cad15b', 'C',      (False, True,  '',    False, 0, 0)),
        (16, 'M', 'Cad16',  'R',      (False, True,  '',    False, 0, 0)),
        (16, 'M', 'Cad16b', 'C',      (False, True,  '',    False, 0, 0)),
        (16, 'M', 'Cad16c', 'BB',     (False, True,  '',    False, 0, 0)),
        (17, 'V', 'Cad17',  'R',      (True,  True,  '',    False, 1, 0)),      # account
        (17, 'V', 'Cad17b', 'C',      (False, True,  '',    False, 0, 0)),
        (17, 'V', 'Cad17c', 'BB',     (False, True,  '',    False, 0, 0)),
        (18, 'M', 'Jun18',  'R',      (False, True,  '',    False, 0, 0)),
        (18, 'M', 'Jun18b', 'C',      (False, True,  '',    False, 0, 0)),
        (18, 'M', 'Jun18c', 'BB',     (False, True,  '',    False, 0, 0)),
        (18, 'V', 'Jun18',  'BB',     (False, True,  '',    False, 0, 0)),
        (19, 'V', 'Jun19',  'R',      (False, True,  '',    False, 0, 0)),
        (19, 'V', 'Jun19b', 'C',      (True,  True,  '',    False, 0, 3)),      # SR3 + account
        (20, 'M', 'Jun20',  'R',      (False, True,  '',    False, 0, 3)),      # SR3
        (20, 'M', 'Jun20b', 'LB',     (False, True,  '',    False, 0, 0)),
        (21, 'V', 'Sen21',  'R+C',    (False, True,  '',    False, 0, 0)),      # schiet twee bogen
        (21, 'V', 'Sen21b', 'C',      (False, True,  'DIS', False, 0, 0)),
        (22, 'M', 'Sen22',  'R',      (False, True,  'DIS', False, 1, 0)),
        (22, 'M', 'Sen22b', 'C',      (False, True,  '',    False, 1, 0)),
        (22, 'M', 'Sen23',  'r',      (False, True,  '',    False, 0, 0)),      # kleine r: geen voorkeur competitie
        (31, 'V', 'Sen31',  'R',      (False, True,  '',    True,  1, 0)),
        (32, 'M', 'Sen32',  'C',      (False, True,  '',    False, 0, 4)),      # SR4
        (32, 'M', 'Sen32b', 'BB',     (True,  True,  '',    False, 0, 0)),      # account
        (33, 'V', 'Sen33',  'R',      (False, True,  '',    False, 0, 0)),
        (33, 'V', 'Sen33b', 'BB',     (False, True,  '',    False, 0, 0)),
        (34, 'M', 'Sen34',  'LB',     (True,  True,  '',    False, 0, 0)),      # Sen34 = HWL
        (35, 'V', 'Sen35',  'R+C+BB', (False, True,  '',    False, 0, 0)),      # schiet 3 bogen
        (36, 'M', 'Sen36',  'C',      (False, True,  'W2',  True,  0, 0)),
        (36, 'M', 'Sen36b', 'BB',     (False, True,  '',    False, 0, 0)),
        (37, 'V', 'Sen37',  'R',      (False, True,  'VI1', True,  0, 5)),      # SR5
        (38, 'M', 'Sen38',  'LB',     (False, True,  '',    False, 0, 0)),
        (39, 'V', 'Sen39',  'R',      (True,  True,  '',    False, 0, 0)),      # Sen39 = BKO/RKO/RCL
        (40, 'M', 'Sen40',  'C+FSC',  (False, True,  '',    False, 0, 0)),
        (41, 'V', 'Sen41',  'R',      (False, False, '',    False, 0, 0)),      # geen voorkeur rk/bk
        (42, 'M', 'Sen42',  'R',      (False, True,  'DIS', True,  1, 0)),
        (42, 'M', 'Sen42b', 'C',      (False, True,  '',    False, 0, 0)),
        (49, 'V', 'Sen49',  'R',      (False, True,  '',    False, 0, 0)),
        (49, 'V', 'Sen49b', 'BB+BBR', (False, True,  '',    False, 0, 0)),
        (50, 'M', 'Mas50',  'R',      (True,  True,  '',    False, 0, 0)),      # Mas50 = SEC
        (51, 'V', 'Mas51',  'R',      (True,  True,  '',    False, 0, 4)),      # SR4 + account
        (51, 'V', 'Mas51b', 'C',      (False, True,  '',    False, 0, 0)),
        (51, 'V', 'Mas52',  'r',      (False, True,  '',    False, 0, 0)),      # kleine r: geen voorkeur competitie
        (59, 'M', 'Mas59',  'R',      (False, True,  '',    False, 0, 0)),
        (59, 'M', 'Mas59b', 'LB',     (False, True,  '',    False, 0, 0)),
        (60, 'V', 'Vet60',  'R',      (False, True,  '',    False, 0, 0)),
        (60, 'V', 'Vet60b', 'C',      (False, True,  '',    False, 0, 0)),
        (60, 'V', 'Vet60c', 'LB',     (True,  True,  '',    False, 0, 0)),      # account
        (61, 'M', 'Vet61',  'C',      (False, True,  '',    False, 0, 0)),
        (61, 'M', 'Vet61b', 'C',      (False, True,  '',    False, 0, 0)),
        (80, 'V', 'Vet80',  'R',      (False, True,  '',    False, 0, 0)),
    ]

    def __init__(self):
        self.account_admin = None
        self.account_bb = None

        # structuur
        self.regio = dict()                     # [regio_nr] = Regio
        self.rayon = dict()                     # [rayon_nr] = Rayon

        # verenigingen
        self.regio_ver_nrs = dict()             # [regio_nr] = list(ver_nrs)
        self.ver_nrs = list()                   # [ver_nr, ...]
        self.vereniging = dict()                # [ver_nr] = Vereniging()

        self.account_sec = dict()               # [ver_nr] = Account
        self.account_hwl = dict()               # [ver_nr] = Account

        self.functie_sec = dict()               # [ver_nr] = Functie
        self.functie_hwl = dict()               # [ver_nr] = Functie

        # leden
        self.ver_sporters = dict()              # [ver_nr] = list(Sporter)
        self.ver_sporters_met_account = dict()  # [ver_nr] = list(Sporter) met sporter.account != None

        # scheidsrechters
        self.sporters_scheids = {               # [scheids] = list(Sporter)
            SCHEIDS_INTERNATIONAAL: [],
            SCHEIDS_BOND: [],
            SCHEIDS_VERENIGING: [],
        }

        # competities
        self.comp18 = None                      # Competitie
        self.comp25 = None                      # Competitie

        self.deelkamp18_bk = None               # Kampioenschap
        self.deelkamp25_bk = None               # Kampioenschap

        self.deelkamp18_rk = dict()             # [rayon_nr] Kampioenschap
        self.deelkamp25_rk = dict()             # [rayon_nr] Kampioenschap

        self.deelcomp18_regio = dict()          # [regio_nr] DeelCompetitie
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

        self.comp18_klassen_teams = dict()      # [teamtype afkorting] = [klasse, ...]
        self.comp25_klassen_teams = dict()      # [teamtype afkorting] = [klasse, ...]

        self.comp18_klassen_rk_bk_teams = dict()    # [teamtype afkorting] = [klasse, ...]
        self.comp25_klassen_rk_bk_teams = dict()    # [teamtype afkorting] = [klasse, ...]

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

        # regiokampioenen
        self.comp18_regiokampioenen = list()    # [KampioenschapSporterBoog met kampioen_label != '', ...]
        self.comp25_regiokampioenen = list()    # [KampioenschapSporterBoog met kampioen_label != '', ...]

        # aangemaakte RK sporters
        self.comp18_rk_deelnemers = list()
        self.comp25_rk_deelnemers = list()

        # aangemaakte RK teams
        self.comp18_kampioenschapteams = list()
        self.comp25_kampioenschapteams = list()

        # aangemaakte BK sporters
        self.comp18_bk_deelnemers = list()
        self.comp25_bk_deelnemers = list()

        self._accounts_beheerders = list()      # 1 per vereniging, voor BKO, RKO, RCL

        self.afkorting2teamtype_khsn = dict()   # [team afkorting] = TeamType()

        self.afkorting2boogtype_khsn = dict()   # [boog afkorting] = BoogType()
        self.afkorting2boogtype_ifaa = dict()   # [boog afkorting] = BoogType()

        for teamtype in get_organisatie_teamtypen(ORGANISATIE_KHSN):
            self.afkorting2teamtype_khsn[teamtype.afkorting] = teamtype
        # for
        for boogtype in get_organisatie_boogtypen(ORGANISATIE_KHSN):
            self.afkorting2boogtype_khsn[boogtype.afkorting] = boogtype
        # for
        for boogtype in get_organisatie_boogtypen(ORGANISATIE_IFAA):
            self.afkorting2boogtype_ifaa[boogtype.afkorting] = boogtype
        # for
        for regio in Regio.objects.all():
            self.regio[regio.regio_nr] = regio
        # for
        for rayon in Rayon.objects.all():
            self.rayon[rayon.rayon_nr] = rayon
        # for

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
    def _verwerk_competitie_mutaties(show_warnings=True, show_all=False):
        # vraag de achtergrond taak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('competitie_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        err_msg = f1.getvalue()
        if '[ERROR]' in err_msg:                                                # pragma: no cover
            print('Onverwachte fout van competitie_mutaties:\n' + err_msg)

        if show_all:                                                            # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

        elif show_warnings:                                                     # pragma: no branch
            lines = f1.getvalue() + '\n' + f2.getvalue()
            for line in lines.split('\n'):
                if line.startswith('[WARNING] '):                               # pragma: no cover
                    print(line)
            # for

    def regio_teamcompetitie_ronde_doorzetten(self, deelcomp):
        """
            Trigger de site om de teamronde van een specifieke competitie door te zetten naar de volgende ronde
        """
        regio_nr = deelcomp.regio.regio_nr
        if deelcomp.competitie.afstand == 18:                                   # pragma: no cover
            account = self.comp18_account_rcl[regio_nr]
            functie = self.comp18_functie_rcl[regio_nr]
        else:
            account = self.comp25_account_rcl[regio_nr]
            functie = self.comp25_functie_rcl[regio_nr]

        # wordt RCL van de regiocompetitie
        client = Client()
        self._login(client, account)
        self._wissel_naar_functie(client, functie)

        url = self.url_volgende_ronde % deelcomp.pk
        client.post(url, {'snel': 1})

        self._verwerk_competitie_mutaties()

    def maak_accounts_admin_en_bb(self):
        """
            Maak de standaard accounts aan die voor de meeste testen nodig zijn:
                account_admin:  met IT beheer rechten
                account_bb:     met BB rechten

            vhpg is geaccepteerd, dus je kan meteen inloggen op deze accounts met:

                self.e2e_login_and_pass_otp(self.testdata.account_bb)
                self.e2e_wisselnaarrol_bb()
                self.e2e_check_rol('BB')
        """

        now = timezone.now()

        # alle accounts moeten en Sporter hebben en die hebben weer een vereniging nodig
        ver = Vereniging(
                    ver_nr=7000,
                    naam='Admin vereniging',
                    plaats='Stadium',
                    regio=self.regio[100],
                    geen_wedstrijden=True)
        ver.save()
        self.vereniging[ver.ver_nr] = ver

        # admin
        email = 'staff@test.com'
        self.account_admin = self._create_account('admin', email, 'Admin')
        self.account_admin.is_staff = True
        self.account_admin.save()

        Sporter(
            lid_nr=200001,
            voornaam='Super',
            achternaam='Admin',
            unaccented_naam='Super Admin',
            geboorte_datum='1900-01-01',
            geboorteplaats='Stadium',
            geslacht=GESLACHT_ANDERS,
            adres_code='8000ZZ',
            is_actief_lid=True,
            sinds_datum='2005-01-01',
            bij_vereniging=ver,
            lid_tot_einde_jaar=now.year,
            email=email,
            account=self.account_admin).save()

        # maak een BB aan, nodig voor de competitie
        email = 'bb@test.com'
        self.account_bb = self._create_account('bb', email, 'Bond')
        self.account_bb.is_BB = True
        self.account_bb.save()

        Sporter(
            lid_nr=200002,
            voornaam='Bond',
            achternaam='de Admin',
            unaccented_naam='BB de Admin',
            geboorte_datum='1900-01-01',
            geboorteplaats='Stadium',
            geslacht=GESLACHT_ANDERS,
            adres_code='8000ZZ',
            is_actief_lid=True,
            sinds_datum='2005-01-01',
            bij_vereniging=ver,
            lid_tot_einde_jaar=now.year,
            email=email,
            account=self.account_bb).save()

        self._accepteer_vhpg_voor_alle_accounts()

    def _create_account(self, username, email, voornaam):
        """
            Maak een Account aan in de database van de website
        """
        account = account_create(username, voornaam, '', self.WACHTWOORD, email, email_is_bevestigd=True)

        # zet OTP actief (een test kan deze altijd weer uit zetten)
        account.otp_code = "whatever"
        account.otp_is_actief = True
        account.save(update_fields=['otp_code', 'otp_is_actief'])

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

        if len(bulk) > 0:                                                           # pragma: no branch
            VerklaringHanterenPersoonsgegevens.objects.bulk_create(bulk)

    def _maak_verenigingen(self):
        """
            Maak in regios 101..107 elk vier verenigingen aan
            Maak in regios 108..116 elk twee verenigingen aan
            Maak in regio 100 twee verenigingen aan

            ver_nr = MIN_VER_NR + regio_nr * 10 + volgnummer + 1
                     3054 is dus 3e vereniging in regio 105

            de eerste 3 verenigingen in regio's 101 en 108 gaan in het eerste cluster van die regio
        """
        cluster_regios = list()

        bulk = list()
        for regio in Regio.objects.select_related('rayon').order_by('regio_nr'):
            if regio.regio_nr in (101, 107):
                cluster_regios.append(regio)

            aantal = 2
            if 101 <= regio.regio_nr <= 107:
                aantal = 4

            for nr in range(aantal):
                ver_nr = MIN_VER_NR + regio.regio_nr * 10 + nr + 1
                self.ver_nrs.append(ver_nr)

                ver = Vereniging(
                            ver_nr=ver_nr,
                            naam="Club %s" % ver_nr,
                            plaats="Regio %s dorp %s" % (regio.regio_nr, nr+1),
                            regio=regio,
                            # geen secretaris lid
                            geen_wedstrijden=regio.is_administratief)

                bulk.append(ver)
            # for
        # for

        Vereniging.objects.bulk_create(bulk)     # 48x
        # print('TestData: created %sx Vereniging' % len(bulk))

        for ver in bulk:
            self.vereniging[ver.ver_nr] = ver

            try:
                self.regio_ver_nrs[ver.regio.regio_nr].append(ver.ver_nr)
            except KeyError:
                self.regio_ver_nrs[ver.regio.regio_nr] = [ver.ver_nr]
        # for

        for regio in cluster_regios:
            cluster = Cluster.objects.filter(regio=regio).order_by('letter')[0]
            self.regio_cluster[regio.regio_nr] = cluster
            for ver in Vereniging.objects.filter(regio=regio).order_by('ver_nr')[:3]:
                ver.clusters.add(cluster)
            # for
        # for

    def _maak_leden(self, ook_ifaa_bogen):
        """
            Maak voor elke vereniging een aantal leden aan: een mix van alle wedstrijdklassen en boogtypen.

            Aspirant <13, Aspirant 13-14, Cadet 15-17, Junior 18-20, Senior 21-49, Master 50-59, Veteraan 60+
        """

        huidige_jaar = timezone.now().year
        lid_sinds_datum = datetime.date(year=huidige_jaar - 1, month=11, day=12)

        geslacht_voornaam2boogtypen = dict()        # [geslacht + voornaam] = [boogtype1, boogtype2, ...]
        for _, geslacht, voornaam, boogtype, flags in self.leden:
            try:
                _ = geslacht_voornaam2boogtypen[geslacht + voornaam]
            except KeyError:
                geslacht_voornaam2boogtypen[geslacht + voornaam] = boogtype.split('+')
            else:
                raise IndexError('TestData: combinatie geslacht %s + voornaam %s komt meerdere keren voor' % (geslacht, voornaam))      # pragma: no cover
        # for

        # maak voor elke vereniging een paar accounts aan
        lid_nr = MIN_LID_NR
        bulk = list()
        ver_unsorted = [(ver.ver_nr, ver) for ver in self.vereniging.values() if not ver.geen_wedstrijden]
        ver_unsorted.sort()     # sorteer op verenigingsnummer om de volgorde te garanderen
        for _, ver in ver_unsorted:
            for _, _, voornaam, _, flags in self.leden:
                maak_account, _, _, _, _, _ = flags
                lid_nr += 1

                if maak_account:
                    account = Account(
                                username=str(lid_nr),
                                otp_code=self.OTP_CODE,
                                otp_is_actief=True,
                                email_is_bevestigd=True,
                                bevestigde_email='lid%s@testdata.zz' % lid_nr)
                    account.set_password(self.WACHTWOORD)
                    bulk.append(account)

                    if len(bulk) > 100:                                        # pragma: no branch
                        Account.objects.bulk_create(bulk)
                        bulk = list()
            # for
        # for

        if len(bulk) > 0:                           # pragma: no branch
            Account.objects.bulk_create(bulk)
        del bulk

        # cache de aangemaakte accounts
        lid_nr2account = dict()
        for account in Account.objects.all():
            lid_nr2account[account.username] = account
        # for

        sr2scheids = {
            0: SCHEIDS_NIET,
            3: SCHEIDS_VERENIGING,
            4: SCHEIDS_BOND,
            5: SCHEIDS_INTERNATIONAAL,
        }

        lid_nr = MIN_LID_NR
        bulk = list()
        geslacht_voornaam2para = dict()  # [geslacht + voornaam] = (voorwerpen, opmerking)
        sr_credits = 25
        for _, ver in ver_unsorted:

            self.ver_sporters[ver.ver_nr] = list()
            self.ver_sporters_met_account[ver.ver_nr] = list()

            for wleeftijd, geslacht, voornaam, _, flags in self.leden:
                _, _, para_code, para_voorwerpen, para_opmerking, sr = flags
                geslacht_voornaam2para[geslacht + voornaam] = (para_voorwerpen, para_opmerking)

                if sr:
                    if sr_credits > 0:
                        sr_credits -= 1
                    else:
                        sr = 0

                lid_nr += 1
                achternaam = "Lid%s van Club%s" % (lid_nr, ver.ver_nr)
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
                        scheids=sr2scheids[sr],
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
        boogtypen = list(self.afkorting2boogtype_khsn.values())
        if ook_ifaa_bogen:
            boogtypen += list(self.afkorting2boogtype_ifaa.values())

        bulk_voorkeuren = list()
        bulk_sporter = list()
        for sporter in (Sporter
                        .objects
                        .exclude(bij_vereniging__geen_wedstrijden=True)
                        .select_related('account',
                                        'bij_vereniging')
                        .order_by('lid_nr')):

            ver_nr = sporter.bij_vereniging.ver_nr

            self.ver_sporters[ver_nr].append(sporter)
            if sporter.account:
                self.ver_sporters_met_account[ver_nr].append(sporter)
            if sporter.scheids != SCHEIDS_NIET:
                self.sporters_scheids[sporter.scheids].append(sporter)

            gewenste_boogtypen = geslacht_voornaam2boogtypen[sporter.geslacht + sporter.voornaam]
            para_voorwerpen, para_opmerking = geslacht_voornaam2para[sporter.geslacht + sporter.voornaam]

            # voorkeuren
            voorkeuren = SporterVoorkeuren(
                                sporter=sporter,
                                para_voorwerpen=para_voorwerpen)

            for gewenst_boogtype in gewenste_boogtypen:
                if para_opmerking > 0:
                    voorkeuren.opmerking_para_sporter = 'Para opmerking van redelijke lengte om mee te testen'

                if gewenst_boogtype.islower():
                    voorkeuren.voorkeur_meedoen_competitie = False
                    gewenst_boogtype = gewenst_boogtype.upper()

                # alle junioren willen een eigen blazoen
                if gewenst_boogtype == 'R' and sporter.voornaam.startswith('Jun'):
                    voorkeuren.voorkeur_eigen_blazoen = True
            # for

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

                for gewenst_boogtype in gewenste_boogtypen:
                    if boogtype.afkorting == gewenst_boogtype:
                        sporterboog.voor_wedstrijd = True
                # for

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
        for ver in (Vereniging
                    .objects
                    .filter(ver_nr__gte=MIN_VER_NR)
                    .exclude(geen_wedstrijden=True)):
            for rol, beschrijving in (('SEC', 'Secretaris vereniging %s'),
                                      ('HWL', 'Hoofdwedstrijdleider %s'),
                                      ('WL', 'Wedstrijdleider %s')):
                func = Functie(
                            # accounts
                            beschrijving=beschrijving % ver.ver_nr,
                            rol=rol,
                            # bevestigde_email=''
                            # nieuwe_email=''
                            vereniging=ver)

                if rol == 'SEC':
                    func.bevestigde_email = 'secretaris.club%s@testdata.zz' % ver.ver_nr

                bulk.append(func)

                if len(bulk) > 150:                           # pragma: no cover
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
                        .select_related('vereniging')
                        .filter(rol__in=('SEC', 'HWL'))):
            ver_nr = functie.vereniging.ver_nr
            if functie.rol == 'SEC':
                self.functie_sec[ver_nr] = functie
                try:
                    account = self.account_sec[ver_nr]
                except KeyError:
                    # typically ver_nr=8000
                    pass
                else:
                    functie.accounts.add(account)
            else:
                self.functie_hwl[ver_nr] = functie
                try:
                    account = self.account_hwl[ver_nr]
                except KeyError:
                    # typically ver_nr=8000
                    pass
                else:
                    functie.accounts.add(account)
        # for

    def maak_clubs_en_sporters(self, ook_ifaa_bogen=False):
        # print('TestData: maak_clubs_en_leden. Counters: Vereniging=%s, Sporter=%s' % (
        #                     Vereniging.objects.count(), Sporter.objects.count()))
        self._maak_verenigingen()
        self._maak_leden(ook_ifaa_bogen)
        self._maak_accounts_en_functies()
        self._accepteer_vhpg_voor_alle_accounts()

    @staticmethod
    def maak_sporterboog_aanvangsgemiddelden(afstand, ver_nr):
        """ Maak voor de helft van de SporterBoog een AG aan in voorgaand seizoen
            deze kunnen gebruikt worden voor de klassengrenzen en inschrijven.
        """
        volgende_ag = 6000       # 6.0
        volgende_ag += ver_nr

        bulk = list()
        for sporterboog in (SporterBoog
                            .objects
                            .filter(sporter__bij_vereniging__ver_nr=ver_nr,
                                    voor_wedstrijd=True)
                            .order_by('pk')):
            # even pk get an AG
            if sporterboog.pk % 1 == 0:                                             # pragma: no branch
                volgende_ag = 6000 if volgende_ag > 9800 else volgende_ag + 25
                ag = Aanvangsgemiddelde(
                            doel=AG_DOEL_INDIV,
                            sporterboog=sporterboog,
                            boogtype=sporterboog.boogtype,
                            waarde=Decimal(volgende_ag / 1000),
                            afstand_meter=afstand)
                bulk.append(ag)

                if len(bulk) > 500:                                                 # pragma: no cover
                    Aanvangsgemiddelde.objects.bulk_create(bulk)

                    bulk2 = list()
                    for ag in bulk:
                        hist = AanvangsgemiddeldeHist(
                                        ag=ag,
                                        oude_waarde=0,
                                        nieuwe_waarde=ag.waarde,
                                        # when = auto-set
                                        # door_account=None,
                                        notitie='Testdata')
                        bulk2.append(hist)
                    # for
                    AanvangsgemiddeldeHist.objects.bulk_create(bulk2)
                    del bulk2

                    bulk = list()
        # for

        if len(bulk):                                                               # pragma: no branch
            Aanvangsgemiddelde.objects.bulk_create(bulk)

            bulk2 = list()
            for ag in bulk:
                hist = AanvangsgemiddeldeHist(
                            ag=ag,
                            oude_waarde=0,
                            nieuwe_waarde=ag.waarde,
                            # when = auto-set
                            # door_account=None,
                            notitie='Testdata')
                bulk2.append(hist)
            # for
            AanvangsgemiddeldeHist.objects.bulk_create(bulk2)
            del bulk2

    def maak_bondscompetities(self, begin_jaar=None):

        competities_aanmaken(begin_jaar)

        for comp in Competitie.objects.all():
            if comp.is_indoor():
                self.comp18 = comp
            else:
                self.comp25 = comp
        # for

        for deelcomp in (Regiocompetitie
                         .objects
                         .select_related('competitie',
                                         'regio')
                         .all()):
            is_18 = deelcomp.competitie.is_indoor()
            regio_nr = deelcomp.regio.regio_nr
            if is_18:
                self.deelcomp18_regio[regio_nr] = deelcomp
            else:
                self.deelcomp25_regio[regio_nr] = deelcomp
        # for
        del deelcomp

        for deelkamp in (Kampioenschap
                         .objects
                         .select_related('competitie',
                                         'rayon')
                         .all()):
            is_18 = deelkamp.competitie.is_indoor()

            if deelkamp.deel == DEEL_BK:
                if is_18:
                    self.deelkamp18_bk = deelkamp
                else:
                    self.deelkamp25_bk = deelkamp

            else:  # if deelkamp.deel == DEEL_RK:
                rayon_nr = deelkamp.rayon.rayon_nr
                if is_18:
                    self.deelkamp18_rk[rayon_nr] = deelkamp
                else:
                    self.deelkamp25_rk[rayon_nr] = deelkamp
        # for
        del deelkamp

        # zorg dat er accounts gekoppeld zijn aan de functies BKO, RKO, RCL
        accounts = self._accounts_beheerders[:]

        if len(accounts) > 0:       # pragma: no branch
            for functie in (Functie
                            .objects
                            .select_related('regio', 'rayon')
                            .filter(rol__in=('RCL', 'RKO', 'BKO'))):

                is_18 = functie.comp_type == '18'

                account = accounts.pop(0)
                functie.accounts.add(account)

                if functie.rol == 'RCL':
                    regio_nr = functie.regio.regio_nr
                    if is_18:
                        self.comp18_functie_rcl[regio_nr] = functie
                        self.comp18_account_rcl[regio_nr] = account
                    else:
                        self.comp25_functie_rcl[regio_nr] = functie
                        self.comp25_account_rcl[regio_nr] = account

                elif functie.rol == 'RKO':
                    rayon_nr = functie.rayon.rayon_nr
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

        for klasse in (CompetitieIndivKlasse
                       .objects
                       .select_related('competitie',
                                       'boogtype')
                       .all()):

            afkorting = klasse.boogtype.afkorting
            if klasse.competitie.is_indoor():
                klassen = self.comp18_klassen_indiv
            else:
                klassen = self.comp25_klassen_indiv

            try:
                klassen[afkorting].append(klasse)
            except KeyError:
                klassen[afkorting] = [klasse]
        # for

        for klasse in (CompetitieTeamKlasse
                       .objects
                       .select_related('competitie',
                                       'team_type')
                       .all()):

            afkorting = klasse.team_type.afkorting

            if klasse.competitie.is_indoor():
                klassen = self.comp18_klassen_teams
                klassen_rk_bk = self.comp18_klassen_rk_bk_teams
            else:
                klassen = self.comp25_klassen_teams
                klassen_rk_bk = self.comp25_klassen_rk_bk_teams

            try:
                klassen[afkorting].append(klasse)
            except KeyError:
                klassen[afkorting] = [klasse]

            if klasse.is_voor_teams_rk_bk:
                try:
                    klassen_rk_bk[afkorting].append(klasse)
                except KeyError:
                    klassen_rk_bk[afkorting] = [klasse]

        # for

    def maak_inschrijvingen_regiocompetitie(self, afstand=18, ver_nr=None):
        """ Schrijf alle leden van de vereniging in voor de competitie, voor een specifieke vereniging

            afstand = 18 / 25
            ver_nr = MIN_VER_NR + regio_nr * 10 + volgnummer + 1
        """

        if afstand == 18:
            comp = self.comp18
            deelnemers = self.comp18_deelnemers
        else:
            comp = self.comp25
            deelnemers = self.comp25_deelnemers

        url = self.url_inschrijven % comp.pk

        # zet competitie fase C zodat we in mogen schrijven
        zet_competitie_fase_regio_inschrijven(comp)

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
                                    voor_wedstrijd=True,
                                    boogtype__organisatie=ORGANISATIE_WA)):

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

        new_deelnemers = (RegiocompetitieSporterBoog
                          .objects
                          .select_related('sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'bij_vereniging',
                                          'indiv_klasse')
                          .filter(regiocompetitie__competitie=comp,
                                  sporterboog__pk__in=pks)
                          .order_by('sporterboog__sporter__lid_nr'))        # consistente volgorde

        deelnemers.extend(new_deelnemers)

        # zet voor een paar deelnemers de inschrijfvoorkeur voor RK/BK uit
        voornamen = list()
        for _, _, voornaam, boogtype, flags in self.leden:
            _, inschrijf_voorkeur_rk_bk, _, _, _, _ = flags
            if not inschrijf_voorkeur_rk_bk:
                voornamen.append(voornaam)
        # for

        # zoek de deelnemers op en pas de vlag aan
        for deelnemer in deelnemers:
            if deelnemer.sporterboog.sporter.voornaam in voornamen:
                deelnemer.inschrijf_voorkeur_rk_bk = False
                deelnemer.save(update_fields=['inschrijf_voorkeur_rk_bk'])
        # for

    def maak_inschrijvingen_regio_teamcompetitie(self, afstand, ver_nr):
        """ Schrijf teams in voor de teamcompetitie, voor een specifieke vereniging

            afstand = 18 / 25
            ver_nr = regio_nr * 10 + volgnummer
        """

        ver = Vereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        regio_nr = ver.regio.regio_nr

        if afstand == 18:
            deelcomp = self.deelcomp18_regio[regio_nr]
            deelnemers = self.comp18_deelnemers
            deelnemers_team = self.comp18_deelnemers_team
            deelnemers_geen_team = self.comp18_deelnemers_geen_team
            klassen = self.comp18_klassen_teams
            regioteams = self.comp18_regioteams
        else:
            deelcomp = self.deelcomp25_regio[regio_nr]
            deelnemers = self.comp25_deelnemers
            deelnemers_team = self.comp25_deelnemers_team
            deelnemers_geen_team = self.comp25_deelnemers_geen_team
            klassen = self.comp25_klassen_teams
            regioteams = self.comp25_regioteams

        # verdeel de deelnemers per boogtype
        deelnemers_per_boog = dict()   # [boogtype.afkorting] = list(deelnemer)

        for deelnemer in deelnemers:
            if deelnemer.inschrijf_voorkeur_team:
                # print('deelnemer: %s (indiv ag: %s, team ag: %s)' % (
                #           deelnemer, deelnemer.ag_voor_indiv, deelnemer.ag_voor_team))
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
                            regiocompetitie=deelcomp,
                            vereniging=ver,
                            volg_nr=next_nr,
                            team_type=self.afkorting2teamtype_khsn[afkorting],
                            team_naam='%s-%s-%s' % (ver_nr, next_nr, afkorting),
                            team_klasse=klasse)
                bulk.append(team)
            # while
        # for

        RegiocompetitieTeam.objects.bulk_create(bulk)

        # koppel de sporters aan het team
        for team in (RegiocompetitieTeam
                     .objects
                     .select_related('team_type')
                     .filter(regiocompetitie=deelcomp,
                             vereniging=ver)):

            afkorting = team.team_type.afkorting

            # vertaal team type naar boog type
            if afkorting in ('R2', 'BB2'):
                afkorting = afkorting[:-1]      # R2/BB2 -> R/BB

            # selecteer de volgende 4 sporters voor dit team
            deelnemers = deelnemers_per_boog[afkorting][:4]
            deelnemers_per_boog[afkorting] = deelnemers_per_boog[afkorting][len(deelnemers):]

            # bereken de teamsterkte (som van top 3)
            ags = [deelnemer.ag_voor_team for deelnemer in deelnemers]
            ags.sort(reverse=True)
            team.aanvangsgemiddelde = sum(ags[:3])
            team.save(update_fields=['aanvangsgemiddelde'])

            team.leden.set(deelnemers)

            regioteams.append(team)
        # for

    def maak_poules(self, deelcomp):
        """ Maak poules en vul deze met teams """

        if deelcomp.competitie.is_indoor():
            regioteams = self.comp18_regioteams
            poules = self.comp18_poules
        else:
            regioteams = self.comp25_regioteams
            poules = self.comp25_poules

        # maak per boogtype 1 poule aan
        done = list()
        bulk = list()
        for team in regioteams:
            if team.regiocompetitie == deelcomp:                                     # pragma: no branch
                afkorting = team.team_type.afkorting
                if afkorting not in done:
                    poule = RegiocompetitieTeamPoule(
                                    regiocompetitie=deelcomp,
                                    # teams,
                                    beschrijving="Poule %s team type %s" % (deelcomp, team.team_type.beschrijving))

                    bulk.append(poule)
                    done.append(afkorting)
        # for

        RegiocompetitieTeamPoule.objects.bulk_create(bulk)

        for poule in (RegiocompetitieTeamPoule
                      .objects
                      .select_related('regiocompetitie__competitie')
                      .filter(regiocompetitie=deelcomp)):

            pks = list()
            for team in regioteams:
                if team.regiocompetitie == deelcomp:                                 # pragma: no branch
                    if poule.beschrijving.endswith(team.team_type.beschrijving):
                        pks.append(team.pk)
            # for

            pks = pks[:8]       # maximaal 8 teams in een poule
            poule.teams.set(pks)

            poules.append(poule)
        # for

    def maak_rk_deelnemers(self, afstand, ver_nr, regio_nr, limit_boogtypen=('R', 'C', 'BB', 'LB', 'TR')):
        """ Maak de RK deelnemers aan, alsof ze doorgestroomd zijn vanuit de regiocompetitie
            rank en volgorde wordt ingevuld door maak_label_regiokampioenen

            afstand = 18 / 25
            ver_nr = regio_nr * 10 + volgnummer
        """

        ver = self.vereniging[ver_nr]

        if afstand == 18:
            deelkamp = self.deelkamp18_rk[ver.regio.rayon_nr]
            klassen = self.comp18_klassen_indiv
            rk_deelnemers = self.comp18_rk_deelnemers
        else:
            deelkamp = self.deelkamp25_rk[ver.regio.rayon_nr]
            klassen = self.comp25_klassen_indiv
            rk_deelnemers = self.comp25_rk_deelnemers

        ag = 7000       # 7.0
        ag += (ver_nr - MIN_VER_NR)

        max_ag = 9000
        if (regio_nr % 4) == 0:
            max_ag = 9500           # zorg dat de regiokampioenen niet allemaal bovenaan staan

        wedstrijd_jaar = deelkamp.competitie.begin_jaar      # niet +1 doen, want dan komen er aspiranten doorheen!

        pks = list()
        bulk = list()
        for sporterboog in (SporterBoog
                            .objects
                            .filter(sporter__bij_vereniging__ver_nr=ver_nr,
                                    voor_wedstrijd=True)
                            .select_related('boogtype')
                            .order_by('sporter__lid_nr')):          # ensure consistent results

            ag = 7000 if ag > max_ag else ag + 25

            leeftijd = sporterboog.sporter.bereken_wedstrijdleeftijd_wa(wedstrijd_jaar)
            if leeftijd > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT:
                afk = sporterboog.boogtype.afkorting
                if afk in limit_boogtypen:
                    deelnemer_klasse = None
                    for klasse in reversed(klassen[afk]):                           # pragma: no branch
                        if klasse.is_ook_voor_rk_bk:
                            for lkl in klasse.leeftijdsklassen.all():
                                if lkl.leeftijd_is_compatible(leeftijd):
                                    deelnemer_klasse = klasse
                                    break
                                # for
                        if deelnemer_klasse:
                            break
                    # for

                    # print(sporterboog.sporter.bij_vereniging.ver_nr,
                    #       sporterboog.sporter.lid_nr,
                    #       sporterboog.boogtype.afkorting,
                    #       "%.3f" % (ag/1000), deelnemer_klasse)
                    if deelnemer_klasse:                                            # pragma: no branch
                        deelnemer = KampioenschapSporterBoog(
                                            kampioenschap=deelkamp,
                                            sporterboog=sporterboog,
                                            indiv_klasse=deelnemer_klasse,
                                            bij_vereniging=sporterboog.sporter.bij_vereniging,
                                            kampioen_label='',
                                            volgorde=0,
                                            rank=0,
                                            # bevestiging_gevraagd_op (date/time) = None
                                            # deelname=DEELNAME_ONBEKEND
                                            gemiddelde=Decimal(ag) / 1000)
                        bulk.append(deelnemer)
                        pks.append(sporterboog.pk)
                        # print(deelnemer, ' --> ', deelnemer.indiv_klasse)
        # for

        KampioenschapSporterBoog.objects.bulk_create(bulk)
        del bulk

        nieuwe_deelnemers = (KampioenschapSporterBoog
                             .objects
                             .select_related('indiv_klasse',
                                             'bij_vereniging',
                                             'kampioenschap',
                                             'kampioenschap__competitie',
                                             'sporterboog',
                                             'sporterboog__sporter',
                                             'sporterboog__boogtype')
                             .filter(kampioenschap=deelkamp,
                                     sporterboog__pk__in=pks)
                             .order_by('sporterboog__sporter__lid_nr',
                                       'sporterboog__boogtype__afkorting'))
        rk_deelnemers.extend(nieuwe_deelnemers)

    def maak_label_regiokampioenen(self, afstand, regio_nr_begin, regio_nr_einde):
        """ label de regiokampioen van elke wedstrijdklasse voor de gevraagde regios en competitie """
        if afstand == 18:
            regiokampioenen = self.comp18_regiokampioenen
        else:
            regiokampioenen = self.comp25_regiokampioenen

        regio_nrs = [regio_nr for regio_nr in range(regio_nr_begin, regio_nr_einde + 1)]

        volgorde_per_klasse = dict()    # [klasse.pk] = teller
        klasse_regio_done = list()      # [(klasse.pk, regio_nr), ...]

        for kampioen in (KampioenschapSporterBoog
                         .objects
                         .filter(kampioenschap__competitie__afstand=afstand,
                                 bij_vereniging__regio__regio_nr__in=regio_nrs)
                         .select_related('indiv_klasse',
                                         'bij_vereniging__regio')
                         .order_by('-gemiddelde',            # hoogste eerst
                                   'indiv_klasse__volgorde')):

            klasse_pk = kampioen.indiv_klasse.pk
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

    def maak_voorinschrijvingen_rk_teamcompetitie(self, afstand, ver_nr, ook_incomplete_teams=True):
        """ maak voor deze vereniging een paar teams aan voor de open RK teams inschrijving """

        ver = Vereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        rayon_nr = ver.regio.rayon_nr

        if afstand == 18:                                                           # pragma: no cover
            deelkamp = self.deelkamp18_rk[rayon_nr]
            deelnemers = self.comp18_deelnemers
            rk_teams = self.comp18_kampioenschapteams
        else:
            deelkamp = self.deelkamp25_rk[rayon_nr]
            deelnemers = self.comp25_deelnemers
            rk_teams = self.comp25_kampioenschapteams

        # verdeel de deelnemers per boogtype
        deelnemers_per_boog = dict()   # [boogtype.afkorting] = list(deelnemer)

        for deelnemer in deelnemers:
            # print('deelnemer: %s (indiv ag: %s, team ag: %s)' % (deelnemer,
            #                                                      deelnemer.ag_voor_indiv,
            #                                                      deelnemer.ag_voor_team))
            if deelnemer.inschrijf_voorkeur_team and deelnemer.bij_vereniging.ver_nr == ver_nr:
                # print('deelnemer: %s (indiv ag: %s, team ag: %s)' % (deelnemer,
                #                                                      deelnemer.ag_voor_indiv,
                #                                                      deelnemer.ag_voor_team))
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
                                kampioenschap=deelkamp,
                                vereniging=ver,
                                volg_nr=next_nr,
                                team_type=self.afkorting2teamtype_khsn[afkorting],
                                team_naam='rk-%s-%s-%s' % (ver_nr, next_nr, afkorting),
                                # team_klasse wordt later bepaald door de BKO
                                aanvangsgemiddelde=ag)

                    bulk.append(team)

                    tup = (team, koppel)
                    nieuwe_teams.append(tup)
            # while
        # for

        KampioenschapTeam.objects.bulk_create(bulk)

        for team, koppel in nieuwe_teams:
            team.tijdelijke_leden.set(koppel)
            rk_teams.append(team)
        # for

    def geef_rk_team_tijdelijke_sporters_genoeg_scores(self, afstand, ver_nr):
        if afstand == 18:                                                           # pragma: no cover
            rk_teams = self.comp18_kampioenschapteams       # list of KampioenschapTeam
        else:
            rk_teams = self.comp25_kampioenschapteams

        gem = 7.0
        step = 0.12

        for team in rk_teams:
            if team.vereniging.ver_nr == ver_nr:            # pragma: no branch
                for deelnemer in team.tijdelijke_leden.all():
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

    def geef_regio_deelnemers_genoeg_scores_voor_rk(self, afstand):         # pragma: no cover
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

            gem += step
            if gem > 9.7:
                step = -0.34
            elif gem < 5.0:
                step = 0.23

            # afronden op 3 decimalen (anders gebeurt dat tijdens opslaan in database)
            gem = round(gem, 3)
        # for

    def maak_rk_teams(self, afstand, ver_nr, per_team=4, limit_teamtypen=('R2', 'C'), zet_klasse=False):
        """ maak voor deze vereniging een paar teams aan voor de RK teams inschrijving
            en koppel er meteen een aantal RK deelnemers van de vereniging aan.
        """

        ver = Vereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        rayon_nr = ver.regio.rayon_nr

        if afstand == 18:
            deelkamp = self.deelkamp18_rk[rayon_nr]
            rk_teams = self.comp18_kampioenschapteams
            team_klassen = self.comp18_klassen_rk_bk_teams
            rk_deelnemers = self.comp18_rk_deelnemers
        else:
            deelkamp = self.deelkamp25_rk[rayon_nr]
            rk_teams = self.comp25_kampioenschapteams
            team_klassen = self.comp25_klassen_rk_bk_teams
            rk_deelnemers = self.comp25_rk_deelnemers

        # verdeel de deelnemers per boogtype
        deelnemers_per_boog = dict()   # [boogtype.afkorting] = list(deelnemer)

        for deelnemer in rk_deelnemers:
            if deelnemer.bij_vereniging.ver_nr == ver_nr:
                # print('deelnemer: %s (indiv ag: %s, team ag: %s)' % (deelnemer,
                #                                                      deelnemer.ag_voor_indiv,
                #                                                      deelnemer.ag_voor_team))
                boogtype_afkorting = deelnemer.sporterboog.boogtype.afkorting

                # vertaal boogtype naar teamtype
                teamtype_afkorting = boogtype_afkorting
                if teamtype_afkorting in ('R', 'BB'):                               # pragma: no branch
                    teamtype_afkorting += '2'  # R2, BB2

                if teamtype_afkorting in limit_teamtypen:
                    try:
                        deelnemers_per_boog[boogtype_afkorting].append(deelnemer)
                    except KeyError:
                        deelnemers_per_boog[boogtype_afkorting] = [deelnemer]
        # for

        # zet 1x BB en 1x LB in een recurve team
        if 'BB' in deelnemers_per_boog and len(deelnemers_per_boog['BB']) > 0:      # pragma: no cover
            deelnemers_per_boog['R'].append(deelnemers_per_boog['BB'].pop(0))

        if 'LB' in deelnemers_per_boog and len(deelnemers_per_boog['LB']) > 0:      # pragma: no cover
            deelnemers_per_boog['R'].append(deelnemers_per_boog['LB'].pop(0))

        bulk = list()
        nieuwe_teams = list()
        for afkorting, deelnemers in deelnemers_per_boog.items():

            # vertaal boogtype naar teamtype
            if afkorting in ('R', 'BB'):                                            # pragma: no branch
                afkorting += '2'            # R2, BB2
            teamtype = self.afkorting2teamtype_khsn[afkorting]

            aantal = len(deelnemers)
            while aantal > 0:
                next_nr = len(bulk) + 1

                koppel = deelnemers[:per_team]

                deelnemers = deelnemers[len(koppel):]
                aantal = len(deelnemers)

                if len(koppel) >= 3:
                    gemiddelden = [deelnemer.gemiddelde for deelnemer in koppel]
                    gemiddelden.sort(reverse=True)      # hoogste eerst
                    team_ag = sum(gemiddelden[:3])

                    team = KampioenschapTeam(
                                kampioenschap=deelkamp,
                                vereniging=ver,
                                volg_nr=next_nr,
                                team_type=teamtype,
                                team_naam='team-%s-%s-%s' % (ver_nr, next_nr, afkorting),
                                # team_klasse wordt later bepaald door de BKO
                                aanvangsgemiddelde=team_ag)
                    if zet_klasse:
                        team.team_klasse = team_klassen[afkorting][0]

                    bulk.append(team)

                    tup = (team, koppel)
                    nieuwe_teams.append(tup)
            # while
        # for

        KampioenschapTeam.objects.bulk_create(bulk)

        for team, koppel in nieuwe_teams:
            team.gekoppelde_leden.set(koppel)
            rk_teams.append(team)
        # for

    def maak_wedstrijd_locatie(self, ver_nr):
        locatie = WedstrijdLocatie(
                        naam='locatie %s' % ver_nr,
                        discipline_25m1pijl=True,
                        discipline_outdoor=True,
                        discipline_indoor=True,
                        discipline_3d=True,
                        banen_18m=12,
                        banen_25m=12,
                        max_sporters_18m=12*4,
                        max_sporters_25m=12*3,
                        buiten_banen=10,
                        buiten_max_afstand=75,
                        adres='Ons doel 1, 9999ZZ Doelstad',
                        plaats='Doelstad')
        locatie.save()
        locatie.verenigingen.add(self.vereniging[ver_nr])

        return locatie

    @staticmethod
    def maak_uitslag_rk_indiv(afstand: int):
        nr = 1
        score1 = 200
        score2 = 150
        klasse_pk2rank = dict()     # [indiv_klasse.pk] = rank

        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap__competitie__afstand=afstand)):

            # print(deelnemer.pk, deelnemer, deelnemer.indiv_klasse)

            if nr % 10 == 0:
                # iedere 10e deelnemer deed niet mee
                deelnemer.deelname = DEELNAME_NEE
                deelnemer.result_rank = 0

                deelnemer.save(update_fields=['deelname', 'result_rank'])

            elif nr % 15 == 0:
                # elke 15 deelnemer was een reserve die niet meegedaan heeft
                deelnemer.result_rank = KAMP_RANK_RESERVE
                deelnemer.save(update_fields=['deelname', 'result_rank'])

            else:
                try:
                    rank = klasse_pk2rank[deelnemer.indiv_klasse.pk]
                except KeyError:
                    rank = 0

                rank += 1
                klasse_pk2rank[deelnemer.indiv_klasse.pk] = rank

                deelnemer.result_rank = rank
                deelnemer.result_score_1 = score1
                deelnemer.result_score_2 = score2

                deelnemer.save(update_fields=['deelname', 'result_rank', 'result_score_1', 'result_score_2'])

            nr += 1
            score1 -= 2
            score2 -= 1
        # for

    def maak_bk_deelnemers(self, afstand):
        """ Laat RK deelnemers doorstromen naar de BK
            afstand = 18 / 25
        """

        if afstand == 18:
            deelkamp_bk = self.deelkamp18_bk
            rk_pks = [deelkamp_rk.pk for deelkamp_rk in self.deelkamp18_rk.values()]
            pijlen = 2.0 * 30
            bk_deelnemers = self.comp18_bk_deelnemers
        else:
            deelkamp_bk = self.deelkamp25_bk
            rk_pks = [deelkamp_rk.pk for deelkamp_rk in self.deelkamp25_rk.values()]
            pijlen = 2.0 * 25
            bk_deelnemers = self.comp25_bk_deelnemers

        bulk = list()
        prev_klasse = None
        volgorde = 0
        for rk_deelnemer in (KampioenschapSporterBoog
                             .objects
                             .filter(kampioenschap__pk__in=rk_pks)
                             .prefetch_related('sporterboog',
                                               'indiv_klasse',
                                               'bij_vereniging')
                             .order_by('indiv_klasse',
                                       'result_rank')):

            if rk_deelnemer.indiv_klasse != prev_klasse:
                prev_klasse = rk_deelnemer.indiv_klasse
                volgorde = 0

            volgorde += 1
            deelname = DEELNAME_JA if volgorde <= 24 else DEELNAME_NEE
            if volgorde == 5:
                deelname = DEELNAME_ONBEKEND
            ag = rk_deelnemer.result_score_1 + rk_deelnemer.result_score_2
            ag /= pijlen
            scores_str = '%03d%03d' % (max(rk_deelnemer.result_score_1, rk_deelnemer.result_score_2),
                                       min(rk_deelnemer.result_score_1, rk_deelnemer.result_score_2))
            label = 'RK Kampioen' if volgorde in (6, 9) else ''     # 9 heeft ook para opmerking in voorkeuren

            bk_deelnemer = KampioenschapSporterBoog(
                                kampioenschap=deelkamp_bk,
                                sporterboog=rk_deelnemer.sporterboog,
                                indiv_klasse=rk_deelnemer.indiv_klasse,
                                bij_vereniging=rk_deelnemer.bij_vereniging,
                                volgorde=volgorde,
                                rank=volgorde,
                                deelname=deelname,
                                kampioen_label=label,
                                gemiddelde=ag,
                                gemiddelde_scores=scores_str)
            bulk.append(bk_deelnemer)
        # for

        if len(bulk):           # pragma: no branch
            KampioenschapSporterBoog.objects.bulk_create(bulk)

        nieuwe_deelnemers = (KampioenschapSporterBoog
                             .objects
                             .select_related('indiv_klasse',
                                             'bij_vereniging',
                                             'kampioenschap',
                                             'kampioenschap__competitie',
                                             'sporterboog',
                                             'sporterboog__sporter',
                                             'sporterboog__boogtype')
                             .filter(kampioenschap=deelkamp_bk)
                             .order_by('sporterboog__sporter__lid_nr',
                                       'sporterboog__boogtype__afkorting'))
        bk_deelnemers.extend(nieuwe_deelnemers)

    def maak_bk_teams(self, afstand):
        """ Laat RK teams doorstromen naar de BK """

        if afstand == 18:
            deelkamp_bk = self.deelkamp18_bk
            rk_pks = [deelkamp_rk.pk for deelkamp_rk in self.deelkamp18_rk.values()]
            pijlen = 30.0
        else:
            deelkamp_bk = self.deelkamp25_bk
            rk_pks = [deelkamp_rk.pk for deelkamp_rk in self.deelkamp25_rk.values()]
            pijlen = 25.0

        rk_team_leden = dict()   # [(ver_nr, volg_nr, team_type_afkorting)] = rk_team gekoppelde_leden

        bulk = list()
        prev_klasse = None
        volgorde = 0
        for rk_team in (KampioenschapTeam
                        .objects
                        .filter(kampioenschap__pk__in=rk_pks)
                        .prefetch_related('team_klasse',
                                          'team_type',
                                          'vereniging')
                        .prefetch_related('gekoppelde_leden')
                        .order_by('team_klasse',
                                  'result_rank')):

            tup = (rk_team.vereniging.ver_nr, rk_team.volg_nr, rk_team.team_type.afkorting)
            rk_team_leden[tup] = list(rk_team.gekoppelde_leden.all())

            if rk_team.team_klasse != prev_klasse:
                prev_klasse = rk_team.team_klasse
                volgorde = 0

            volgorde += 1

            ag = rk_team.result_teamscore / pijlen

            # print('[%s] bk_team: %s, klasse=%s' % (afstand, rk_team.team_naam, rk_team.team_klasse))
            # print('     team_leden: %s' % repr(rk_team_leden[tup]))

            bk_team = KampioenschapTeam(
                            kampioenschap=deelkamp_bk,
                            vereniging=rk_team.vereniging,
                            volg_nr=rk_team.volg_nr,
                            team_type=rk_team.team_type,
                            team_naam=rk_team.team_naam,
                            volgorde=volgorde,
                            team_klasse=rk_team.team_klasse,
                            aanvangsgemiddelde=ag)

            bulk.append(bk_team)
        # for

        if len(bulk):       # pragma: no branch
            KampioenschapTeam.objects.bulk_create(bulk)

        for bk_team in KampioenschapTeam.objects.filter(kampioenschap=deelkamp_bk):
            tup = (bk_team.vereniging.ver_nr, bk_team.volg_nr, bk_team.team_type.afkorting)
            leden = rk_team_leden[tup]
            bk_team.gekoppelde_leden.set(leden)
        # for


# end of file
