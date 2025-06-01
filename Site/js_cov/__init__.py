# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" In-brosser Javascript coverage measurement plugin for (python) Coverage """

from .coverage_plugin import JsCoveragePluginException  # noqa
from .coverage_plugin import JsCoveragePlugin


def coverage_init(reg, options):
    print('{jscov} registering')
    plugin = JsCoveragePlugin(options)
    reg.add_file_tracer(plugin)
    #reg.add_configurer(plugin)

# end of file
