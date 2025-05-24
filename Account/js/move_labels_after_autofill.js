/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

"use strict";

// respond to browser auto-fill of login dialog, especially password field
// no events are fired (for security) and the value itself is not accessible,
// but we need to move the label out of the way to avoid visual overlap

function delayedUpdate() {
    const els = document.querySelectorAll('input[type=text]:-webkit-autofill, input[type=password]:-webkit-autofill');
    els.forEach(el => {
        const el2 = el.previousSibling;
        el2.classList.add('active');
    })
}

document.addEventListener("DOMContentLoaded", function() {
    // not all devices are equally fast, so repeat to ensure quick response when possible
    setTimeout(delayedUpdate, 50);
    setTimeout(delayedUpdate, 100);
    setTimeout(delayedUpdate, 200);
    setTimeout(delayedUpdate, 500);
    setTimeout(delayedUpdate, 1000);
})

/* end of file */
