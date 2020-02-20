# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from BasisTypen.models import WedstrijdKlasse
from NhbStructuur.models import NhbRegio, NhbRayon, NhbVereniging, NhbLid, ADMINISTRATIEVE_REGIO
from Logboek.models import schrijf_in_logboek
from Account.models import Account
from Account.rol import rol_zet_plugins, Rollen
from datetime import date
from decimal import Decimal


ZERO = Decimal('0.000')


class FavorieteBestuurders(models.Model):
    """ Deze klasse verbindt accounts met favoriete bestuurders
        De favorieten kunnen gekozen worden bij het koppelen van bestuurders
    """
    zelf = models.ForeignKey(Account, on_delete=models.CASCADE)
    favoriet = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='favorietebestuurder', blank=True, null=True)

    def __str__(self):
        return "%s --> %s" % (self.zelf.volledige_naam(), self.favoriet.volledige_naam())

    class Meta:
        verbose_name = verbose_name_plural = 'Favoriete bestuurders'


def add_favoriete_bestuurder(zelf_account, fav_account_pk):
    # alleen toevoegen als nog niet in de lijst
    if len(FavorieteBestuurders.objects.filter(zelf=zelf_account, favoriet__pk=fav_account_pk)) == 0:
        try:
            account = Account.objects.get(pk=fav_account_pk)
        except Account.DoesNotExist:
            # ignore illegal request
            pass
        else:
            FavorieteBestuurders(zelf=zelf_account, favoriet=account).save()


def drop_favoriete_bestuurder(zelf_account, fav_account_pk):
    # TODO: exception to handle?
    FavorieteBestuurders.objects.filter(zelf=zelf_account, favoriet__pk=fav_account_pk).delete()


class CompetitieWedstrijdKlasse(models.Model):
    """ Deze database tabel bevat een de klassen voor een competitie,
        met de vastgestelde aanvangsgemiddelden
    """
    wedstrijdklasse = models.ForeignKey(WedstrijdKlasse, on_delete=models.PROTECT)
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000
    is_afgesloten = models.BooleanField(default=False)

    def __str__(self):
        return "%s (%s)" % (self.wedstrijdklasse, self.min_ag)


class Competitie(models.Model):
    """ Deze database tabel bevat een van de jaarlijkste competities voor 18m of 25m
        Elke competitie heeft een beschrijving, een aantal belangrijke datums
        en een lijst van wedstrijdklassen met aanvangsgemiddelden
    """
    AFSTAND = [('18', 'Indoor'),
               ('25', '25m 1pijl')]

    beschrijving = models.CharField(max_length=40)
    afstand = models.CharField(max_length=2, choices=AFSTAND)
    begin_jaar = models.PositiveSmallIntegerField()     # 2019
    uiterste_datum_lid = models.DateField()
    begin_aanmeldingen = models.DateField()
    einde_aanmeldingen = models.DateField()
    einde_teamvorming = models.DateField()
    eerste_wedstrijd = models.DateField()
    klassen_indiv = models.ManyToManyField(CompetitieWedstrijdKlasse, related_name='indiv')
    klassen_team = models.ManyToManyField(CompetitieWedstrijdKlasse, related_name='team')
    is_afgesloten = models.BooleanField(default=False)

    def zet_fase(self):
        # fase A was totdat dit object gemaakt werd

        now = timezone.now()
        now = date(year=now.year, month=now.month, day=now.day)

        # A1 = competitie is aangemaakt en mag nog getuned worden
        if now < self.begin_aanmeldingen:
            # zijn de aanvangsgemiddelden bepaald?
            if len(self.klassen_indiv.all()) == 0:
                self.fase = 'A1'
                return

            # A2 = klassengrenzen zijn bepaald
            self.fase ='A2'
            return

        # B = open voor inschrijvingen
        if now < self.einde_aanmeldingen:
            self.fase ='B'
            return

        # C = aanmaken teams; gesloten voor individuele inschrijvingen
        if now < self.einde_teamvorming:
            self.fase = 'C'
            return

        # D = aanmaken poules en afronden wedstrijdschema's
        if now < self.eerste_wedstrijd:
            self.fase ='D'
            return

        # E = Begin wedstrijden
        self.fase ='E'

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.beschrijving


