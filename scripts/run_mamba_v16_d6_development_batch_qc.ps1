param(
    [ValidateSet(1, 2, 3)]
    [int]$BatchId = 1,
    [string]$Mug500plusRoot = "E:\ResearchBackups\AdaPoinTr\MUG500plus"
)

$ErrorActionPreference = "Stop"
$batch = "{0:D3}" -f $BatchId
$lock = Join-Path $Mug500plusRoot "data_locks\mug500plus_d6_source125_acquisition_lock_v1"
$raw = Join-Path $Mug500plusRoot "raw_v20"
$archiveDir = Join-Path $raw "archives\d6_development100_v1\batch_$batch"
$stlOut = Join-Path $raw "clear_stl\d6_development100_v1\batch_$batch"
$qcOut = Join-Path $Mug500plusRoot "qc_d6_development100_v1\batch_$batch"
$confirmation = Join-Path $raw "archives\d6_source125_v1\sealed\proposal_confirmation"
$zeroStepReport = Join-Path $PSScriptRoot "..\docs\mamba_v16_d6a_slot32_implementation_zero_step_complete_result_zh.md"

New-Item -ItemType Directory -Force -Path $confirmation | Out-Null

python tools/test_mamba_v16_d6_development_batch_qc.py
if ($LASTEXITCODE -ne 0) { throw "D6 batch-QC contract tests failed" }

python -u tools/qc_mamba_v16_d6_development_batch.py `
    --source_lock_dir $lock `
    --zero_step_report $zeroStepReport `
    --batch_id $BatchId `
    --archive_dir $archiveDir `
    --stl_out_dir $stlOut `
    --qc_out_dir $qcOut `
    --confirmation_sealed_dir $confirmation
if ($LASTEXITCODE -ne 0) { throw "D6 development batch QC failed" }

Get-Content -LiteralPath (Join-Path $qcOut "files.sha256") | ForEach-Object {
    if ($_ -match '^([0-9a-f]{64})\s+(.+)$') {
        $path = Join-Path $qcOut $Matches[2]
        $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $Matches[1]) { throw "Frozen output hash mismatch: $path" }
        Write-Host "$($Matches[2]): OK"
    }
}

Write-Host "[done] D6 development batch $batch extraction and QC frozen"
Write-Host "[locked] confirmation25 remains empty; no model or generation access"
