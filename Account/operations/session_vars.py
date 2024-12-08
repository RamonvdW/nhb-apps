# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

def zet_sessionvar_if_changed(request, var_name, value):
    """ voorkom onnodig opslaan van een sessie
    """

    curr_value = request.session.get(var_name, None)
    if curr_value != value:
        request.session[var_name] = value


# end of file
