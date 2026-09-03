param(
    [string]$Mug500plusRoot = "E:\ResearchBackups\AdaPoinTr\MUG500plus"
)

$ErrorActionPreference = "Stop"
$raw = Join-Path $Mug500plusRoot "raw_v20"
$sourceLock = Join-Path $Mug500plusRoot "data_locks\mug500plus_d6_source125_acquisition_lock_v1"
$d3Lock = Join-Path $Mug500plusRoot "data_locks\mug500plus_m1_healthy125_v1"
$d4Lock = Join-Path $Mug500plusRoot "data_locks\mug500plus_d4_source100_qc_lock_v1"
$d5Lock = Join-Path $Mug500plusRoot "data_locks\mug500plus_d5_development100_qc_lock_v1"
$qcRoot = Join-Path $Mug500plusRoot "qc_d6_development100_v1"
$stlRoot = Join-Path $raw "clear_stl\d6_development100_v1"
$confirmation = Join-Path $raw "archives\d6_source125_v1\sealed\proposal_confirmation"
$out = Join-Path $Mug500plusRoot "data_locks\mug500plus_d6_development100_qc_lock_v1"

python tools/test_mamba_v16_d6_development100_qc_lock.py
if ($LASTEXITCODE -ne 0) { throw "D6 development100 final-lock tests failed" }

python -u tools/lock_mamba_v16_d6_development100_qc.py `
    --source_lock_dir $sourceLock `
    --d3_lock_dir $d3Lock `
    --d4_lock_dir $d4Lock `
    --d5_lock_dir $d5Lock `
    --qc_root $qcRoot `
    --stl_root $stlRoot `
    --confirmation_sealed_dir $confirmation `
    --protocol_json docs/mamba_v16_d6_development100_final_qc_lock_protocol_v1.json `
    --out_dir $out
if ($LASTEXITCODE -ne 0) { throw "D6 development100 final QC lock failed" }

Get-Content -LiteralPath (Join-Path $out "files.sha256") | ForEach-Object {
    if ($_ -notmatch '^([0-9a-f]{64})\s+(.+)$') {
        throw "Malformed frozen manifest line: $_"
    }
    $path = Join-Path $out $Matches[2]
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Matches[1]) { throw "Frozen output hash mismatch: $path" }
    Write-Host "$($Matches[2]): OK"
}

Write-Host "[done] D6 development100 final QC lock frozen"
Write-Host "[authorized-next] D6 data-generation protocol preparation only"
Write-Host "[locked] generation=false calibration=false training=false seed1=false confirmation=false"
