# PowerShell script to create GitHub repository

Write-Host "🚀 Creating GitHub repository 'Driftly-Prompt-Veo3' for user 'apedonkey'" -ForegroundColor Green
Write-Host ""
Write-Host "You need a GitHub Personal Access Token to create a repository via API" -ForegroundColor Yellow
Write-Host "Get one from: https://github.com/settings/tokens/new" -ForegroundColor Cyan
Write-Host "Required scopes: repo" -ForegroundColor Cyan
Write-Host ""

$token = Read-Host -Prompt "Enter your GitHub Personal Access Token" -AsSecureString
$tokenText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($token))

Write-Host ""
Write-Host "Creating repository..." -ForegroundColor Yellow

$headers = @{
    "Authorization" = "token $tokenText"
    "Accept" = "application/vnd.github.v3+json"
}

$body = @{
    "name" = "Driftly-Prompt-Veo3"
    "description" = "AI-powered video automation studio using Grok 3 and Google Veo 3"
    "private" = $false
    "has_issues" = $true
    "has_projects" = $false
    "has_wiki" = $false
    "auto_init" = $false
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/user/repos" `
                                 -Method Post `
                                 -Headers $headers `
                                 -Body $body `
                                 -ContentType "application/json"
    
    Write-Host "✅ Repository created successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Add remote and push
    Write-Host "Adding remote origin..." -ForegroundColor Yellow
    git remote add origin https://github.com/apedonkey/Driftly-Prompt-Veo3.git
    
    Write-Host "Pushing code to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    Write-Host ""
    Write-Host "🎉 Success! Your repository is live at:" -ForegroundColor Green
    Write-Host "https://github.com/apedonkey/Driftly-Prompt-Veo3" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error creating repository:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "You can create it manually at: https://github.com/new" -ForegroundColor Yellow
}