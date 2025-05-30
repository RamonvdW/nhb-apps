/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

// ### tabel filter ###

// wordt gebruikt om te reageren op de input van een gebruiker in een zoekveld
// en regels van de tabel wel/niet zichtbaar te maken
// kolommen waarin gezocht mag worden moeten het 'filter' attribuut hebben
//          <thead>
//              <tr>
//                  <th data-filter="on">Header1</th>
//                  <th>Header2<th>

// Uitgebreider voorbeeld:
//   <table class="sv-kader" id="table3">
//     <thead>
//       <tr>        <!-- filter veld -->
//         <td colspan="2"></td>
//         <td colspan="2" class="table-filter">
//            <input class="table-filter" oninput="tabel_filter(this, 'table3')" placeholder="Zoeken"/>
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

function tabel_filter(zoekveld, tableId)
{
    'use strict';
    const table = document.getElementById(tableId);
    if (table === null) {
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
    if (body === undefined)
        return;

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
        if (show) {
            if (row.style.display == "none") {
                row_deferred_show.push(i);      // voeg toe aan lijst
            }
        }
        else {
            if (row.style.display != "none") {
                row_deferred_hide.push(i);      // voeg toe aan lijst
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


// framework init, after everything has been loaded and instantiated
window.addEventListener("load", () => {
    // page is fully loaded

    // zoek alle tabellen met een zoekveld en trigger de oninput method
    // dit is noodzakelijk bij gebruik van de browser 'back' knop
    // anders zijn de tabellen niet meer gefiltreerd
    const tables = document.getElementsByTagName("table");
    Array.from(tables).forEach(table => {
        if (table.id !== "") {
            const inputs = table.getElementsByTagName("input");
            if (inputs.length >= 1) tabel_filter(inputs[0], table.id);
        }
    });
});

// end of file
