#!/bin/bash

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

rm requirements.txt
pip-compile requirements.in

rm requirements_test.txt
pip-compile requirements_test.in

rm requirements_dev.txt 
pip-compile requirements_dev.in

# end of file

