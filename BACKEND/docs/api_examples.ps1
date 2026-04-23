# PowerShell API examples for Django POS backend

$baseUrl = "http://127.0.0.1:8000/api/v1"

# 1) Login and get tokens
$tokenResponse = Invoke-RestMethod -Method Post -Uri "$baseUrl/auth/token/" -ContentType "application/json" -Body (@{
    username = "admin"
    password = "Admin@12345"
} | ConvertTo-Json)

$accessToken = $tokenResponse.access
$refreshToken = $tokenResponse.refresh

Write-Host "Access token acquired."

$headers = @{
    Authorization = "Bearer $accessToken"
}

# 2) Product category search and ordering
Invoke-RestMethod -Method Get -Uri "$baseUrl/products/categories/?search=snack" -Headers $headers
Invoke-RestMethod -Method Get -Uri "$baseUrl/products/categories/?ordering=name" -Headers $headers

# 3) Checkout example
$checkoutBody = @{
    items = @(
        @{ product_id = 1; quantity = 2 }
    )
    payment_method = "CASH"
    discount_amount = "0.00"
    tax_amount = "0.00"
    notes = "API docs example checkout"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri "$baseUrl/sales/checkout/" -Headers $headers -ContentType "application/json" -Body $checkoutBody

# 4) Reporting examples
Invoke-RestMethod -Method Get -Uri "$baseUrl/reports/sales/daily/" -Headers $headers
Invoke-RestMethod -Method Get -Uri "$baseUrl/reports/sales/weekly/?weeks=8" -Headers $headers
Invoke-RestMethod -Method Get -Uri "$baseUrl/reports/products/performance/?limit=10" -Headers $headers
Invoke-RestMethod -Method Get -Uri "$baseUrl/reports/inventory/summary/" -Headers $headers

# 5) Refresh access token when expired
$refreshBody = @{ refresh = $refreshToken } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$baseUrl/auth/token/refresh/" -ContentType "application/json" -Body $refreshBody
