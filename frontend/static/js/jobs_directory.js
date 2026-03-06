async function loadJobs(){

let response = await fetch("/api/jobs-directory")
let jobs = await response.json()

let table = document.getElementById("jobs_table")

jobs.forEach(job=>{

let row = `
<tr>
<td>${job.title}</td>
<td>${job.company}</td>
<td>${job.location}</td>
<td><a href="${job.url}" target="_blank">View</a></td>
</tr>
`

table.innerHTML += row

})

}

loadJobs()
