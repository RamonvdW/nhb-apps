# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Routines om de database te vullen met een test set die gebruikt wordt in vele van de test cases """

from django.utils import timezone
from Account.models import Account, account_create
from BasisTypen.models import BoogType
from Competitie.models import Competitie, DeelCompetitie, LAAG_BK, LAAG_RK, LAAG_REGIO
from Competitie.operations import competities_aanmaken
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from NhbStructuur.models import NhbRegio, NhbCluster, NhbVereniging
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
import datetime

# fixtures zijn overwogen, maar zijn lastig te onderhouden en geven geen recente datums (zoals voor VHPG)


class TestData(object):
    """
        Maak een standaard set data aan die in veel tests gebruikt kan worden

        gebruik:
            from django.test import TestCase
            from TestHelpers import testdata

            class MyTests(TestCase):

                @classmethod
                def setUpClass(cls):
                    super().setUpClass()
                    cls.testdata = testdata.TestData()
    """

    OTP_CODE = "test"
    WACHTWOORD = "qewretrytuyi"  # sterk genoeg default wachtwoord

    def __init__(self):
        self.account_admin = None
        self.account_bb = None

        # verenigingen
        self.account_sec = dict()               # [ver_nr] = Account
        self.account_hwl = dict()               # [ver_nr] = Account

        self.functie_sec = dict()               # [ver_nr] = Functie
        self.functie_hwl = dict()               # [ver_nr] = Functie

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

        self._accounts_beheerders = list()      # 1 per vereniging, voor BKO, RKO, RCL


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
        now = timezone.now()
        bulk = list()
        for account in Account.objects.all():
            vhpg = VerklaringHanterenPersoonsgegevens(
                        account=account,
                        acceptatie_datum=now)
            bulk.append(vhpg)
        # for
        VerklaringHanterenPersoonsgegevens.objects.bulk_create(bulk)

    @staticmethod
    def _maak_verenigingen():
        """
            Maak in elk van de 16 regio's vier verenigingen aan

            ver_nr = regio_nr * 10 + volgnummer
                     1053 is dus 3e vereniging in regio 105

            de eerste 3 verenigingen in regio's 101 en 108 gaan in het eerste cluster van die regio
        """
        cluster_regios = list()
        curr_rayon = 0

        bulk = list()
        for regio in NhbRegio.objects.select_related('rayon').all():

            if regio.regio_nr in (101, 108):
                cluster_regios.append(regio)

            if regio.rayon.rayon_nr != curr_rayon:
                curr_rayon = regio.rayon.rayon_nr
                if curr_rayon in (3, 4):
                    aantal = 1
                else:
                    aantal = 4

            for nr in range(aantal):
                ver_nr = regio.regio_nr * 10 + 1 + nr

                # vereniging 0, 1, 2 gaan in een cluster, 3 niet
                if nr >= 3:
                    cluster = None

                ver = NhbVereniging(
                            ver_nr=ver_nr,
                            naam="Club %s" % ver_nr,
                            plaats="Regio %s dorp %s" % (regio.regio_nr, nr+1),
                            contact_email='club%s@testdata.zz' % ver_nr,
                            regio=regio,
                            # geen secretaris lid
                            geen_wedstrijden=regio.is_administratief)

                bulk.append(ver)
            # for
        # for

        NhbVereniging.objects.bulk_create(bulk)     # 16 x 4 = 64 verenigingen
        # print('TestData: created %sx NhbVereniging' % len(bulk))

        for regio in cluster_regios:
            cluster = NhbCluster.objects.filter(regio=regio).order_by('letter')[0]
            for ver in NhbVereniging.objects.filter(regio=regio).order_by('ver_nr')[:3]:
                ver.clusters.add(cluster)
            # for
        # for

    @staticmethod
    def _maak_leden():
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
            (17, 'V', 'Cad17', 'R'),
            (17, 'V', 'Cad17b', 'C'),
            (17, 'V', 'Cad17c', 'BB'),
            (18, 'M', 'Jun18', 'R'),
            (18, 'M', 'Jun18b', 'C'),
            (18, 'M', 'Jun18c', 'BB'),
            (18, 'V', 'Jun18', 'BB'),
            (19, 'V', 'Jun19', 'R'),
            (19, 'V', 'Jun19b', 'C'),
            (20, 'M', 'Jun20', 'R'),
            (20, 'M', 'Jun20b', 'C'),
            (21, 'V', 'Sen21', 'R'),
            (21, 'V', 'Sen21b', 'C'),
            (22, 'M', 'Sen22', 'R'),
            (22, 'M', 'Sen22b', 'C'),
            (22, 'M', 'Sen23', 'r'),            # klein letter: geen voorkeur voor de competitie
            (31, 'V', 'Sen31', 'R'),
            (32, 'M', 'Sen32', 'C'),
            (32, 'M', 'Sen32b', 'BB'),
            (33, 'V', 'Sen33', 'R'),
            (33, 'V', 'Sen33b', 'BB'),
            (34, 'M', 'Sen34', 'C'),            # Sen34 = HWL
            (35, 'V', 'Sen35', 'R'),
            (36, 'M', 'Sen36', 'C'),
            (36, 'M', 'Sen36b', 'BB'),
            (37, 'V', 'Sen37', 'R'),
            (38, 'M', 'Sen38', 'C'),
            (39, 'V', 'Sen39', 'R'),            # Sen39 = BKO/RKO/RCL
            (40, 'M', 'Sen40', 'C'),
            (41, 'V', 'Sen41', 'R'),
            (42, 'M', 'Sen42', 'R'),
            (42, 'M', 'Sen42b', 'C'),
            (49, 'V', 'Sen49', 'R'),
            (49, 'V', 'Sen49b', 'BB'),
            (50, 'M', 'Mas50', 'R'),            # Mas50 = SEC
            (51, 'V', 'Mas51', 'R'),
            (51, 'V', 'Mas51b', 'C'),
            (51, 'V', 'Mas52', 'r'),            # kleine letter: geen voorkeur voor de competitie
            (59, 'M', 'Mas59', 'R'),
            (59, 'M', 'Mas59b', 'LB'),
            (60, 'V', 'Vet60', 'R'),
            (60, 'V', 'Vet60b', 'C'),
            (60, 'V', 'Vet60c', 'LB'),
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
                raise IndexError('TestData: combinatie geslacht %s + voornaam %s komt meerdere keren voor' % (geslacht, voornaam))
        # for

        lid_nr = 300000
        bulk = list()
        for ver in NhbVereniging.objects.all():
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
        for sporter in Sporter.objects.all():
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
            # for
        # for

        SporterVoorkeuren.objects.bulk_create(bulk_voorkeuren)
        # print('TestData: Created %sx SporterVoorkeuren' % len(bulk_voorkeuren))
        del bulk_voorkeuren

        SporterBoog.objects.bulk_create(bulk_sporter)
        # print('TestData: Created %sx SporterBoog' % len(bulk_sporter))
        del bulk_sporter

    def _maak_accounts_en_functies(self):
        """
            Maak voor elke verenigingen drie functies aan: SEC, HWL, WL

            Maak voor bepaalde leden van de vereniging een account aan
            Koppel deze accounts aan de rollen SEC en HWL
        """

        # maak voor elke vereniging een paar accounts aan
        bulk = list()
        for sporter in Sporter.objects.filter(voornaam__in=('Sen34', 'Sen39', 'Mas50')):
            account = Account(
                            username=str(sporter.lid_nr),
                            otp_code=self.OTP_CODE,
                            password=self.WACHTWOORD)
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
                        .filter(voornaam__in=('Sen34', 'Sen39', 'Mas50'))):

            account = username2account[str(sporter.lid_nr)]
            sporter.account = account
            sporter.save(update_fields=['account'])

            ver_nr = sporter.bij_vereniging.ver_nr
            if sporter.voornaam == 'Sen34':
                self.account_hwl[ver_nr] = account
            elif sporter.voornaam == 'Mas50':
                self.account_sec[ver_nr] = account
            else:
                self._accounts_beheerders.append(account)

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
