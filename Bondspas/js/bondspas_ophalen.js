/*!
 * Copyright (c) 2022-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

const dataset = document.getElementById("js_data").dataset;

const el_img = document.getElementById('id_image');
const el_even_wachten = document.getElementById('id_even_wachten');
const el_download_knop = document.getElementById('id_download_knop');

let timeout60s = 60000;     // 60 sec voor trage verbinding


function toon_foutmelding() {
    const el_p = el_even_wachten.firstElementChild;
    el_p.style.color = "red";
    el_p.innerText = "Er is een fout opgetreden";
}


function ophalen_klaar(xhr) {
    //console.log('ophalen_klaar: ready=',xhr.readyState, 'status=', xhr.status);
    if (xhr.readyState === XMLHttpRequest.DONE) {
        let toon_fout = true;

        if (xhr.status === 200) {
            // verzoek is klaar en we hebben een antwoord
            // responseText is leeg bij connection failure
            if (xhr.responseText !== "") {
                try {
                    /** @param rsp.bondspas_base64 **/
                    const rsp = JSON.parse(xhr.responseText);
                    const bondspas_data = rsp.bondspas_base64;
                    toon_fout = false;

                    el_img.src = "data:image/jpeg;base64," + bondspas_data;
                    el_img.style.display = "inline-block";

                    // "Je bondspas wordt opgehaald" bericht weghalen
                    el_even_wachten.style.display = "none";

                    // download knop zichtbaar maken
                    el_download_knop.style.display = "inherit";
                } catch (e) {
                    // waarschijnlijk geen goede JSON data
                    // een Http404() geeft een foutmelding pagina met status=200 (OK) en komt hier terecht
                }
            }
        }

        if (toon_fout) {
            toon_foutmelding();
        }
    }
}


function ophalen_timeout(xhr) {
    // voorkom reactie bij ontvangst laat antwoord
    xhr.abort();

    toon_foutmelding();
    // note: ophalen_klaar wordt zo aangeroepen met readyState=0
}


window.addEventListener("load", function() {
    // alles is opgehaald en ingeladen

    let xhr = new XMLHttpRequest();

    // POST voorkomt caching
    xhr.open("POST", dataset.urlDynamic, true);        // true = async
    xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
    xhr.timeout = timeout60s;
    xhr.onloadend = function() {
                        ophalen_klaar(xhr);
                    };
    xhr.ontimeout = function() {
                        ophalen_timeout(xhr);
                    };
    xhr.send();
});


// support for testing timeouts
if (localStorage.getItem("js_cov_short_timeout")) {
    timeout60s = 1;
}

/* end of file */
