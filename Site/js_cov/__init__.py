# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" In-brosser Javascript coverage measurement plugin for (python) Coverage """

from .js_cov_plugin import JsCoveragePlugin


def coverage_init(reg, options):
    # note: cannot (easily) access Django settings, because coverage runs before Django starts
    # from django.conf import settings
    plugin = JsCoveragePlugin(options)
    reg.add_file_tracer(plugin)

# end of file
