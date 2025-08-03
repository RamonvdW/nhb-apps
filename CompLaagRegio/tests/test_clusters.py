# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.tests.helpers import maak_functie
from Geo.models import Regio, Cluster
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestCompLaagRegioClusters(E2EHelpers, TestCase):

    """ Tests voor de CompLaagRegio applicatie, Wijzig Clusters functies """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_clusters = '/bondscompetities/regio/clusters/'

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        regio_111 = Regio.objects.get(regio_nr=111)

        # maak een RCL aan
        rcl = self.e2e_create_account('rcl111', 'rcl111@test.com', 'RCL', accepteer_vhpg=True)
        rcl.regio = regio_111
        rcl.save()
        self.account_rcl111 = rcl

        # maak de HWL functie
        self.functie_rcl111 = maak_functie("RCL Regio 111 test", "RCL")
        self.functie_rcl111.regio = regio_111
        self.functie_rcl111.comp_type = '18'
        self.functie_rcl111.save()
        self.functie_rcl111.accounts.add(self.account_rcl111)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Eerste Club",
                    ver_nr=1001,
                    regio=regio_111)
        ver.save()
        self.ver1 = ver

        ver = Vereniging(
                    naam="Tweede Club",
                    ver_nr=1002,
                    regio=regio_111)
        ver.save()
        self.ver2 = ver

        ver = Vereniging(
                    naam="Derde Club",
                    ver_nr=1003,
                    regio=regio_111)
        ver.save()
        self.ver3 = ver

        # stop de verenigingen in een cluster
        self.cluster1 = Cluster.objects.get(gebruik='18', regio=regio_111, letter='a')     # standaard cluster
        self.ver1.clusters.add(self.cluster1)

        self.cluster2 = Cluster.objects.get(gebruik='18', regio=regio_111, letter='b')     # standaard cluster
        self.ver2.clusters.add(self.cluster2)

    def test_anon(self):
        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_clusters)
        self.assert403(resp)

    def test_rcl(self):
        # log in als RCL
        self.e2e_login_and_pass_otp(self.account_rcl111)
        self.e2e_wissel_naar_functie(self.functie_rcl111)
        self.e2e_check_rol('RCL')

        # haal het overzicht op
        with self.assert_max_queries(8):
            resp = self.client.get(self.url_clusters)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # pas de naam van een cluster aan
        # plaats ver1 in een ander cluster
        # haal ver2 uit zijn cluster
        # stop ver3 in een cluster
        with self.assert_max_queries(24):
            resp = self.client.post(self.url_clusters, {'naam_%s' % self.cluster1.pk: 'Hallo!',
                                                        'ver_1001': self.cluster2.pk,
                                                        'ver_1002': '0',
                                                        'ver_1003': self.cluster1.pk})
        self.assert_is_redirect_not_plein(resp)    # redirect = success

        cluster = Cluster.objects.get(pk=self.cluster1.pk)
        self.assertEqual(cluster.naam, 'Hallo!')

        # tweede set transacties, identiek aan de eerste
        # dit resulteert in alle "geen wijzigingen"
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_clusters, {'naam_%s' % self.cluster1.pk: 'Hallo!',
                                                        'ver_1001': self.cluster2.pk,
                                                        'ver_1002': '0',
                                                        'ver_1003': self.cluster1.pk})
        self.assert_is_redirect_not_plein(resp)    # redirect = success

        # stuur nog wat illegale parameters
        lange_tekst = 'Dit is een veel te lange tekst die ergens afgekapt gaat worden maar wel opgeslagen wordt.'
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_clusters, {'ver_1001': 'x',
                                                        'naam_%s' % self.cluster1.pk: lange_tekst})
        # foute parameters are silently ignored
        self.assert_is_redirect_not_plein(resp)    # redirect = success

        cluster = Cluster.objects.get(pk=self.cluster1.pk)
        self.assertEqual(cluster.naam, lange_tekst[:50])

        self.e2e_assert_other_http_commands_not_supported(self.url_clusters, post=False)

# end of file
