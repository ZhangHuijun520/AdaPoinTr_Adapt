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
        "data_locks\mug500plus_d6_source125_acquisition_lock_v1"
}

$Metadata = Join-Path $MugRoot "metadata_v20"
$D3 = Join-Path $MugRoot "data_locks\mug500plus_m1_healthy125_v1"
$D4 = Join-Path $MugRoot `
    "data_locks\mug500plus_d4_source100_acquisition_lock_v1"
$D5 = Join-Path $MugRoot `
    "data_locks\mug500plus_d5_source150_acquisition_lock_v1"

Write-Host "===== D6 source125 deterministic tests ====="
python tools/test_mamba_v16_d6_source125_acquisition.py
if ($LASTEXITCODE -ne 0) { throw "D6 source125 tests failed" }

Write-Host "===== Freeze metadata-only D6 source125 lock ====="
python tools/lock_mamba_v16_d6_source125_acquisition.py `
    --article_json (Join-Path $Metadata "mug500plus_article_v20.json") `
    --files_json (Join-Path $Metadata "mug500plus_files_v20.json") `
    --d3_lock_dir $D3 `
    --d4_lock_dir $D4 `
    --d5_lock_dir $D5 `
    --out_dir $OutDir
if ($LASTEXITCODE -ne 0) { throw "D6 source125 lock failed" }

Write-Host "===== Verify immutable lock ====="
Push-Location $OutDir
try {
    $manifest = Get-Content -LiteralPath "files.sha256"
    foreach ($line in $manifest) {
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

$receipt = Get-Content -LiteralPath `
    (Join-Path $OutDir "source_acquisition_lock_receipt.json") -Raw |
    ConvertFrom-Json

if ($receipt.status -ne `
    "source125_terminal_two_partition_acquisition_locked") {
    throw "Unexpected D6 source125 lock status"
}
if ($receipt.counts.remaining_sources -ne 125 -or
    $receipt.counts.development_sources -ne 100 -or
    $receipt.counts.proposal_confirmation_sources -ne 25) {
    throw "Unexpected D6 source counts"
}
if ($receipt.development_extraction_authorized -ne $false -or
    $receipt.proposal_confirmation_extraction_authorized -ne $false -or
    $receipt.D6_training_authorized -ne $false) {
    throw "D6 access boundary changed"
}

Write-Host "[done] exact D6 source125 metadata-only lock frozen"
Write-Host "[authorized] archive download/checksum only"
Write-Host "[locked] extraction=false generation=false training=false confirmation=false"
Write-Host "[next] freeze assignment-consistent R0/R1 mechanism protocol"

