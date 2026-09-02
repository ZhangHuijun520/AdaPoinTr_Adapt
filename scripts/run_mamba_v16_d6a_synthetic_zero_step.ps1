[CmdletBinding()]
param(
    [string]$MugRoot = "E:\ResearchBackups\AdaPoinTr\MUG500plus",
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not $OutDir) {
    $OutDir = Join-Path $RepoRoot `
        "logs\mamba_v16_d6_contact_support\d6a_synthetic_zero_step_v1"
}
$MechanismLock = Join-Path $MugRoot `
    "data_locks\mug500plus_d6a_slot32_mechanism_protocol_lock_v1"

Write-Host "===== D6-A implementation tests ====="
python tools/test_mamba_v16_d6a_slot_allocator.py
if ($LASTEXITCODE -ne 0) { throw "D6-A implementation tests failed" }

Write-Host "===== D6-A artificial CUDA zero-step ====="
python tools/preflight_mamba_v16_d6a_synthetic_zero_step.py `
    --mechanism_lock_dir $MechanismLock `
    --out_dir $OutDir
if ($LASTEXITCODE -ne 0) { throw "D6-A synthetic zero-step failed" }

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
    (Join-Path $OutDir "zero_step_preflight_receipt.json") -Raw |
    ConvertFrom-Json
if ($Receipt.status -ne "D6A_R0_R1_artificial_CUDA_zero_step_passed" -or
    $Receipt.optimizer_steps -ne 0 -or
    $Receipt.model_updates -ne 0 -or
    $Receipt.D6_cases_accessed -ne 0 -or
    $Receipt.training_authorized -ne $false) {
    throw "D6-A zero-step frozen semantics changed"
}

Write-Host "[done] D6-A artificial CUDA zero-step passed"
Write-Host "[locked] D6=0 generation=false calibration=false training=false sealed=false"
