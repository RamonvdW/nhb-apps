/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

function activeer_deel() {
    // vind de gekozen radiobutton
    const el = document.querySelector("input[type='radio'][name='deel']:checked");

    // haal de url op van het input element en navigeer daar naartoe
    window.location.href = el.dataset.url;
}

/* end of file */
