[CmdletBinding()]
param(
    [string]$MugRoot = "E:\ResearchBackups\AdaPoinTr\MUG500plus",
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not $OutDir) {
    $OutDir = Join-Path $MugRoot `
        "data_locks\mug500plus_d6a_slot32_mechanism_protocol_lock_v1"
}

$SourceLock = Join-Path $MugRoot `
    "data_locks\mug500plus_d6_source125_acquisition_lock_v1"

Write-Host "===== D6-A mechanism protocol tests ====="
python tools/test_mamba_v16_d6a_slot32_mechanism_protocol.py
if ($LASTEXITCODE -ne 0) { throw "D6-A mechanism tests failed" }

Write-Host "===== Freeze D6-A mechanism lock ====="
python tools/lock_mamba_v16_d6a_slot32_mechanism_protocol.py `
    --source_lock_dir $SourceLock `
    --out_dir $OutDir
if ($LASTEXITCODE -ne 0) { throw "D6-A mechanism lock failed" }

Write-Host "===== Verify immutable lock ====="
Push-Location $OutDir
try {
    foreach ($line in Get-Content -LiteralPath "files.sha256") {
        if (-not $line.Trim()) { continue }
        $expected, $name = $line -split '\s+', 2
        $name = $name.TrimStart('*')
        $actual = (Get-FileHash -LiteralPath $name -Algorithm SHA256).Hash
        if ($actual.ToLowerInvariant() -ne $expected.ToLowerInvariant()) {
            throw "SHA256 mismatch: $name"
        }
        Write-Host "$name`: OK"
    }
}
finally {
    Pop-Location
}

$Receipt = Get-Content -LiteralPath `
    (Join-Path $OutDir "mechanism_lock_receipt.json") -Raw |
    ConvertFrom-Json

if ($Receipt.status -ne `
    "D6A_slot32_mechanism_frozen_implementation_not_started") {
    throw "Unexpected D6-A mechanism lock status"
}
if ($Receipt.slots -ne 32 -or $Receipt.candidate_points -ne 8192) {
    throw "D6-A proposal budget drifted"
}
if ($Receipt.training_authorized -ne $false -or
    $Receipt.D6_generation_authorized -ne $false -or
    $Receipt.proposal_confirmation_authorized -ne $false) {
    throw "D6-A permission boundary changed"
}

Write-Host "[done] D6-A slot32 mechanism protocol frozen"
Write-Host "[authorized-next] implementation, toy tests, then artificial zero-step only"
Write-Host "[locked] extraction=false generation=false calibration=false training=false sealed=false"
