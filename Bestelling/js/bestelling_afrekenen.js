/*!
 * Copyright (c) 2022-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

const dataset = document.getElementById("js_data").dataset;

function verwijder(id) {
    const el = document.getElementById(id);
    const url = el.dataset.url;

    // voer een POST uit om toe te voegen
    let form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', url);

    let inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "csrfmiddlewaretoken";
    inp.value = dataset.csrfToken;
    form.appendChild(inp);

    form.style.display = 'hidden';
    document.body.appendChild(form);
    form.submit();
}

/* end of file */
