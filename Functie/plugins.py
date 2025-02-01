# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Account.plugin_manager import account_add_plugin_post_login
from Functie.definities import Rol
from Functie.rol.bepaal import rol_eval_rechten_simpel
from Functie.rol.huidige import rol_zet_huidige_rol, rol_zet_huidige_functie_pk


def functie_post_login_plugin(request, account):
    """ Deze plugin functie wordt aangeroepen vanuit de Account login view
        (de koppeling wordt gelegd in Functie.apps.ready)

        We initialiseren het de sessie voor huidige rol/sessie.
        We sturen de gebruiker naar de 2FA pagina, indien van toepassing

        Return: "url" of None = geen redirect
    """

    rol_zet_huidige_rol(request, Rol.ROL_SPORTER)
    rol_zet_huidige_functie_pk(request, None)

    # controleer of deze gebruiker rollen heeft en dus van rol mag wisselen
    rol_eval_rechten_simpel(request, account)

    if account.otp_is_actief:
        # 2FA check altijd aanbieden aan account met BB rol of admin access
        if account.is_staff or account.is_BB:
            return reverse('Account:otp-controle')

        # alleen 2FA check aanbieden als er ook functies aan gekoppeld zijn
        # dit voorkomt 2FA check voor ex-managers

        # uitgezet --> gebruikersvriendelijker om uit te stellen totdat wissel van rol gekozen wordt
        # if account.functie_set.count() > 0:
        #     return reverse('Account:otp-controle')

    return None


# registreer de plugin
account_add_plugin_post_login(20, functie_post_login_plugin)


# end of file
