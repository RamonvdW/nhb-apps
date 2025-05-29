/*!
 * Copyright (c) 2022-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

"use strict";

/* jshint esversion: 6 */

const js_fotos = JSON.parse(document.getElementById('js_fotos').textContent);
// console.log(js_fotos);

const foto_elements = [];
js_fotos.forEach(arr => {
    let [volgorde, id_thumb, id_img] = arr;
    let tup = [volgorde,
                     document.getElementById(id_thumb),
                     document.getElementById(id_img)];
    foto_elements.push(tup);
});
// console.log(foto_elements);

// activeer een van de product foto's en vraag om de volgende in te laden
function kies_foto(nr) {
    //console.log('nr', nr);
    foto_elements.forEach(arr => {
        let [volgorde, el_thumb, el_img] = arr;

        if (volgorde === nr) {
            el_thumb.classList.add("sv-foto-thumb-selected");
            el_img.hidden = false;
        } else {
            el_thumb.classList.remove("sv-foto-thumb-selected");
            el_img.hidden = true;
        }

        // on-demand loading of the next photo
        if (volgorde === nr + 1) {
            el_img.loading = 'eager';
        }
    });
}

// activeer de eerste foto meteen
kies_foto(js_fotos[0][0]);

/* end of file */
