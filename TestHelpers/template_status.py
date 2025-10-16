# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from pathlib import Path


# template names checked out by assert_html_ok
validated_templates = list()

# template names checked out by assert_consistent_email_html_text
consistent_email_templates = list()

# these templates are included by other templates
included_templates = (
    'design/site_layout.dtl',
    'design/site_layout_fonts.dtl',
    'design/site_layout_favicons.dtl',
    'design/site_layout_minimaal.dtl',
    'design/card_icon.dtl',
    'design/card_logo.dtl',
    'design/card_icon_beschikbaar-vanaf.dtl',
    'design/card_logo_beschikbaar-vanaf.dtl',
    'design/card_niet-beschikbaar.dtl',
    'plein/andere-sites.dtl',
    'plein/ga-naar-live-server.dtl',
    'feedback/sidebar.dtl',
    'functie/vhpg-tekst.dtl',
    'logboek/common.dtl',
    'snippets.dtl',
    'email_mailer/email_basis.dtl',
)


def end_of_run():
    """ Deze functie wordt aangeroepen aan het einde van een test run.
        Hier rapporteren we welke templates niet gecheckt zijn met assert_html_ok.
    """

    # do something special for a "test all" run
    if len(validated_templates) > 100:          # pragma: no branch
        # for dtl in validated_templates:
        #     print('Validated template: %s' % repr(dtl))
        # # for

        for dtl in Path().rglob('*.dtl'):
            dtl_str = str(dtl)
            is_email_template = '/templates/email_' in dtl_str
            dtl_str = dtl_str[dtl_str.find('/templates/')+11:]
            if dtl_str not in included_templates:       # pragma: no cover
                if dtl_str not in validated_templates:
                    if is_email_template:
                        print('[WARNING] Missing assert_email_html_ok coverage for template %s' % repr(dtl_str))
                    else:
                        print('[WARNING] Missing assert_html_ok coverage for template %s' % repr(dtl_str))

                if is_email_template and dtl_str not in consistent_email_templates:
                    print('[WARNING] Missing assert_consistent_email_html_text coverage for e-mail template %s' %
                          repr(dtl_str))
        # for


# end of file
