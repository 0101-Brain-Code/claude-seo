# Claude SEO - Brain & Code audit extension installer (Windows).
#
# Adds the Chrome-assisted data tier to the seo-audit skill's Phase 0.
# Read-only by design, and no API keys.
$ErrorActionPreference = "Stop"

$SkillDir = Join-Path $HOME ".claude\skills"

Write-Host "========================================"
Write-Host "|   Claude SEO - Brain & Code audit    |"
Write-Host "========================================"

if (-not (Test-Path (Join-Path $SkillDir "seo"))) {
    Write-Host "X claude-seo base not installed."; exit 1
}
if (-not (Test-Path (Join-Path $SkillDir "seo-audit"))) {
    Write-Host "X seo-audit skill not installed."; exit 1
}

$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RefDir = Join-Path $SkillDir "seo-audit\references"
New-Item -ItemType Directory -Force -Path $RefDir | Out-Null

Copy-Item (Join-Path $SourceDir "skills\seo-audit\references\chrome-assisted-data.md") `
          (Join-Path $RefDir "chrome-assisted-data.md") -Force
Write-Host "OK Installed reference: $RefDir\chrome-assisted-data.md"

Write-Host ""
Write-Host "Phase 0 option (b) is now available in full audits."
Write-Host "Setup notes: docs\BRAINANDCODE-AUDIT-SETUP.md"
