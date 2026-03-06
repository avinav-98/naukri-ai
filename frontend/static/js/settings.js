fetch("/api/settings")
.then(res=>res.json())
.then(data=>{

document.getElementById("job_role").value=data.job_role
document.getElementById("location").value=data.preferred_location
document.getElementById("experience").value=data.experience
document.getElementById("salary").value=data.salary
document.getElementById("pages").value=data.pages_to_scrape
document.getElementById("limit").value=data.auto_apply_limit

})


document.getElementById("settingsForm").addEventListener("submit",function(e){

e.preventDefault()

let data={

job_role:document.getElementById("job_role").value,
preferred_location:document.getElementById("location").value,
experience:document.getElementById("experience").value,
salary:document.getElementById("salary").value,
pages_to_scrape:document.getElementById("pages").value,
auto_apply_limit:document.getElementById("limit").value

}

fetch("/api/settings",{

method:"POST",
headers:{'Content-Type':'application/json'},
body:JSON.stringify(data)

})

alert("Settings saved")

})
