/*!
 * Copyright (c) 2022-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

function ophalen_klaar(xhr) {
    // console.log('ophalen_klaar: ready=',xhr.readyState, 'status=', xhr.status);
    if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
        // verzoek is klaar en we hebben een antwoord
        // responseText is leeg bij connection failure
        if (xhr.responseText !== "") {
            const rsp = JSON.parse(xhr.responseText);
            const bondspas_data = rsp['bondspas_base64'];
            const el_img = document.getElementById('id_image');

            el_img.src = "data:image/jpeg;base64," + bondspas_data;
            el_img.style.display = "inline-block";

            // "Je bondspas wordt opgehaald" bericht weghalen
            const el = document.getElementById('id_even_wachten');
            el.style.display = "none";

            // download knop zichtbaar maken
            const el_dl = document.getElementById('id_download_knop');
            el_dl.style.display = "inherit";
        }
    }
}

function ophalen_timeout(xhr) {
    // voorkom reactie bij ontvangst laat antwoord
    xhr.abort();

    // note: ophalen_klaar wordt zo aangeroepen met readyState=0
    // deze kan een melding doen naar de gebruiker
}


window.addEventListener("load", function() {
    // alles is opgehaald en ingeladen
    const dataset = document.getElementById("js_data").dataset;

    let xhr = new XMLHttpRequest();

    // POST voorkomt caching
    xhr.open("POST", dataset.urlDynamic, true);         // true = async
    xhr.timeout = 60000;                                 // 60 sec voor trage verbinding
    xhr.onloadend = ophalen_klaar;
    xhr.ontimeout = ophalen_timeout;
    //xhr.onloadend = function(){ ophalen_klaar(xhr); };
    //xhr.ontimeout = function(){ ophalen_timeout(xhr); };
    xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
    xhr.send();
});

/* end of file */
