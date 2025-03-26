$ErrorActionPreference = "Stop"

# Get the installation directory from the command line argument
$installDir = $args[0]
$questionsFile = Join-Path $installDir "test_questions.json"

try {
    # Download the latest questions from GitHub
    $url = "https://raw.githubusercontent.com/SailboatSteve/SMQT_Practice_Exam/main/test_questions.json"
    Write-Host "Downloading latest questions from GitHub..."
    
    # Create a web client with TLS 1.2 support
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($url, $questionsFile)
    
    Write-Host "Questions downloaded successfully to: $questionsFile"
    exit 0
} catch {
    Write-Host "Error downloading questions: $_"
    exit 1
}
