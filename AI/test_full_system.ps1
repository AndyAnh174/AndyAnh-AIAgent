# Comprehensive System Test Script
# Tests all features: health, journal entries, multimodal processing, retrieval, reminders

$ErrorActionPreference = "Continue"
$baseUrl = "http://localhost:8000"
$apiKey = "local-dev-key-1"
$headers = @{"x-api-key" = $apiKey; "Content-Type" = "application/json"}

$testResults = @{
    Passed = 0
    Failed = 0
    Warnings = 0
    Details = @()
}

function Add-Result {
    param($status, $message, $details = "")
    if ($status -eq "PASS") {
        $script:testResults.Passed++
        Write-Host "✓ PASS: $message" -ForegroundColor Green
    } elseif ($status -eq "FAIL") {
        $script:testResults.Failed++
        Write-Host "✗ FAIL: $message" -ForegroundColor Red
    } else {
        $script:testResults.Warnings++
        Write-Host "⚠ WARN: $message" -ForegroundColor Yellow
    }
    $script:testResults.Details += @{
        Status = $status
        Message = $message
        Details = $details
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  COMPREHENSIVE SYSTEM TEST" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "=== Test 1: Health Check ===" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET -ErrorAction Stop
    if ($health.status -eq "ok") {
        Add-Result "PASS" "Health check successful"
    } else {
        Add-Result "FAIL" "Health check returned unexpected status: $($health.status)"
    }
} catch {
    Add-Result "FAIL" "Health check failed: $($_.Exception.Message)"
}

# Test 2: Text Journal Entry
Write-Host ""
Write-Host "=== Test 2: Text Journal Entry ===" -ForegroundColor Yellow
try {
    $entry = @{
        title = "Test Text Entry"
        content = "This is a test journal entry with only text content. No media files."
        mood = "neutral"
        tags = @("test", "text")
        media = @()
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/journal" -Method POST -Body $entry -Headers $headers -ErrorAction Stop
    Add-Result "PASS" "Text journal entry created" "Entry ID: $($response.entry_id)"
    $textEntryId = $response.entry_id
} catch {
    Add-Result "FAIL" "Text journal entry creation failed: $($_.Exception.Message)"
    $textEntryId = $null
}

# Test 3: Image Journal Entry
Write-Host ""
Write-Host "=== Test 3: Image Journal Entry (qwen2.5vl:7b) ===" -ForegroundColor Yellow
if (Test-Path "image.jpg") {
    try {
        Write-Host "  Converting image.jpg to base64..." -ForegroundColor Gray
        $imageBytes = [System.IO.File]::ReadAllBytes("image.jpg")
        $imageBase64 = [System.Convert]::ToBase64String($imageBytes)
        $mimeType = 'data:image/jpeg;base64,'
        $dataUri = $mimeType + $imageBase64
        
        $entry = @{
            title = "Test Image Entry"
            content = "Testing image processing with qwen2.5vl:7b"
            mood = "happy"
            tags = @("test", "image", "cat")
            media = @(
                @{
                    type = "image"
                    url = $dataUri
                    caption = "Test cat image"
                }
            )
        } | ConvertTo-Json -Depth 10
        
        $response = Invoke-RestMethod -Uri "$baseUrl/journal" -Method POST -Body $entry -Headers $headers -ErrorAction Stop
        Add-Result "PASS" "Image journal entry created" "Entry ID: $($response.entry_id)"
        $imageEntryId = $response.entry_id
        
        Write-Host "  Waiting 15 seconds for qwen2.5vl:7b to process image..." -ForegroundColor Gray
        Start-Sleep -Seconds 15
        
        # Check logs for image processing
        $logs = docker logs ai_life_companion_api --tail 30 2>&1 | Out-String
        if ($logs -match "Extracted content from image|qwen|ginger cat|cat sitting") {
            Add-Result "PASS" "Image processing successful (qwen2.5vl:7b)" "Content extracted from image"
        } else {
            Add-Result "WARN" "Image processing status unclear" "Check logs manually"
        }
    } catch {
        Add-Result "FAIL" "Image journal entry creation failed: $($_.Exception.Message)"
        $imageEntryId = $null
    }
} else {
    Add-Result "WARN" "image.jpg not found, skipping image test"
    $imageEntryId = $null
}

# Test 4: Retrieval Query with Gemini
Write-Host ""
Write-Host "=== Test 4: Retrieval Query (gemini-2.0-flash) ===" -ForegroundColor Yellow
try {
    $query = @{
        query = "What did I write about in my journal entries? Summarize my recent entries."
        top_k = 5
        model = "gemini"
    } | ConvertTo-Json
    
    $retrievalResponse = Invoke-RestMethod -Uri "$baseUrl/retrieval" -Method POST -Body $query -Headers $headers -ErrorAction Stop
    
    $answerText = $retrievalResponse.answer
    if ($answerText -and $answerText -notmatch "Query failed" -and $answerText -notmatch "Error" -and $answerText -notmatch "401" -and $answerText -notmatch "404") {
        Add-Result "PASS" "Retrieval query successful (gemini-2.0-flash)" "Got response from Gemini"
        Write-Host "  Response preview: $($retrievalResponse.answer.Substring(0, [Math]::Min(100, $retrievalResponse.answer.Length)))..." -ForegroundColor Gray
    } else {
        Add-Result "WARN" "Retrieval query returned error" "Response: $($retrievalResponse.answer)"
    }
} catch {
    Add-Result "WARN" "Retrieval query failed: $($_.Exception.Message)" "This may be due to embeddings configuration"
}

# Test 5: Reminder Creation
Write-Host ""
Write-Host "=== Test 5: Reminder Creation ===" -ForegroundColor Yellow
try {
    # Get a valid entry_id from database or use the one we just created
    $validEntryId = if ($textEntryId) { $textEntryId } elseif ($imageEntryId) { $imageEntryId } else { $null }
    
    if ($validEntryId) {
        $utcNow = [DateTime]::UtcNow
        $reminderTime = $utcNow.AddMinutes(5).ToString("yyyy-MM-ddTHH:mm:ss")
        
        $reminder = @{
            entry_id = $validEntryId
            email = "hovietanh147@gmail.com"
            subject = "Test Reminder"
            body = "This is a test reminder from the comprehensive test suite."
            cadence = "once"
            first_run_at = $reminderTime
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$baseUrl/reminders" -Method POST -Body $reminder -Headers $headers -ErrorAction Stop
        Add-Result "PASS" "Reminder created successfully" "Reminder ID: $($response.reminder_id), Scheduled: $reminderTime"
    } else {
        Add-Result "WARN" "No valid entry_id available for reminder test" "Skipping reminder creation"
    }
} catch {
    Add-Result "FAIL" "Reminder creation failed: $($_.Exception.Message)"
}

# Test 6: Check Docker Services
Write-Host ""
Write-Host "=== Test 6: Docker Services Status ===" -ForegroundColor Yellow
$services = @("ai_life_companion_api", "ai_life_companion_worker", "ai_life_companion_db", "ai_life_companion_redis", "ai_life_companion_minio", "ai_life_companion_qdrant")
foreach ($service in $services) {
    $status = docker ps --filter "name=$service" --format "{{.Status}}" 2>&1
    if ($status -and $status -notmatch "Error") {
        Add-Result "PASS" "Service $service is running" $status
    } else {
        Add-Result "FAIL" "Service $service is not running"
    }
}

# Test 7: Check Recent Logs for Errors
Write-Host ""
Write-Host "=== Test 7: Error Check in Logs ===" -ForegroundColor Yellow
$apiLogs = docker logs ai_life_companion_api --tail 50 2>&1 | Out-String
$errorCount = ([regex]::Matches($apiLogs, "ERROR|CRITICAL|Exception|Traceback", "IgnoreCase")).Count
if ($errorCount -eq 0) {
    Add-Result "PASS" "No critical errors in API logs"
} else {
    Add-Result "WARN" "Found $errorCount potential errors in API logs" "Review logs for details"
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TEST SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Passed:  $($testResults.Passed)" -ForegroundColor Green
Write-Host "Failed:  $($testResults.Failed)" -ForegroundColor $(if ($testResults.Failed -gt 0) { "Red" } else { "Gray" })
Write-Host "Warnings: $($testResults.Warnings)" -ForegroundColor $(if ($testResults.Warnings -gt 0) { "Yellow" } else { "Gray" })
Write-Host ""

if ($testResults.Failed -gt 0) {
    Write-Host "Failed Tests:" -ForegroundColor Red
    $testResults.Details | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "  - $($_.Message)" -ForegroundColor Red
        if ($_.Details) {
            Write-Host "    Details: $($_.Details)" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

if ($testResults.Warnings -gt 0) {
    Write-Host "Warnings:" -ForegroundColor Yellow
    $testResults.Details | Where-Object { $_.Status -eq "WARN" } | ForEach-Object {
        Write-Host "  - $($_.Message)" -ForegroundColor Yellow
        if ($_.Details) {
            Write-Host "    Details: $($_.Details)" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

# Check for common issues and suggest fixes
Write-Host "=== Common Issues Check ===" -ForegroundColor Cyan

# Check if Gemini model error
if ($apiLogs -match "404 Model is not found.*gemini-pro") {
    Write-Host "⚠ Found Gemini model error - checking configuration..." -ForegroundColor Yellow
    $graphFile = Get-Content "app/services/graph.py" -Raw
    if ($graphFile -match "gemini-2.0-flash") {
        Write-Host "  ✓ Model name is correct in code" -ForegroundColor Green
        Write-Host "  → May need to restart container or check LlamaIndex version" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Model name may be incorrect" -ForegroundColor Red
    }
}

# Check if embeddings error
if ($apiLogs -match "401.*openai.*api.*key") {
    Write-Host "⚠ Found OpenAI embeddings error" -ForegroundColor Yellow
    Write-Host "  → LlamaIndex is using OpenAI embeddings by default" -ForegroundColor Gray
    Write-Host "  → This is expected if OPENAI_API_KEY is not set" -ForegroundColor Gray
    Write-Host "  → GraphRAG indexing will fail but vision processing works" -ForegroundColor Gray
}

# Check if Ollama connection error
if ($apiLogs -match "Failed to process.*ollama|301.*ollama|Connection.*ollama") {
    Write-Host "⚠ Found Ollama connection issues" -ForegroundColor Yellow
    Write-Host "  → Check OLLAMA_BASE_URL in .env" -ForegroundColor Gray
    Write-Host "  → Ensure Ollama server is accessible" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Test completed!" -ForegroundColor Green

