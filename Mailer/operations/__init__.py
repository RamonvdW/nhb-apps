# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from .send import send_mail, set_bad_email_handler
from .queue import mailer_queue_email
from .internal_error import mailer_notify_internal_error
from .render import render_email_template
from .email_address import mailer_obfuscate_email, mailer_email_is_valide

__all__ = ['send_mail', 'set_bad_email_handler',
           'mailer_queue_email',
           'mailer_notify_internal_error',
           'render_email_template',
           'mailer_obfuscate_email', 'mailer_email_is_valide']

# end of file
