fetch("/api/applied-jobs")
.then(res=>res.json())
.then(data=>{

let tbody=document.querySelector("#applied_table tbody")

data.forEach(job=>{

let row=`<tr>
<td>${job.title}</td>
<td>${job.company}</td>
<td>${job.location}</td>
<td>${job.applied_at}</td>
</tr>`

tbody.innerHTML+=row

})

})