class DeelCompetitie(models.Model):
    """ Deze database tabel bevat informatie over een deel van een competitie:
        regiocompetitie (16x), rayoncompetitie (4x) of bondscompetitie (1x)
    """
    LAAG = [('Regio', 'Regiocompetitie'),
            ('RK', 'Rayoncompetitie'),
            ('BK', 'Bondscompetitie')]
    laag = models.CharField(max_length=5, choices=LAAG)
    competitie = models.ForeignKey(Competitie, on_delete=models.PROTECT)
    nhb_regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT,
                                  null=True, blank=True)    # optioneel want alleen voor laag Regio
    nhb_rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT,
                                  null=True, blank=True)    # optioneel want alleen voor laag Rayon
    is_afgesloten = models.BooleanField(default=False)

    functies = models.ManyToManyField(Group)    # Group representeert een Functie
    # Note: er is maar 1 functie per deelcompetitie
    #       ManyToMany maakt het mogelijk om via group.deelcompetities_set weer hier te komen

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        if self.nhb_regio:
            substr = str(self.nhb_regio)
        elif self.nhb_rayon:
            substr = str(self.nhb_rayon)
        else:
            substr = "BK"
        return "%s - %s"  % (self.competitie, substr)

    def get_rol_str(self):
        if self.laag == 'Regio':
            rol = 'RCL regio %s' % self.nhb_regio.regio_nr
        elif self.laag == 'RK':
            rol = 'RKO rayon %s' % self.nhb_rayon.rayon_nr
        else:
            rol = "BKO"
        return rol

    def bepaal_rol(self, Rollen):
        if self.laag == 'Regio':
            rol = Rollen.ROL_RCL
        elif self.laag == 'RK':
            rol = Rollen.ROL_RKO
        else:
            rol = "BKO"
        return rol


def deelcompetitie_met_functie(group):
    deelcomps = group.deelcompetitie_set.all()
    if len(deelcomps):
        return deelcomps[0]     # normaal is het er maar 1

    return None

def models_bepaal_startjaar_nieuwe_competitie():
    """ bepaal het start jaar van de nieuwe competitie """
    return timezone.now().year


def get_competitie_fase(afstand):
    # volgens tabel in hoofdstuk 1.3.1

    # TODO: er kunnen twee competities actief zijn. Geef de status van de oudste competitie.

    # A = initieel
    objs = Competitie.objects.filter(is_afgesloten=False, afstand=afstand)
    if len(objs) == 0:
        return 'A', Competitie()

    comp = objs[0]
    comp.zet_fase()
    return comp.fase, comp


def maak_deelcompetitie_functie(deel):
    """ Maak een nieuwe functie aan voor dit deel van de competitie
        Hieraan kunnen bestuurders gekoppeld worden.
    """
    if deel.nhb_regio:
        func_naam = "RCL regio %s" % deel.nhb_regio.regio_nr
    elif deel.nhb_rayon:
        func_naam = "RKO rayon %s" % deel.nhb_rayon.rayon_nr
    else:
        func_naam = "BKO"

    func_naam += " voor de " + deel.competitie.beschrijving

    # een Functie is gewoon een auth.Group
    func, created = Group.objects.get_or_create(name=func_naam)
    deel.functies.add(func)


def competitie_aanmaken():
    """ Deze functie wordt aangeroepen als de BKO de nieuwe competitie op wil starten
        We maken de 18m en 25m competitie aan en daaronder de deelcompetities voor regio, rayon en bond

        Wedstrijdklassen volgen later, tijdens het bepalen van de klassengrenzen
    """
    jaar = models_bepaal_startjaar_nieuwe_competitie()
    yearend = date(year=jaar, month=12, day=31)     # 31 december
    udvl = date(year=jaar, month=8, day=1)          # 1 augustus = uiterste datum van lidmaatschap voor deelname teamcompetitie

    # maak de Competitie aan voor 18m en 25m
    for afstand, beschrijving in Competitie.AFSTAND:
        fase, _ = get_competitie_fase(afstand)
        if fase == 'A':
            comp = Competitie()
            comp.beschrijving = '%s competitie %s/%s' % (beschrijving, jaar, jaar+1)
            comp.afstand = afstand      # 18/25
            comp.begin_jaar = jaar
            comp.uiterste_datum_lid = udvl
            comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = comp.eerste_wedstrijd = yearend
            comp.save()

            # maak de Deelcompetities aan voor Regio, RK, BK
            for laag, _ in DeelCompetitie.LAAG:
                deel = DeelCompetitie()
                deel.laag = laag
                deel.competitie = comp
                if laag == DeelCompetitie.LAAG[0][0]:
                    # Regio
                    for obj in NhbRegio.objects.all():
                        if obj.regio_nr != ADMINISTRATIEVE_REGIO:
                            deel.nhb_regio = obj
                            deel.pk = None
                            deel.save()
                            maak_deelcompetitie_functie(deel)
                    # for
                elif laag == DeelCompetitie.LAAG[1][0]:
                    # RK
                    for obj in NhbRayon.objects.all():
                        deel.nhb_rayon = obj
                        deel.pk = None
                        deel.save()
                        maak_deelcompetitie_functie(deel)
                else:
                    # BK
                    deel.save()
                    maak_deelcompetitie_functie(deel)
            # for
        # if
    # for


