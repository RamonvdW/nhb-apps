# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Account.plugin_manager import account_add_plugin_post_login_redirect


def functie_post_login_redirect_plugin(request, account):
    """ Deze plugin functie wordt aangeroepen vanuit de Account login view
        (de koppeling wordt gelegd in Functie.apps.ready)

        We sturende gebruiker naar de 2FA pagina, indien van toepassing

        Return: "url" of None = geen redirect
    """

    # gebruikersvriendelijker om uit te stellen totdat wissel van rol gekozen wordt
    # if account.otp_is_actief:
    #     # 2FA check altijd aanbieden aan account met BB rol of admin access
    #     if account.is_staff or account.is_BB:
    #         return reverse('Account:otp-controle')
    #
    #     # alleen 2FA check aanbieden als er ook functies aan gekoppeld zijn
    #     # dit voorkomt 2FA check voor ex-managers
    #     if account.functie_set.count() > 0:
    #         return reverse('Account:otp-controle')

    return None


# registreer de plugin
account_add_plugin_post_login_redirect(20, functie_post_login_redirect_plugin)


# end of file
