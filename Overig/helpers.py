# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


def get_safe_from_ip(request):
    """ This helper returns the IP address of the request
        and makes sure it is a safe string that just contains an IP address
        any garbage is removed
    """

    # filter out any character that is not part of a valid IPv4 or IPv6 IP address
    # (max length 15) IPv4:                     100.200.100.200
    # (max length 39) IPv6:                     0000:0000:0000:0000:0000:0000:0000:0000
    # (max length 45) IPv6 mapped IPv4 address: 0000:0000:0000:0000:0000:ffff:100.200.100.200

    safe_ip = ""

    if request:
        try:
            from_ip = request.META['REMOTE_ADDR']
        except (KeyError, AttributeError):
            pass
        else:
            for chr in from_ip:
                if chr in '0123456789ABCDEFabcdef:.':
                    safe_ip += chr
            # for

            # also limit it in length
            safe_ip = safe_ip[:46]
    # if

    return safe_ip


# end of file
