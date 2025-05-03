/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */
function do_selecteer(id){const dataset=document.getElementById("js_data").dataset;const form=document.createElement('form');form.setAttribute('method','post');form.setAttribute('action',dataset.url);let inp=document.createElement('input');inp.type="hidden";inp.name="selecteer";inp.value=id.dataset.pk;form.appendChild(inp);inp=document.createElement('input');inp.type="hidden";inp.name="csrfmiddlewaretoken";inp.value=dataset.csrfToken;form.appendChild(inp);form.style.display='hidden';document.body.appendChild(form);form.submit();}