$ErrorActionPreference = "Stop"
$Base = "http://localhost:8001"
Write-Host "1. Health"
Invoke-RestMethod "$Base/api/health" | Format-List

Write-Host "2. Patient login"
$Login = Invoke-RestMethod "$Base/api/auth/login" -Method Post -ContentType "application/json" -Body (@{username="john";password="patient123"} | ConvertTo-Json)
$Headers = @{Authorization="Bearer $($Login.access_token)"}
$Me = Invoke-RestMethod "$Base/api/auth/me" -Headers $Headers
$Summary = Invoke-RestMethod "$Base/api/patients/me/summary" -Headers $Headers
Write-Host "Logged in as $($Me.full_name); patient id $($Me.patient_id)"

Write-Host "3. Patient chat"
$Chat = Invoke-RestMethod "$Base/api/agent/message" -Method Post -Headers $Headers -ContentType "application/json" -Body (@{patient_id=$Me.patient_id;message="Help me book an appointment";channel="WEB"} | ConvertTo-Json)
$Chat | Format-List

Write-Host "4. Doctor login"
$Doctor = Invoke-RestMethod "$Base/api/auth/login" -Method Post -ContentType "application/json" -Body (@{username="drjones";password="doctor123"} | ConvertTo-Json)
$DoctorHeaders = @{Authorization="Bearer $($Doctor.access_token)"}
$Stats = Invoke-RestMethod "$Base/api/dashboard/stats" -Headers $DoctorHeaders
$Stats | Format-List

Write-Host "Smoke test complete."
