/*!
 * Copyright (c) 2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

function stuur_post(url, csrfToken){
    let xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);         // true = async
    xhr.setRequestHeader("X-CSRFToken", csrfToken);
    xhr.send();
}

/* end of file */
