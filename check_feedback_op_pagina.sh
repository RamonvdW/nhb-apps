#!/bin/bash

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# helper to check the uniqueness of the "op_pagina" for the feedback form

find . -name \*.dtl -exec grep "with op_pagina" {} \+ | cut -d':' -f2 | grep -E '^{' | cut -d' ' -f5 | sort | uniq -c | sort -n

# end of file
