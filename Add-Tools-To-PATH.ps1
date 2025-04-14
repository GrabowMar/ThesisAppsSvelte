# Script to locate and add Semgrep, Trufflehog, and Lighthouse to PATH
# This version uses user-level PATH modifications (no admin required)

function Test-CommandExists {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Command
    )
    
    $exists = $null -ne (Get-Command -Name $Command -ErrorAction SilentlyContinue)
    return $exists
}

function Find-ExecutablePath {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Command
    )
    
    try {
        $commandPath = (Get-Command $Command -ErrorAction SilentlyContinue).Source
        return $commandPath
    }
    catch {
        return $null
    }
}

function Find-PythonExecutablePath {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    # Check common Python script locations
    $possibleLocations = @(
        # Global pip installations
        "C:\Python*\Scripts\$Command.exe",
        # User pip installations
        "$env:LOCALAPPDATA\Programs\Python\Python*\Scripts\$Command.exe",
        # Virtual environments
        ".\.venv\Scripts\$Command.exe",
        ".\venv\Scripts\$Command.exe",
        ".\.env\Scripts\$Command.exe",
        "$env:USERPROFILE\.venv\Scripts\$Command.exe"
    )
    
    foreach ($location in $possibleLocations) {
        $paths = Resolve-Path -Path $location -ErrorAction SilentlyContinue
        if ($paths) {
            # Return the most recent version if multiple are found
            return $paths[-1].Path
        }
    }
    
    return $null
}

function Add-ToUserPath {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Directory
    )
    
    # Check if directory exists
    if (-not (Test-Path -Path $Directory)) {
        Write-Warning "Directory does not exist: $Directory"
        return $false
    }
    
    # Check if directory is already in PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentPath -split ";" -contains $Directory) {
        Write-Host "Directory already in user PATH: $Directory" -ForegroundColor Green
        return $true
    }
    
    try {
        # Add to user PATH (doesn't require admin privileges)
        $newPath = $currentPath + ";" + $Directory
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        Write-Host "Added to user PATH: $Directory" -ForegroundColor Green
        # Update current session PATH
        $env:Path = $env:Path + ";" + $Directory
        return $true
    }
    catch {
        Write-Error "Failed to add to PATH: $Directory. Error: $_"
        return $false
    }
}

# Setup section
Write-Host "Starting tools PATH configuration..." -ForegroundColor Cyan

# 1. Configure Lighthouse
$lighthouseExists = Test-CommandExists -Command "lighthouse"
if ($lighthouseExists) {
    Write-Host "Lighthouse is installed" -ForegroundColor Green
    $lighthousePath = Find-ExecutablePath -Command "lighthouse"
    if ($lighthousePath) {
        $lighthouseDir = Split-Path -Parent $lighthousePath
        Add-ToUserPath -Directory $lighthouseDir
    } else {
        Write-Host "Could not determine Lighthouse directory" -ForegroundColor Yellow
        # Try to get npm global directory
        $npmGlobalDir = npm root -g
        if ($npmGlobalDir) {
            $npmBinDir = Join-Path (Split-Path -Parent $npmGlobalDir) ".bin"
            if (Test-Path $npmBinDir) {
                Add-ToUserPath -Directory $npmBinDir
            }
        }
    }
} else {
    Write-Host "Lighthouse is not installed. Installing..." -ForegroundColor Yellow
    npm install -g lighthouse
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Lighthouse installed successfully" -ForegroundColor Green
        # Get npm global bin directory
        $npmGlobalDir = npm root -g
        if ($npmGlobalDir) {
            $npmBinDir = Join-Path (Split-Path -Parent $npmGlobalDir) ".bin"
            if (Test-Path $npmBinDir) {
                Add-ToUserPath -Directory $npmBinDir
            }
        }
    } else {
        Write-Error "Failed to install Lighthouse"
    }
}

