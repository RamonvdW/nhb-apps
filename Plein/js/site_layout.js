/*!
 * Copyright (c) 2020-2023 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */

// helper functie om een opgeslagen cookie in te lezen
function getCookie(name) {
    'use strict';
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// haalt het getal uit een cookie
// geef 0 terug als het cookie niet gezet is
// geef 0 terug als het cookie geen getal bevat
function getCookieNumber(name) {
    'use strict';
    let value = getCookie(name);
    let number = 0;
    if (value != null) {
        number = parseInt(value, 10);
        if (isNaN(number)) {
            number = 0;
        }
    }
    return number;
}


// ### tabel filter ###

// wordt gebruikt om te reageren op de input van een gebruiker in een zoekveld
// en regels van de tabel wel/niet zichtbaar te maken
// kolommen waarin gezocht mag worden moeten het 'filter' attribuut hebben
//          <thead>
//              <tr>
//                  <th data-filter="on">Header1</th>
//                  <th>Header2<th>

// Uitgebreider voorbeeld:
//   <table class="white" id="table3">
//     <thead>
//       <tr>        <!-- filter veld -->
//         <td colspan="2"></td>
//         <td colspan="2" class="table-filter">
//            <input class="table-filter" oninput="myTableFilter(this, 'table3')" placeholder="Zoeken"/>
//         </td>
//         <td colspan="3"></td>
//       </tr>
//       <tr>
//         <th>Laatste poging</th>
//         <th>Laatste inlog</th>
//         <th data-filter="on">Inlog</th>
//         <th data-filter="on">Naam</th>
//         <th>Email is bevestigd</th>
//         <th>Tweede factor</th>
//         <th>Aangemaakt</th>
//       </tr>
//     </thead>

function myTableFilter(zoekveld, tableId)
{
    'use strict';
    const table = document.getElementById(tableId);
    if (table === undefined) {
        return;
    }

    const filter = /[\u0300-\u036f]/g;         // precompiled regexp, for performance gain
    const filter_tekst = zoekveld.value.normalize("NFD").replace(filter, "").toLowerCase();

    // doorzoek de header kolommen op data-filter=on
    const filter_kolommen = [];
    for (let row of table.tHead.rows)
    {
        let col_nr = 0;
        for (let cell of row.cells)
        {
            if (cell.hasAttribute("data-filter")) {
                filter_kolommen.push(col_nr);
            }

            if (cell.hasAttribute("colSpan")) {
                col_nr += cell.colSpan;
            } else {
                col_nr += 1;
            }
        }
    }
    //window.console.log("kolom nummers met filter: ", filter_kolommen)

    const row_deferred_hide = [];       // deferred updates, for performance gain
    const row_deferred_show = [];

    const body = table.tBodies[0];
    for (let i=0; i < body.rows.length; i++)     // stops when row=null
    {
        const row = body.rows[i];
        const filter_cmd = row.dataset.tablefilter;
        if (filter_cmd === "stop") {
            break;      // from the for
        }

        // besluit om deze regel te tonen, of niet
        let show = false;

        if (filter_tekst === "") {
            // performance optimization: converteren van elke tabel string
            // stellen we uit tot de gebruiker een eerste letter invoert
            show = true;
        } else {
            // kijk of de zoekterm in een van de gekozen kolommen voorkomt
            filter_kolommen.forEach(kolom_nr => {
                const cell = row.cells[kolom_nr];
                if (cell === undefined) {
                    window.console.log('missing cell in kolom_nr=', kolom_nr, "in row", i, "of row", row);
                }
                let clean_text = cell.dataset.clean_text;    // cached resultaat ophalen
                //window.console.log("clean_text:", clean_text);
                if (typeof clean_text === "undefined") {
                    // eerste keer: voer de vervorming uit en cache het resultaat op
                    clean_text = cell.innerText.normalize("NFD").replace(filter, "").toLowerCase();
                    cell.dataset.clean_text = clean_text;
                }
                if (clean_text.indexOf(filter_tekst) != -1) {
                    show = true;
                }
            });
        }

        // onderzoek of een table row getoond of verstopt moet worden
        // sla het resultaat op, zodat we niet in een read-write-read-write cyclus komen
        // waarbij de browser steeds het hele scherm update voordat de read doorgang vindt
        // OLD: row.style.display = show ? "table-row" : "none";
        if (show) {
            if (row.style.display == "none") {
                row_deferred_show.push(i);
            }
        }
        else {
            if (row.style.display != "none") {
                row_deferred_hide.push(i);
            }
        }
    }

    //window.console.log("row_deferred_hide:", row_deferred_hide)
    //window.console.log("row_deferred_show:", row_deferred_show)

    // voor de deferred updates uit
    row_deferred_hide.forEach(row_nr => {
            body.rows[row_nr].style.display = "none";
        });
    row_deferred_show.forEach(row_nr => {
            body.rows[row_nr].style.display = "table-row";
        });
}


// filter activeer knop afhandeling
//
// filters moeten de namen "filter_1", "filter_2" hebben
// elke radiobutton moet een 'url' in zijn dataset hebben
// maximaal 8 filters
// 1 element met id "filters" moet de template url hebben met daarin ~1, ~2, etc. die vervangen moeten worden
// meerdere knoppen kunnen een onclick hebben met filters_activate()
//
// voorbeeld:
//     <h4
//        id="filters"                        <--
//        data-url="{{ filter_url }}">        <--
//        Filters
//     </h4>
//     <b>Kies een regio:</b>
//     <ul>
//         {% for filter in regio_filters %}
//             <li>
//                 <label for="id_{{ filter.sel }}">
//                     <input
//                        type="radio"
//            -->         name="filter_2"
//                        value="{{ filter.sel }}"
//                        required id="id_{{ filter.sel }}"
//                        {% if filter.selected %}checked{% endif %}
//            -->         data-url="{{ filter.url_part }}">
//                     <span>{{ filter.opt_text }}</span>
//                 </label>
//             </li>
//         {% endfor %}
//     </ul>
//     <a onclick="filter_activate()">Activeer</a>

function filters_activate() {
    'use strict';

    // get the template url (with the ~1 etc in it)
    let url = document.getElementById("filters").dataset.url;

    // replace the ~1 etc. as far as present in the url
    for(let nr=1; nr<8; nr++) {
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
// bij het maken van een wijziging wordt deze doorgezet naar het andere filter
//
// voorbeeld:
//
//          <input type="radio"
//                 name="filter_4"
//                 value="{{ filter.sel }}"
//                 data-url="{{ filter.url_part }}">
//
//          <input type="radio"
//                 name="makl2"
//                 value="{{ filter.sel }}"
//        -->      onchange="mirror_radio('makl2', 'filter_4')">
//
function mirror_radio(src_name, dst_name) {
    'use strict';

    // zoek het geselecteerde element in de bron radiobutton set
    const src_sel = "input[type='radio'][name=" + src_name + "]:checked";
    const src_value = document.querySelector(src_sel).value;

    // zoek dezelfde optie in de andere radiobutton set
    const dst_sel = "input[type='radio'][name=" + dst_name + "][value=" + src_value + "]";
    const dst_el = document.querySelector(dst_sel);

    // activeer de juiste optie
    dst_el.checked = true;
}

// end of file
