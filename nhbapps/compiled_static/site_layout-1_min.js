//Copyright(c) 2020-2022 Ramon van der Winkel.function getCookie(name){let cookieValue=nullif(document.cookie&&document.cookie!==""){let cookies=document.cookie.split(";")for(let i=0;i<cookies.length;i++){let cookie=cookies[i].trim()if(cookie.substring(0,name.length+1)===(name+"=")){cookieValue=decodeURIComponent(cookie.substring(name.length+1))break}}}return cookieValue}function getCookieNumber(name){let value=getCookie(name)let number=0if(value!=null){number=parseInt(value,10)if(isNaN(number)) number=0}return number}function myTableFilter(zoekveld,tableId){const table=document.getElementById(tableId)if(table===undefined) returnconst filter=/[\u0300-\u036f]/g         const filter_tekst=zoekveld.value.normalize("NFD").replace(filter,"").toLowerCase()const filter_kolommen=new Array()for(let row of table.tHead.rows){let col_nr=0for(let cell of row.cells){if(cell.hasAttribute("data-filter")) filter_kolommen.push(col_nr)if(cell.hasAttribute("colSpan")){col_nr+=cell.colSpan}else{col_nr+=1}}}const row_deferred_hide=new Array()     const row_deferred_show=new Array()const body=table.tBodies[0]for(let i=0;i<body.rows.length;i++)     {const row=body.rows[i]const filter_cmd=row.dataset["tablefilter"]if(filter_cmd==="stop") break       let show=falseif(filter_tekst==""){show=true}else{filter_kolommen.forEach(kolom_nr => {const cell=row.cells[kolom_nr]let clean_text=cell.dataset["clean_text"]     if(typeof clean_text==="undefined"){clean_text=cell.innerText.normalize("NFD").replace(filter,"").toLowerCase()cell.dataset["clean_text"]=clean_text}if(clean_text.indexOf(filter_tekst)!=-1) show=true})}if(show){if(row.style.display=="none") row_deferred_show.push(i)}else{if(row.style.display!="none") row_deferred_hide.push(i)}}row_deferred_hide.forEach(row_nr => {body.rows[row_nr].style.display="none"})row_deferred_show.forEach(row_nr => {body.rows[row_nr].style.display="table-row"})}