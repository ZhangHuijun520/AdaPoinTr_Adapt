param(
    [ValidateSet(1, 2, 3)]
    [int]$BatchId = 1,
    [string]$Mug500plusRoot = "E:\ResearchBackups\AdaPoinTr\MUG500plus"
)

$ErrorActionPreference = "Stop"
$batch = "{0:D3}" -f $BatchId
$lock = Join-Path $Mug500plusRoot "data_locks\mug500plus_d5_source150_acquisition_lock_v1"
$raw = Join-Path $Mug500plusRoot "raw_v20"
$archiveDir = Join-Path $raw "archives\d5_source150_v1\development\batch_$batch"
$stlOut = Join-Path $raw "clear_stl\d5_source150_v1\development\batch_$batch"
$qcOut = Join-Path $Mug500plusRoot "qc_d5_source150_v1\development\batch_$batch"
$proposal = Join-Path $raw "archives\d5_source150_v1\sealed\proposal_confirmation"
$completion = Join-Path $raw "archives\d5_source150_v1\sealed\completion_holdout"

python tools/test_mamba_v15_d5_development_batch_qc.py
if ($LASTEXITCODE -ne 0) { throw "D5 batch-QC contract tests failed" }

python -u tools/qc_mamba_v15_d5_development_batch.py `
    --source_lock_dir $lock `
    --batch_id $BatchId `
    --archive_dir $archiveDir `
    --stl_out_dir $stlOut `
    --qc_out_dir $qcOut `
    --proposal_sealed_dir $proposal `
    --completion_sealed_dir $completion
if ($LASTEXITCODE -ne 0) { throw "D5 development batch QC failed" }

Get-Content -LiteralPath (Join-Path $qcOut "files.sha256") | ForEach-Object {
    if ($_ -match '^([0-9a-f]{64})\s+(.+)$') {
        $path = Join-Path $qcOut $Matches[2]
        $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $Matches[1]) { throw "Frozen output hash mismatch: $path" }
        Write-Host "$($Matches[2]): OK"
    }
}

Write-Host "[done] D5 development batch $batch extraction and QC frozen"
Write-Host "[locked] sealed partitions remain empty; no model or generation access"
