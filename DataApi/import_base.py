# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

class ImportCrmBase:

    """ Basis klasse waar alle importeer helpers van afgeleid worden

        Hier bieden we de standaard interface aan en een paar helpers.
    """

    def __init__(self, stdout, dryrun: bool, aanmelddatum: str, afmelddatum: str):
        self.stdout = stdout
        self.dryrun = dryrun
        self.exit_error = False

        self.aanmelddatum = aanmelddatum
        self.afmelddatum = afmelddatum

        self.count_errors = 0
        self.count_warnings = 0
        self.count_wijzigingen = 0
        self.count_toevoegingen = 0
        self.count_verwijderingen = 0

    def out_warning(self, msg: str):
        assert msg[0] != '['
        self.stdout.write('[WARNING] %s' % msg)
        self.count_warnings += 1

    def out_error(self, msg: str):
        assert msg[0] != '['
        self.stdout.write('[ERROR] %s' % msg)
        self.count_errors += 1

    def out_info(self, msg: str):
        assert msg[0] != '['
        self.stdout.write('[INFO] %s' % msg)

    def out_debug(self, msg: str):
        assert msg[0] != '['
        self.stdout.write('[DEBUG] %s' % msg)

    def check_keys(self, keys, verplichte_keys: tuple, optionale_keys: tuple, level: str):
        has_error = False

        keys = list(keys)       # iterator --> lijst waar we element uit kunnen halen

        # check the verplichte keys
        for key in verplichte_keys:
            try:
                keys.remove(key)
            except ValueError:
                self.stdout.write("[ERROR] [FATAL] Verplichte sleutel %s niet aanwezig in de %s data" % (
                                    repr(key), repr(level)))
                self.exit_error = True
                has_error = True
        # for

        # check the optionele keys
        for key in optionale_keys:
            try:
                keys.remove(key)
            except ValueError:
                pass

        if len(keys):
            self.stdout.write("[WARNING] Extra sleutel aanwezig in de %s data: %s" % (repr(level), repr(keys)))
            self.count_warnings += 1

        return has_error

    def extract_huisnummer(self, straat_huis_nr: str) -> int:
        """
            straat_huis_nr:
                "Eerste straat 1" --> 1
                "Tweede straat 2bis" --> 2
                "Derde straat 3 A" --> 3
                "3e straat 4" --> 4
                "" --> 0
        """
        huis_nr = 0
        spl = straat_huis_nr.split(' ')
        # remove empty split parts
        spl = [elem
               for elem in spl
               if elem]
        while len(spl) > 0 and not spl[-1][0].isdigit():
            spl.pop(-1)
        # while

        if len(spl) > 0:
            huis_nr_str = spl[-1]
            # if not huis_nr_str.isdigit():
            #     self.out_debug('Uitdaging: huis_nr_str = %s' % repr(huis_nr_str))
            while len(huis_nr_str) > 0 and not huis_nr_str.isdigit():
                huis_nr_str = huis_nr_str[:-1]
            huis_nr = int(huis_nr_str)

        # self.out_debug('Split straat_huis_nr %s --> %s' % (repr(straat_huis_nr), huis_nr))
        return huis_nr

# end of file
