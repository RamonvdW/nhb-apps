/*!
 * Copyright (c) 2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

"use strict";

function stuur_post(url, csrfToken) {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);         // true = async
    xhr.setRequestHeader("X-CSRFToken", csrfToken);
    xhr.send();
}

window.addEventListener("load", function() {
    // alles is opgehaald en ingeladen
    const dataset = document.getElementById("js_data").dataset;
    stuur_post(dataset.urlPing, dataset.csrfToken);
});

/* end of file */
