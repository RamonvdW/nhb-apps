/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console */
"use strict";


/* pagina filters

    Meerdere radio-button groepen die samen een URL maken.

    Pagina moet een element hebben met id="filter" en data-url= de url met ~1, ~2, etc. als placeholders (maximaal 8).
    De radio-button groepen moeten een id="filter_#" hebben (# = 1, 2, 3, etc.) overeenkomstig ~1, ~2, etc.
    Elk van de radio-button elementen moet een data-url_part="xxx" hebben met de tekst voor ~1, ~2, etc.

    Pagina kan meerdere knoppen hebben om het filter te activeren.
    Deze moeten de class "btn-sv-activeer-filter" hebben. De onclick handler wordt er automatisch aan gekoppeld.

    De click handler navigeert naar een andere pagina aan de hand van de url die geconstrueerd is.

    voorbeeld:
        <h4
           id="filters"                        <--
           data-url="{{ url_filter }}">        <-- "/app/func/~1/regio-~2/"
           Filters
        </h4>
        <b>Kies een regio:</b>
        <ul>
            {% for filter in regio_filters %}
                <li>
                    <label for="id_{{ filter.sel }}">
                        <input
                           type="radio"
               -->         name="filter_2"
                           value="{{ filter.sel }}"
                           required id="id_{{ filter.sel }}"
                           {% if filter.selected %}checked{% endif %}
               -->         data-url="{{ filter.url_part }}">
                        <span>{{ filter.opt_text }}</span>
                    </label>
                </li>
            {% endfor %}
        </ul>
        <button
            class="btn-sv-rood btn-sv-activeer-filter"      <--
            >Activeer</button>
 */


function activeer_filter(event) {

    // get the template url (with the ~1 etc in it)
    let url = document.getElementById("filters").dataset.url;

    // replace the ~1 etc. as far as present in the url
    for (let nr = 1; nr < 8; nr++) {
        let tilde_nr = '~' + nr;
        if (url.includes(tilde_nr)) {
            let el = document.querySelector("input[name='filter_" + nr + "']:checked");
            if (!el) {
                // find the backup, typically <input type="hidden" ..>
                el = document.querySelector("input[name='filter_" + nr + "']");
            }
            url = url.replace(tilde_nr, el.dataset.url);
        }
    }

    // navigate to the final url
    window.location.href = url;
}


// radio button groups in sync laten lopen
// gebruik: als een filter meerdere keren voorkomt, ivm layout (media queries)
// bij het maken van een keuze (klik op de radio button),
// dan wordt deze doorgezet naar het andere (niet zichtbare) filter
//
// class="sv-mirror-filter" wordt gebruikt om een functie te koppelen aan het change event
//
// voorbeeld:
//
//          <input type="radio"
//                 name="filter_4"
//                 value="{{ filter.sel }}"
//                 data-url="{{ filter.url_part }}"
//        -->      class="sv-mirror-filter"
//        -->      data-mirror-dest="makl2">>
//
//          <input type="radio"
//                 name="makl2"
//                 value="{{ filter.sel }}"
//        -->      class="sv-mirror-filter"
//        -->      data-mirror-dest="filter_4">
//
function mirror_filter(event) {
    const el_src = event.target;
    const dest_name = el_src.dataset.mirrorDest;

    // elk filter heeft meerdere radio opties met verschillende "value"
    // vind de juiste radio input om te activeren
    const src_value = el_src.value;
    const dest_sel = "input[type='radio'][name=" + dest_name + "][value=" + src_value + "]";
    const el_dest = document.querySelector(dest_sel);

    // activeer de gevonden radiobutton
    el_dest.checked = true;
}


// koppel de filter activeer knop "click" event aan de activeer functie
document.addEventListener('DOMContentLoaded', function() {

    // koppel het click event van de knoppen aan de activeer functie
    const els_button = document.getElementsByClassName('btn-sv-activeer-filter');
    Array.from(els_button).forEach(el_button => {
        el_button.addEventListener('click', activeer_filter);
    });

    // koppel het change event van de radio inputs aan de mirror functie
    const els_radio_inputs = document.getElementsByClassName('sv-mirror-filter');
    Array.from(els_radio_inputs).forEach(el_radio_input => {
        el_radio_input.addEventListener('change', mirror_filter);
    });
});

// end of file
