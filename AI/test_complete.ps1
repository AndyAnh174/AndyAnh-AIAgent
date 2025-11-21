# Complete System Test
$baseUrl = "http://localhost:8000"
$apiKey = "local-dev-key-1"
$headers = @{"x-api-key" = $apiKey; "Content-Type" = "application/json"}

$passed = 0
$failed = 0
$warnings = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  COMPREHENSIVE SYSTEM TEST" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health
Write-Host "[1/6] Health Check..." -ForegroundColor Yellow
try {
    $h = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    if ($h.status -eq "ok") {
        Write-Host "  PASS" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  FAIL" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Test 2: Text Entry
Write-Host "[2/6] Text Journal Entry..." -ForegroundColor Yellow
try {
    $e = @{
        title = "Test Entry"
        content = "Test content"
        tags = @("test")
        media = @()
    } | ConvertTo-Json
    
    $r = Invoke-RestMethod -Uri "$baseUrl/journal" -Method POST -Body $e -Headers $headers
    Write-Host "  PASS - Entry ID: $($r.entry_id)" -ForegroundColor Green
    $textId = $r.entry_id
    $passed++
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
    $textId = $null
}

# Test 3: Image Entry
Write-Host "[3/6] Image Journal Entry..." -ForegroundColor Yellow
if (Test-Path "image.jpg") {
    try {
        $img = [System.IO.File]::ReadAllBytes("image.jpg")
        $b64 = [System.Convert]::ToBase64String($img)
        $uri = "data:image/jpeg;base64," + $b64
        
        $e = @{
            title = "Image Test"
            content = "Testing image"
            tags = @("test", "image")
            media = @(@{type="image"; url=$uri; caption="Test"})
        } | ConvertTo-Json -Depth 10
        
        $r = Invoke-RestMethod -Uri "$baseUrl/journal" -Method POST -Body $e -Headers $headers
        Write-Host "  PASS - Entry ID: $($r.entry_id)" -ForegroundColor Green
        $imgId = $r.entry_id
        $passed++
        
        Write-Host "  Waiting 15s for qwen2.5vl:7b..." -ForegroundColor Gray
        Start-Sleep -Seconds 15
        
        $logs = docker logs ai_life_companion_api --tail 20 2>&1 | Out-String
        if ($logs -match "Extracted content|ginger cat") {
            Write-Host "  PASS - Image processed" -ForegroundColor Green
            $passed++
        } else {
            Write-Host "  WARN - Processing unclear" -ForegroundColor Yellow
            $warnings++
        }
    } catch {
        Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
} else {
    Write-Host "  SKIP - image.jpg not found" -ForegroundColor Yellow
    $warnings++
}

# Test 4: Retrieval
Write-Host "[4/6] Retrieval Query (Gemini)..." -ForegroundColor Yellow
try {
    $q = @{
        query = "What did I write?"
        top_k = 5
        model = "gemini"
    } | ConvertTo-Json
    
    $r = Invoke-RestMethod -Uri "$baseUrl/retrieval" -Method POST -Body $q -Headers $headers
    if ($r.answer -notmatch "Query failed" -and $r.answer -notmatch "401") {
        Write-Host "  PASS" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  WARN - $($r.answer.Substring(0, [Math]::Min(50, $r.answer.Length)))" -ForegroundColor Yellow
        $warnings++
    }
} catch {
    Write-Host "  WARN: $($_.Exception.Message)" -ForegroundColor Yellow
    $warnings++
}

# Test 5: Reminder
Write-Host "[5/6] Reminder Creation..." -ForegroundColor Yellow
if ($textId) {
    try {
        $now = [DateTime]::UtcNow
        $time = $now.AddMinutes(10).ToString("yyyy-MM-ddTHH:mm:ss")
        
        $rem = @{
            entry_id = $textId
            email = "hovietanh147@gmail.com"
            subject = "Test"
            body = "Test reminder"
            cadence = "once"
            first_run_at = $time
        } | ConvertTo-Json
        
        $r = Invoke-RestMethod -Uri "$baseUrl/reminders" -Method POST -Body $rem -Headers $headers
        Write-Host "  PASS - Reminder ID: $($r.reminder_id)" -ForegroundColor Green
        $passed++
    } catch {
        Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
} else {
    Write-Host "  SKIP - No valid entry_id" -ForegroundColor Yellow
    $warnings++
}

# Test 6: Services
Write-Host "[6/6] Docker Services..." -ForegroundColor Yellow
$svc = @("api", "worker", "db", "redis", "minio", "qdrant")
$allRunning = $true
foreach ($s in $svc) {
    $st = docker ps --filter "name=ai_life_companion_$s" --format "{{.Names}}" 2>&1
    if (-not $st -or $st -match "Error") {
        $allRunning = $false
        break
    }
}
if ($allRunning) {
    Write-Host "  PASS - All services running" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  FAIL - Some services not running" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESULTS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Passed:   $passed" -ForegroundColor Green
Write-Host "Failed:   $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Gray" })
Write-Host "Warnings: $warnings" -ForegroundColor $(if ($warnings -gt 0) { "Yellow" } else { "Gray" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "All critical tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed. Check logs above." -ForegroundColor Red
}

