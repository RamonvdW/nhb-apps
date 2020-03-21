#!/bin/bash
find . -name \*.dtl -exec grep "with op_pagina" {} \+ | cut -d':' -f2 | grep -E '^{' | cut -d' ' -f5 | sort | uniq -c | sort -n
# end of file
