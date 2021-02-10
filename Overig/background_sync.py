# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Helper om een ping te geven aan een management taak die in de achtergrond draait
    en wacht op een nieuwe opdracht, welke via de database doorgegeven moet worden.

    Elke taak kan met een unieke naam benaderd worden.
"""

import socket
import select


class BackgroundSync(object):

    """ Poort nummer moeten gelijk zijn aan de zendende en ontvangende kant
        en moeten dus globaal gealloceerd worden, typisch in settings.py
    """
    def __init__(self, poort_nummer):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._address = ('localhost', poort_nummer)
        self._conn = None
        self._listener = None

    def _setup_receiver(self):
        if not self._conn:
            self._sock.bind(self._address)
            self._sock.setblocking(False)
            self._conn = 1

    def ping(self):
        self._sock.sendto(b'ping', self._address)

    def wait_for_ping(self, timeout=1.0) -> bool:
        """ returns True when a ping was received or False in case of a timeout """
        got_ping = False

        self._setup_receiver()

        # wait for data to arrive, or timeout
        select.select((self._sock,), (), (), timeout)

        # try to read the data, regardless of whether anything arrived
        # this works because the socket is non-blocking
        try:
            data = self._sock.recv(10)
        except BlockingIOError:
            # no data received
            pass
        else:
            # receive some data
            got_ping = True

        return got_ping

# end of file
