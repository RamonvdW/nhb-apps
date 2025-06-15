# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

def zet_sessionvar_if_changed(request, var_name: str, value) -> bool:
    """ voorkom onnodige opslaan van een sessie door onnodige wijzigingen niet te doen

        Return value:
            True:  Value different; was stored
            False: Value identical; not stored
    """
    changed = False
    curr_value = request.session.get(var_name, None)
    if curr_value != value:
        request.session[var_name] = value
        changed = True
    return changed


# end of file
