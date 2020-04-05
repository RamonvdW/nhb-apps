# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class AccountConfig(AppConfig):
    name = 'Account'

    def ready(self):
        # geef de otp code een kans de plugins te registreren
        import Account.rechten


# end of file
