/*!
 * Copyright (c) 2022-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

const dataset = document.getElementById("js_data").dataset;
let pogingen = 20;      // komt overeen met 20 seconden

const el_status = document.getElementById("id_status");
const el_knop = document.getElementById("id_afschrift");

let timeout5s = 5000;


function status_ophalen_klaar(xhr)
{
    let retry = true;

    //console.log('xhr: ready=',xhr.readyState, 'status=', xhr.status);
    if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
        // verzoek is klaar en we hebben een antwoord
        // responseText is leeg bij connection failure
        if (xhr.responseText !== "") {
            let rsp;
            try {
                /** @param rsp.status: string **/
                rsp = JSON.parse(xhr.responseText);
            } catch(e) {
                // waarschijnlijk geen goede JSON data
                // een Http404() geeft een foutmelding pagina met status=200 (OK) en komt hier terecht
                rsp = "fout";
            }
            //console.log('rsp=', rsp);
            if ("status" in rsp) {
                const status = rsp.status;

                // status kan zijn:
                // - nieuw: nog niet opgestart
                // - betaal: we wachten op de betaling
                // - afgerond: de betaling is afgerond
                // - mislukt: de betaling is niet gelukt (final)
                // - error: onverwachte fout

                if (status === "afgerond") {
                    // toon de gebruiker dat de betaling binnen is
                    el_status.innerText = "De betaling is gelukt";

                    // enable de knop 'Toon afschrift'
                    el_knop.style.display = "inline-block";

                    // niet nodig om te blijven checken
                    pogingen = 0;
                    retry = false;
                } else if (status === "mislukt") {
                    // toon de gebruiker dat de betaling afgebroken/mislukt is
                    el_status.innerText = "De betaling is niet gelukt";

                    // niet nodig om te blijven checken
                    pogingen = 0;
                    retry = false;
                }
            }
        }
    }

    if (retry) {
        // over 1 seconde opnieuw proberen
        setTimeout(check_status_bestelling, 1000);
    }
}


function status_ophalen_timeout(xhr) {
    // voorkom reactie bij ontvangst laat antwoord
    xhr.abort();

    // doe de volgende status check over 1 seconde
    setTimeout(check_status_bestelling, 1000);
}


function check_status_bestelling() {
    // haal de status van de bestelling op
    // als de checkout_url beschikbaar is, redirect dan daar naartoe
    // wacht anders 1 seconde en herhaal de check
    if (pogingen > 0) {
        pogingen -= 1;

        // POST voorkomt caching
        const xhr = new XMLHttpRequest();
        xhr.open("POST",
                 dataset.urlStatusCheck,
                 true);          // true = async
        xhr.timeout = timeout5s;
        xhr.onloadend = function() {
                            status_ophalen_klaar(xhr);
                        };
        xhr.ontimeout = function() {
                            status_ophalen_timeout(xhr);
                        };
        xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
        xhr.send();     // no data
    }
}


window.addEventListener("load", function()  {
    // doe de eerste status check over 250ms
    setTimeout(check_status_bestelling, 250);
});


// support for testing timeouts
if (localStorage.getItem("js_cov_short_timeout")) {
    timeout5s = 1;
}


/* end of file */
