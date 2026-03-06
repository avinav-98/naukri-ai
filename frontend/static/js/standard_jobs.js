fetch("/standard-jobs")
.then(res=>res.json())
.then(data=>{

let tbody=document.querySelector("#standard_table tbody")

data.forEach(job=>{

let row=`<tr>
<td>${job.title}</td>
<td>${job.company}</td>
<td>${job.location}</td>
<td><a href="${job.url}" target="_blank">Apply</a></td>
</tr>`

tbody.innerHTML+=row

})

})