document.addEventListener("DOMContentLoaded", function () {

loadDashboardStats()

})


function loadDashboardStats(){

fetch("/api/dashboard-stats")
.then(response => response.json())
.then(data => {

let total = document.getElementById("total_jobs")
if(!total){
total = document.getElementById("jobs_directory")
}
let relevant = document.getElementById("relevant_jobs")
let applied = document.getElementById("applied_jobs")

if(total){
total.innerText = data.scraped
}

if(relevant){
relevant.innerText = data.relevant
}

if(applied){
applied.innerText = data.applied
}

})
.catch(error => {

console.log("Dashboard API Error:", error)

})

}
