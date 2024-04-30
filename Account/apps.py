# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class AccountConfig(AppConfig):
    name = 'Account'

    def ready(self):
        # laat de plugin zich registeren
        import Account.plugins              # noqa


# end of file