def maak_competitieklasse_indiv(comp, wedstrijdklasse, min_ag):
    """ Deze functie maakt een nieuwe CompetitieWedstrijdKlasse aan met het gevraagde min_ag
        en koppelt deze aan de gevraagde Competitie
    """
    compkl = CompetitieWedstrijdKlasse()
    compkl.wedstrijdklasse = wedstrijdklasse
    compkl.min_ag = min_ag
    compkl.save()
    comp.klassen_indiv.add(compkl)


def competitie_expandeer_rol(rol_in, group_in):
    """ Plug-in van de Account.rol module om een groep/functie te expanderen naar onderliggende functies
        Voorbeeld: RKO rayon 3 --> RCL regios 109, 110, 111, 112
        Deze functie yield (rol, group_pk)
    """
    #print("competitie_expandeer_rol: rol=%s, group=%s" % (repr(rol_in), repr(group_in)))

    if rol_in == Rollen.ROL_BB:
        # deze rol mag voor alle competities BKO zijn
        for competitie in Competitie.objects.filter(is_afgesloten=False):
            for deelcomp in DeelCompetitie.objects.filter(competitie=competitie, laag="BK"):
                for group in deelcomp.functies.all():
                    yield (Rollen.ROL_BKO, group.pk)
            # for
        # for

    if group_in:
        if group_in.name[:4] == "BKO ":
            # expandeer naar de RKO rollen
            # group --> deelcompetitie laag=BK --> competitie --> deelcompetities laag=RK
            for deelcomp_top in group_in.deelcompetitie_set.all():     # TODO: kan compacter met values_list
                competitie = deelcomp_top.competitie
                # zoek andere deelcompetitie die hier bij horen
                for deelcomp in DeelCompetitie.objects.filter(competitie=competitie, laag="RK"):
                    for group in deelcomp.functies.all():
                        yield (Rollen.ROL_RKO, group.pk)
                    # for
                # for
            # for

        if group_in.name[:4] == "RKO ":
            # expandeer naar de RCL rollen binnen het rayon
            # group --> deelcompetitie laag=RK --> competitie --> deelcompetities laag=Regio
            for deelcomp_top in group_in.deelcompetitie_set.all():     # TODO: kan compacter met values_list
                competitie = deelcomp_top.competitie
                rayon_nr = deelcomp_top.nhb_rayon.rayon_nr      # rayon nummer van de RKO
                # zoek andere deelcompetitie die hier bij horen
                for deelcomp in DeelCompetitie.objects.filter(competitie=competitie, laag="Regio"):
                    # alleen de regio's die in het rayon van de RKO zitten
                    if deelcomp.nhb_regio.rayon.rayon_nr == rayon_nr:
                        for group in deelcomp.functies.all():
                            yield (Rollen.ROL_RCL, group.pk)
                    # for
                # for
            # for

        if group_in.name[:4] == "RCL ":
            # expandeer naar de CWZ rollen binnen de regio
            # deelcompetitie.laag=Regio; deelcompetitie.nhb_regio == NhbVereniging.regio
            for deelcomp in group_in.deelcompetitie_set.all():      # normaal maar een
                if deelcomp.laag == "Regio":
                    # vind alle verenigingen in deze regio
                    for ver in NhbVereniging.objects.filter(regio=deelcomp.nhb_regio):
                        if ver.cwz_group:
                            yield (Rollen.ROL_CWZ, ver.cwz_group.pk)
                    # for
            # for

rol_zet_plugins(competitie_expandeer_rol)

# end of file
