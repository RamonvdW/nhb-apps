/*!
 * Copyright (c) 2022-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console */
"use strict";

const dataset = document.getElementById("js_data").dataset;
let pogingen = 20;      // komt overeen met 20 seconden

const el_bericht = document.getElementById('id_bericht');
const el_teller = document.getElementById('id_teller');

let timeout5s = 5000;


function toon_melding_in_rood(msg) {
    el_bericht.innerText = msg;
    el_bericht.classList.add('sv-rood-text');
}


function status_ophalen_klaar(xhr)
{
    let retry = true;

    //console.log('xhr: ready=',xhr.readyState, 'status=', xhr.status);
    if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status === 200) {
            // verzoek is klaar en we hebben een antwoord
            // responseText is leeg bij connection failure
            if (xhr.responseText !== "") {
                let rsp;
                try {
                    /** @param rsp.status:string **/
                    /** @param rsp.checkout_url **/
                    rsp = JSON.parse(xhr.responseText);
                } catch(e) {
                    // waarschijnlijk geen goede JSON data
                    // een Http404() geeft een foutmelding pagina met status=200 (OK) en komt hier terecht
                    rsp = {};
                }
                //console.log('rsp=', rsp);
                if ("status" in rsp) {
                    const status = rsp.status;

                    // status kan zijn:
                    // - nieuw: nog niet opgestart
                    // - betaal: we wachten op de betaling
                    // - afgerond: de betaling is afgerond (final)
                    // - mislukt: de betaling is niet gelukt (final)
                    // - error: onverwachte fout

                    if (status === "nieuw") {
                        // checkout_url is nog niet beschikbaar
                        retry = true;

                    }  else if (status === "betaal") {
                        // redirect naar de checkout_url
                        window.location.href = rsp.checkout_url;
                        // won't get here

                    } else if (status === "mislukt") {
                        // betaling is afgebroken / expired
                        el_bericht.innerText = "De betaling is niet gelukt";

                        retry = false;      // stop trying

                    } else if (status === "error") {
                        // intern probleem
                        toon_melding_in_rood("Er is een probleem opgetreden met deze bestelling");

                        retry = false;      // stop trying
                    }
                }
            }
        }
        // else: fout
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
        el_teller.innerText = pogingen;
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
    } else {
        toon_melding_in_rood("Het is op dit moment niet mogelijk om te betalen. Probeer het later nog eens");
    }
}


window.addEventListener("load", function() {
    // doe de eerste status check over 250ms
    setTimeout(check_status_bestelling, 250);
});


// support for testing timeouts
if (localStorage.getItem("js_cov_short_timeout")) {
    timeout5s = 1;
}


/* end of file */
