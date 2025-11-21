# Test Multimodal Processing with Image
$baseUrl = "http://localhost:8000"
$apiKey = "local-dev-key-1"
$headers = @{"x-api-key" = $apiKey; "Content-Type" = "application/json"}

Write-Host "=== Testing Multimodal Processing ===" -ForegroundColor Cyan
Write-Host ""

# Check if image.jpg exists
$imagePath = "image.jpg"
if (-not (Test-Path $imagePath)) {
    Write-Host "ERROR: image.jpg not found in current directory" -ForegroundColor Red
    Write-Host "Please place image.jpg (cat image) in: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found image.jpg, converting to base64..." -ForegroundColor Green

# Convert image to base64
$imageBytes = [System.IO.File]::ReadAllBytes($imagePath)
$imageBase64 = [System.Convert]::ToBase64String($imageBytes)
$mimeType = "image/jpeg"
$dataUri = "data:$mimeType;base64,$imageBase64"

Write-Host "Image converted (size: $($imageBytes.Length) bytes)" -ForegroundColor Gray
Write-Host ""

# Create journal entry with image
Write-Host "=== Creating Journal Entry with Cat Image ===" -ForegroundColor Cyan

$entry = @{
    title = "My Cat Photo"
    content = "I took a photo of my cat today"
    mood = "happy"
    tags = @("cat", "pet", "photo")
    media = @(
        @{
            type = "image"
            url = $dataUri
            caption = "My cute cat"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/journal" -Method POST -Body $entry -Headers $headers
    Write-Host "✓ Journal Entry Created!" -ForegroundColor Green
    Write-Host "  Entry ID: $($response.entry_id)" -ForegroundColor Gray
    Write-Host "  Created at: $($response.created_at)" -ForegroundColor Gray
    Write-Host ""
    
    $entryId = $response.entry_id
    
    # Wait a bit for processing
    Write-Host "Waiting 5 seconds for image processing..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Test retrieval - ask about the cat
    Write-Host "=== Testing Retrieval - Asking about the cat ===" -ForegroundColor Cyan
    
    $query = @{
        query = "What animal is in my photo? Describe what you see in my images."
        top_k = 5
        model = "gemini"
    } | ConvertTo-Json
    
    $retrievalResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/retrieval" -Method POST -Body $query -Headers $headers
    Write-Host "✓ Retrieval Response:" -ForegroundColor Green
    Write-Host ""
    Write-Host "Answer:" -ForegroundColor Cyan
    Write-Host $retrievalResponse.answer -ForegroundColor White
    Write-Host ""
    Write-Host "References:" -ForegroundColor Cyan
    $retrievalResponse.references | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    Write-Host ""
    
    # Check if answer mentions cat
    $answerLower = $retrievalResponse.answer.ToLower()
    if ($answerLower -match "cat|kitten|feline|meow") {
        Write-Host "✓ SUCCESS: Model correctly identified the cat!" -ForegroundColor Green
    } else {
        Write-Host "⚠ WARNING: Model response doesn't clearly mention cat" -ForegroundColor Yellow
        Write-Host "  This might be normal if the image wasn't fully processed yet" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Checking Docker Logs ===" -ForegroundColor Cyan
Write-Host "Checking API logs for image processing..." -ForegroundColor Gray
docker logs ai_life_companion_api --tail 20

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan

