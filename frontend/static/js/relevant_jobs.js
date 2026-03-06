fetch("/api/relevant-jobs")
.then(res=>res.json())
.then(data=>{

let tbody=document.querySelector("#relevant_table tbody")

data.forEach(job=>{

let row=`<tr>
<td>${job.title}</td>
<td>${job.company}</td>
<td>${job.location}</td>
<td>${job.score ?? "-"}</td>
<td><a href="${job.url}" target="_blank">Open</a></td>
</tr>`

tbody.innerHTML+=row

})

})
