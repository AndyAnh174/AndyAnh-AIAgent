# Test script for AI Life Companion API
$baseUrl = "http://localhost:8000"
$apiKey = "local-dev-key-1"
$headers = @{"x-api-key" = $apiKey; "Content-Type" = "application/json"}

Write-Host "=== AI Life Companion API Test ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "1. Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "   ✓ Health check passed: $($health.message)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Health check failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Create Journal Entries
Write-Host "2. Creating Journal Entries..." -ForegroundColor Yellow

$entries = @(
    @{
        title = "Buổi sáng tuyệt vời"
        content = "Hôm nay thức dậy sớm, tập thể dục và có bữa sáng ngon lành. Cảm thấy tràn đầy năng lượng cho ngày mới!"
        mood = "happy"
        tags = @("morning", "exercise", "breakfast")
        media = @()
    },
    @{
        title = "Meeting quan trọng"
        content = "Cuộc họp với team về dự án mới. Đã thảo luận về roadmap và phân công công việc. Mọi người đều hào hứng!"
        mood = "excited"
        tags = @("work", "meeting", "team")
        media = @()
    },
    @{
        title = "Đi chơi với bạn"
        content = "Đi xem phim và ăn tối với bạn thân. Trò chuyện về cuộc sống và những dự định tương lai. Thời gian trôi qua thật nhanh!"
        mood = "happy"
        tags = @("friends", "entertainment", "social")
        media = @()
    },
    @{
        title = "Học Machine Learning"
        content = "Dành cả buổi chiều để học về GraphRAG và LangGraph. Đã hiểu thêm về cách xây dựng knowledge graph và retrieval system."
        mood = "focused"
        tags = @("learning", "ai", "technology")
        media = @()
    },
    @{
        title = "Kỷ niệm đặc biệt"
        content = "Hôm nay là kỷ niệm 1 năm làm việc tại công ty. Nhìn lại chặng đường đã qua, cảm thấy tự hào về những gì đã đạt được."
        mood = "grateful"
        tags = @("milestone", "work", "reflection")
        media = @()
    }
)

$createdEntries = @()
foreach ($entry in $entries) {
    try {
        $body = $entry | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$baseUrl/journal" -Method POST -Body $body -Headers $headers
        $createdEntries += $response
        Write-Host "   ✓ Created entry: $($entry.title) (ID: $($response.entry_id))" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Failed to create entry '$($entry.title)': $_" -ForegroundColor Red
    }
}
Write-Host "   Total entries created: $($createdEntries.Count)" -ForegroundColor Cyan
Write-Host ""

# Test 3: Create Reminders
Write-Host "3. Creating Reminders..." -ForegroundColor Yellow

if ($createdEntries.Count -gt 0) {
    $firstEntry = $createdEntries[0]
    $reminderTime = (Get-Date).AddMinutes(2).ToString("yyyy-MM-ddTHH:mm:ss")
    
    $reminders = @(
        @{
            entry_id = $firstEntry.entry_id
            email = "hovietanh147@gmail.com"
            subject = "Reminder: Review memories"
            body = "This is a reminder about entry: $($firstEntry.title). Take time to reflect on these memories!"
            cadence = "daily"
            first_run_at = $reminderTime
        },
        @{
            entry_id = $firstEntry.entry_id
            email = "hovietanh147@gmail.com"
            subject = "Weekly reminder"
            body = "Weekly reminder about your entry. Review and update your journal!"
            cadence = "weekly"
            first_run_at = (Get-Date).AddDays(7).ToString("yyyy-MM-ddTHH:mm:ss")
        }
    )
    
    foreach ($reminder in $reminders) {
        try {
            $body = $reminder | ConvertTo-Json
            $response = Invoke-RestMethod -Uri "$baseUrl/reminders" -Method POST -Body $body -Headers $headers
            Write-Host "   ✓ Created reminder: $($reminder.subject) (ID: $($response.reminder_id))" -ForegroundColor Green
            Write-Host "     Will run at: $($reminder.first_run_at)" -ForegroundColor Gray
        } catch {
            Write-Host "   ✗ Failed to create reminder: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   ⚠ No entries created, skipping reminder creation" -ForegroundColor Yellow
}
Write-Host ""

# Test 4: Test Retrieval
Write-Host "4. Testing Retrieval Endpoint..." -ForegroundColor Yellow
$queries = @(
    "What did I do today?",
    "Tell me about my work activities",
    "What made me happy?",
    "What did I learn?"
)

foreach ($query in $queries) {
    try {
        $body = @{query = $query; top_k = 3} | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$baseUrl/retrieval" -Method POST -Body $body -Headers $headers
        Write-Host "   Query: $query" -ForegroundColor Cyan
        Write-Host "   Answer: $($response.answer)" -ForegroundColor White
        Write-Host ""
    } catch {
        Write-Host "   ✗ Query failed: $_" -ForegroundColor Red
    }
}

# Test 5: Check Worker Logs
Write-Host "5. Checking Worker Status..." -ForegroundColor Yellow
Write-Host "   Checking if worker is processing reminders..." -ForegroundColor Gray
docker logs ai_life_companion_worker --tail 10

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host "Check docker logs for detailed information:" -ForegroundColor Yellow
Write-Host "  docker logs ai_life_companion_api --tail 50" -ForegroundColor Gray
Write-Host "  docker logs ai_life_companion_worker --tail 50" -ForegroundColor Gray

