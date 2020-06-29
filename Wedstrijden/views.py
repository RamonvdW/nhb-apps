# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from Plein.menu import menu_dynamics


# end of file
