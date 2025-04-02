# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


class SpecificExitCode(Exception):
    """ when raised, the provided value is used as the program exit code

        use this instead of sys.exit(n), which raises SystemExit that is caught, logged and replaced with exit code 3.
    """
    pass


# end of file
