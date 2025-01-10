# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Ondersteuning voor de rollen binnen de applicatie """

from Account.models import Account
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import Kampioenschap
from Functie.definities import Rol, functie_rol_str2rol
from Functie.models import Functie
from Functie.rol.beschrijving import rol_get_beschrijving, rol_zet_beschrijving
from Functie.rol.mag_wisselen import rol_zet_mag_wisselen
from Functie.rol.scheids import rol_zet_is_scheids
from Functie.rol.huidige import rol_get_huidige_functie, rol_zet_huidige_rol, rol_zet_huidige_functie_pk
from typing import Generator, Tuple
import typing


def rol_eval_rechten_simpel(request, account: Account):
    """ Deze functie wordt gebruikt om te bepalen of een gebruiker extra rechten heeft,
        zoals beheerder (via Account of Functie) en scheidsrechter.

        Wordt aangeroepen na diverse punten in de applicatie waar een POST ontvangen wordt.
        Voorbeeld: inlog, login-as, login-wachtwoord-vergeten
                   en ping-back van het plein

        Te verversen:
            - mag wisselen: afhankelijk van gekoppelde rollen (niet van VHPG of OTP status)

        Niet verversen:
            - huidige rol en functie
    """

    mag_wisselen = account.is_staff or account.is_BB

    if not mag_wisselen:
        if account.functie_set.count() > 0:
            mag_wisselen = True

    rol_zet_mag_wisselen(request, mag_wisselen)

    rol_zet_is_scheids(request, account)

    # zorg dat de beschrijving gezet is
    msg = rol_get_beschrijving(request)
    if not msg or len(msg) < 3:
        rol, functie_pk = rol_get_huidige_functie(request)
        rol_zet_beschrijving(request, rol, functie_pk)


class ShortFunc:

    def __init__(self):
        self.functie_pk = 0
        self.functie = Functie()
        self.rol_str = ""
        self.rol = Rol.ROL_NONE
        self.comp_type = 0
        self.rcl_regio_nr = 0
        self.rcl_rayon_nr = 0
        self.rko_rayon_nr = 0
        self.ver_nr = 0          # alleen voor SEC, HWL en WL


