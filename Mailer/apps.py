# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig


class MailerConfig(AppConfig):
    name = 'Mailer'

    def ready(self):
        # registreer de error handler
        # dit voorkomt circular dependencies tijdens opstarten
        from Mailer.operations import set_bad_email_handler
        from Mailer.report import emailadres_is_geblokkeerd
        set_bad_email_handler(emailadres_is_geblokkeerd)


# end of file
