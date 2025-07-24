/*!
 * Copyright (c) 2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

const dataset = document.getElementById("js_data").dataset;

function stuur_ping() {
    let xhr = new XMLHttpRequest();
    xhr.open("POST",
             dataset.urlPing,
       true);               // true = async
    xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
    xhr.send();
}

window.addEventListener("load", function() {
    // alles is opgehaald en ingeladen
    stuur_ping();
});

/* end of file */
