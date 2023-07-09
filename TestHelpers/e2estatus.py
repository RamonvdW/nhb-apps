# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


# template names checked out by assert_html_ok
validated_templates = list()

# template names checked out by assert_consistent_email_html_text
consistent_email_templates = list()

# these templates are included by other templates
included_templates = (
    'plein/site_layout.dtl',
    'plein/site_layout_fonts.dtl',
    'plein/site_layout_favicons.dtl',
    'plein/site_layout_minimaal.dtl',
    'plein/card_icon.dtl',
    'plein/card_logo.dtl',
    'plein/card_icon_beschikbaar-vanaf.dtl',
    'plein/card_logo_beschikbaar-vanaf.dtl',
    'plein/card_niet-beschikbaar.dtl',
    'plein/andere-sites.dtl',
    'plein/ga-naar-live-server.dtl',
    'feedback/sidebar.dtl',
    'functie/vhpg-tekst.dtl',
    'logboek/common.dtl',
    'snippets.dtl',
    'email_mailer/email_basis.dtl',
)

# end of file
