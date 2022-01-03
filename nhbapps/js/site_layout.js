// Copyright (c) 2020-2022 Ramon van der Winkel.
// All rights reserved.
// Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


// helper functie om een opgeslagen cookie in te lezen
function getCookie(name) {
    let cookieValue = null
    if (document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";")
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim()
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}

// haalt het getal uit een cookie
// geef 0 terug als het cookie niet gezet is
// geef 0 terug als het cookie geen getal bevat
function getCookieNumber(name) {
    let value = getCookie(name)
    let number = 0
    if (value != null) {
        number = parseInt(value, 10)
        if (isNaN(number)) number = 0
    }
    return number
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
    const table = document.getElementById(tableId)
    if (table === undefined) return

    const filter = /[\u0300-\u036f]/g         // precompiled regexp, for performance gain
    const filter_tekst = zoekveld.value.normalize("NFD").replace(filter, "").toLowerCase()

    // doorzoek de header kolommen op data-filter=on
    const filter_kolommen = new Array()
    for (let row of table.tHead.rows)
    {
        let col_nr = 0
        for (let cell of row.cells)
        {
            if (cell.hasAttribute("data-filter")) filter_kolommen.push(col_nr)

            if (cell.hasAttribute("colSpan")) {
                col_nr += cell.colSpan
            } else {
                col_nr += 1
            }
        }
    }
    //console.log("kolom nummers met filter: ", filter_kolommen)

    const row_deferred_hide = new Array()     // deferred updates, for performance gain
    const row_deferred_show = new Array()

    const body = table.tBodies[0]
    for (let i=0; i < body.rows.length; i++)     // stops when row=null
    {
        const row = body.rows[i]
        const filter_cmd = row.dataset["tablefilter"]
        if (filter_cmd === "stop") break       // from the for

        // besluit om deze regel te tonen, of niet
        let show = false

        if (filter_tekst == "") {
            // performance optimization: converteren van elke tabel string
            // stellen we uit tot de gebruiker een eerste letter invoert
            show = true
        } else {
            // kijk of de zoekterm in een van de gekozen kolommen voorkomt
            filter_kolommen.forEach(kolom_nr => {
                const cell = row.cells[kolom_nr]
                //if (cell === undefined) { console.log('missing cell in kolom_nr=', kolom_nr, "in row", i) }
                let clean_text = cell.dataset["clean_text"]     // cached resultaat ophalen
                //console.log("clean_text:", clean_text)
                if (typeof clean_text === "undefined") {
                    // eerste keer: voer de vervorming uit en cache het resultaat op
                    clean_text = cell.innerText.normalize("NFD").replace(filter, "").toLowerCase()
                    cell.dataset["clean_text"] = clean_text
                }
                if (clean_text.indexOf(filter_tekst) != -1) show = true
            })
        }

        // onderzoek of een table row getoond of verstopt moet worden
        // sla het resultaat op, zodat we niet in een read-write-read-write cyclus komen
        // waarbij de browser steeds het hele scherm update voordat de read doorgang vindt
        // OLD: row.style.display = show ? "table-row" : "none";
        if (show) {
            if (row.style.display == "none") row_deferred_show.push(i)
        }
        else {
            if (row.style.display != "none") row_deferred_hide.push(i)
        }
    }

    //console.log("row_deferred_hide:", row_deferred_hide)
    //console.log("row_deferred_show:", row_deferred_show)

    // voor de deferred updates uit
    row_deferred_hide.forEach(row_nr => {
            body.rows[row_nr].style.display = "none"
        })
    row_deferred_show.forEach(row_nr => {
            body.rows[row_nr].style.display = "table-row"
        })
}


// end of file