class RolBepaler:

    """ Verzameling van alle logica voor toegestane rollen

        Wordt gebruikt voor het wissel-van-rol scherm
        En voor activeer_rol/functie
    """

    def __init__(self, account):
        self._alle: typing.Dict[int, ShortFunc] = dict()                    # [functie.pk] = func
        self._rayon2rcl: typing.Dict[int, typing.List[ShortFunc]] = dict()  # [rayon_nr] = [func, ...]
        self._regio2hwl: typing.Dict[int, typing.List[ShortFunc]] = dict()  # [regio_nr] = [func, ...]

        self._eigen: typing.List[ShortFunc] = list()                        # [func, ...]
        self._management: typing.List[ShortFunc] = list()                   # [func, ...]

        self._has_bb: bool = account.is_staff or account.is_BB

        self._vul_cache()
        self._directe_rollen_van_account_toevoegen(account)

    @staticmethod
    def _make_func(obj: Functie) -> ShortFunc:
        func = ShortFunc()
        func.functie_pk = obj.pk
        func.functie = obj
        func.rol_str = obj.rol
        try:
            func.rol = functie_rol_str2rol[obj.rol]
        except KeyError:
            func.rol = Rol.ROL_SPORTER
        func.comp_type = obj.comp_type

        if obj.rayon_id:
            func.rko_rayon_nr = obj.rayon.rayon_nr

        if obj.regio_id:
            func.rcl_regio_nr = obj.regio.regio_nr
            func.rcl_regio_rayon_nr = obj.regio.rayon_nr

        if obj.vereniging_id:
            func.ver_nr = obj.vereniging.ver_nr

        return func

    def _vul_cache(self):
        """ haal alle Functie records binnen """

        # TODO: met values() kan deze query minder zwaar gemaakt worden
        for obj in (Functie
                    .objects
                    .select_related('rayon',
                                    'regio',
                                    'regio__rayon',
                                    'vereniging',
                                    'vereniging__regio')
                    .all()):

            func = self._make_func(obj)

            self._alle[obj.pk] = func

            # regio 100 zijn speciale verenigingen die door rol BB gebruikt mogen worden
            if obj.rol == 'HWL' and obj.vereniging:
                regio_nr = obj.vereniging.regio.regio_nr
                try:
                    self._regio2hwl[regio_nr].append(func)
                except KeyError:
                    self._regio2hwl[regio_nr] = [func]

            # alle management rollen
            if self._has_bb:
                if func.rol in (Rol.ROL_MO, Rol.ROL_MWZ, Rol.ROL_MWW,
                                Rol.ROL_SUP, Rol.ROL_CS, Rol.ROL_BKO):
                    self._management.append(func)
            # for

            if obj.rol == 'RCL' and obj.regio:
                rayon_nr = obj.regio.rayon_nr
                try:
                    self._rayon2rcl[rayon_nr].append(func)
                except KeyError:
                    self._rayon2rcl[rayon_nr] = [func]
        # for

    def _directe_rollen_van_account_toevoegen(self, account):
        self._eigen = list()

        for obj in (account
                    .functie_set
                    .select_related('rayon',
                                    'regio',
                                    'regio__rayon',
                                    'vereniging',
                                    'vereniging__regio')
                    .all()):

            func = self._make_func(obj)
            self._eigen.append(func)
        # for

    def iter_directe_rollen(self) -> Generator[Tuple[Rol, Functie | None], None, None]:
        """                                    yields,                        send, returns
            yields (Rollen, Functie) voor elke vaste rol
        """
        if self._has_bb:
            yield Rol.ROL_BB, None

        for func in self._eigen:
            yield func.rol, func.functie
        # for

        yield Rol.ROL_SPORTER, None

    def iter_indirecte_rollen(self, rol: Rol, huidige_functie_pk: int) -> \
            Generator[Tuple[Rol, Functie | None], None, None]:
        #             yields,                     send, returns
        """
            yields (Rollen, Functie) voor elke indirecte rol

            Welke rollen beschikbaar zijn is afhankelijk van de huidige functie
        """

        # BB mag wisselen naar alle management rollen
        if rol == Rol.ROL_BB:
            for func in self._management:
                yield func.rol, func.functie
            # for

            # bondsbureau beheert de speciale vereniging in regio 100
            for func in self._regio2hwl.get(100, []):
                yield func.rol, func.functie
            # for

        func_nu = self._alle.get(huidige_functie_pk, None)
        if not func_nu:
            return

        if func_nu.rol == Rol.ROL_BKO:
            # expandeer naar de RKO rollen van dezelfde competitie
            for func in self._alle.values():
                if func.rol == Rol.ROL_RKO and func.comp_type == func.comp_type:
                    yield Rol.ROL_RKO, func.functie      # sorteren (op rayon_nr) is niet nodig
            # for

            # expandeer naar de HWL van verenigingen gekozen voor de BK's
            qset = (Kampioenschap
                    .objects
                    .filter(competitie__afstand=func_nu.comp_type,
                            deel=DEEL_BK)
                    .prefetch_related('rk_bk_matches'))

            ver_nrs = list()
            for deelkamp in qset:
                ver_nrs.extend(list(deelkamp
                                    .rk_bk_matches
                                    .select_related('vereniging')
                                    .values_list('vereniging__ver_nr', flat=True)))
            # for

            # zoek de HWL functies op
            for func in self._alle.values():
                if func.rol == Rol.ROL_HWL and func.ver_nr in ver_nrs:
                    yield Rol.ROL_HWL, func.functie
            # for

            return

        if func_nu.rol == Rol.ROL_RKO:
            # expandeer naar de RCL rollen binnen het rayon
            for func in self._rayon2rcl[func_nu.rko_rayon_nr]:
                if func.comp_type == func.comp_type:
                    yield Rol.ROL_RCL, func.functie        # sorteren (op regio_nr) is niet nodig
            # for

            # expandeer naar de HWL van verenigingen gekozen voor de RK's
            qset = (Kampioenschap
                    .objects
                    .filter(competitie__afstand=func_nu.comp_type,
                            deel=DEEL_RK,
                            rayon__rayon_nr=func.rko_rayon_nr)
                    .prefetch_related('rk_bk_matches'))

            ver_nrs = list()
            for deelkamp in qset:
                ver_nrs.extend(list(deelkamp
                                    .rk_bk_matches
                                    .select_related('vereniging')
                                    .values_list('vereniging__ver_nr', flat=True)))
            # for

            # zoek de HWL functies op
            for func in self._alle.values():
                if func.rol == Rol.ROL_HWL and func.ver_nr in ver_nrs:
                    yield Rol.ROL_HWL, func.functie
            # for

            return

        if func_nu.rol == Rol.ROL_RCL:
            # RCL mag wisselen naar de HWL van alle verenigingen in zijn regio
            for func in self._regio2hwl.get(func_nu.rcl_regio_nr, []):
                yield Rol.ROL_HWL, func.functie
            # for
            return

        if func_nu.rol == Rol.ROL_SEC:
            # SEC mag HWL worden, binnen de vereniging
            for func in self._alle.values():
                if func.rol == Rol.ROL_HWL and func.ver_nr == func_nu.ver_nr:
                    yield Rol.ROL_HWL, func.functie
            # for
            return

        if func_nu.rol == Rol.ROL_HWL:
            # expandeer naar de WL rollen binnen dezelfde vereniging
            for func in self._alle.values():
                if func.rol == Rol.ROL_WL and func.ver_nr == func_nu.ver_nr:
                    yield Rol.ROL_WL, func.functie
            # for
            return

    def mag_rol(self, rol: Rol) -> bool:
        """ Controleer of de gebruiker de gevraagde rol aan mag nemen
        """
        for mag_rol, _ in self.iter_directe_rollen():
            if mag_rol == rol:
                return True
        # for
        return False

    def mag_functie(self, request, functie_pk: int) -> (bool, Rol):
        """ Controleer of de gebruiker de gevraagde functie aan mag nemen
        """

        # IT en BB mogen direct wisselen naar elke andere rol
        if self._has_bb:
            for func in self._alle.values():
                if func.functie_pk == functie_pk:
                    return True, func.rol
            # for

        # is dit een van de eigen rollen?
        for mag_rol, mag_functie in self.iter_directe_rollen():
            if mag_functie and mag_functie.pk == functie_pk:
                func = self._alle[functie_pk]
                return True, func.rol
        # for

        rol_nu, functie_nu = rol_get_huidige_functie(request)
        if functie_nu:
            # is de gevraagde functie een afgeleide rol van de huidige rol?
            for mag_rol, mag_functie in self.iter_indirecte_rollen(functie_nu.pk):
                if mag_functie.pk == functie_pk:
                    func = self._alle[functie_pk]
                    return True, func.rol
            # for

        return False, Rol.ROL_NONE


# end of file