# 2. Configure Semgrep
$semgrepExists = Test-CommandExists -Command "semgrep"
if ($semgrepExists) {
    Write-Host "Semgrep is installed" -ForegroundColor Green
    $semgrepPath = Find-ExecutablePath -Command "semgrep"
    if (-not $semgrepPath) {
        $semgrepPath = Find-PythonExecutablePath -Command "semgrep"
    }
    
    if ($semgrepPath) {
        $semgrepDir = Split-Path -Parent $semgrepPath
        Add-ToUserPath -Directory $semgrepDir
    } else {
        Write-Host "Could not determine Semgrep directory. Please run this command to find it:" -ForegroundColor Yellow
        Write-Host "    where.exe semgrep" -ForegroundColor Yellow
    }
} else {
    Write-Host "Semgrep is not installed. Installing..." -ForegroundColor Yellow
    pip install semgrep
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Semgrep installed successfully" -ForegroundColor Green
        # Try to find Python Scripts directory
        $pythonScriptsPath = (& python -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))")
        if ($pythonScriptsPath -and (Test-Path $pythonScriptsPath)) {
            Add-ToUserPath -Directory $pythonScriptsPath
        }
    } else {
        Write-Error "Failed to install Semgrep"
    }
}

# 3. Configure Trufflehog
$trufflehogExists = Test-CommandExists -Command "trufflehog"
if ($trufflehogExists) {
    Write-Host "Trufflehog is installed" -ForegroundColor Green
    $trufflehogPath = Find-ExecutablePath -Command "trufflehog"
    if (-not $trufflehogPath) {
        $trufflehogPath = Find-PythonExecutablePath -Command "trufflehog"
    }
    
    if ($trufflehogPath) {
        $trufflehogDir = Split-Path -Parent $trufflehogPath
        Add-ToUserPath -Directory $trufflehogDir
    } else {
        Write-Host "Could not determine Trufflehog directory. Please run this command to find it:" -ForegroundColor Yellow
        Write-Host "    where.exe trufflehog" -ForegroundColor Yellow
    }
} else {
    Write-Host "Trufflehog is not installed. Installing..." -ForegroundColor Yellow
    pip install trufflehog
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Trufflehog installed successfully" -ForegroundColor Green
        # Try to find Python Scripts directory
        $pythonScriptsPath = (& python -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))")
        if ($pythonScriptsPath -and (Test-Path $pythonScriptsPath)) {
            Add-ToUserPath -Directory $pythonScriptsPath
        }
    } else {
        Write-Error "Failed to install Trufflehog"
    }
}

# Manual path addition option for venv
$venvScriptsPath = Join-Path (Get-Location) ".venv\Scripts"
if (Test-Path $venvScriptsPath) {
    Write-Host "Found virtual environment Scripts directory" -ForegroundColor Cyan
    $addVenvToPath = Read-Host "Add virtual environment Scripts to PATH? (y/n)"
    if ($addVenvToPath -eq "y") {
        Add-ToUserPath -Directory $venvScriptsPath
    }
}

Write-Host "`nPATH configuration completed!" -ForegroundColor Cyan
Write-Host "You may need to restart your terminal for some changes to take effect." -ForegroundColor Yellow

# Verify installation
Write-Host "`nVerifying installations:" -ForegroundColor Cyan
$tools = @("lighthouse", "semgrep", "trufflehog")

foreach ($tool in $tools) {
    if (Test-CommandExists -Command $tool) {
        Write-Host "$tool is now available in PATH" -ForegroundColor Green
    }
    else {
        Write-Host "$tool is not available in PATH" -ForegroundColor Red
        Write-Host "If you just installed it, try opening a new terminal window and run: $tool --version" -ForegroundColor Yellow
    }
}

# Provide manual instructions if tools still missing
Write-Host "`nIf tools are still not accessible after restarting your terminal, you can manually find their locations with:"
Write-Host "    pip show semgrep | Select-String 'Location'" -ForegroundColor Yellow
Write-Host "    pip show trufflehog | Select-String 'Location'" -ForegroundColor Yellow

# Virtual environment option
Write-Host "`nFor tools in your virtual environment, you may need to use them with the venv activated:"
Write-Host "    .\.venv\Scripts\activate" -ForegroundColor Yellow
Write-Host "    semgrep --help" -ForegroundColor Yellow