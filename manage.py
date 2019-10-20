#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django's command-line utility for administrative tasks.
"""

import os
import sys
from django.core.management import execute_from_command_line

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhb-apps.settings')
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

# end of file

