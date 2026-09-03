$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

if (-not $env:MUG500PLUS_D6_DEVELOPMENT100_QC_LOCK_DIR) {
    throw "Set MUG500PLUS_D6_DEVELOPMENT100_QC_LOCK_DIR"
}
if (-not $env:MUG500PLUS_D6_SOURCE125_ACQUISITION_LOCK_DIR) {
    throw "Set MUG500PLUS_D6_SOURCE125_ACQUISITION_LOCK_DIR"
}
if (-not $env:MUG500PLUS_D6_DEVELOPMENT_PROTOCOL_LOCK_DIR) {
    throw "Set MUG500PLUS_D6_DEVELOPMENT_PROTOCOL_LOCK_DIR"
}

$Locker = "tools/lock_mamba_v16_d6_mug500plus_development_fourfold_protocol.py"
$Generator = "tools/generate_mamba_v16_d6_mug500plus_development_cases.py"
$Test = "tools/test_mamba_v16_d6_mug500plus_development_fourfold_protocol.py"
$Protocol = "docs/mamba_v16_d6_mug500plus_development_generation_fourfold_protocol_v1.json"
$Engine = "tools/generate_mug500plus_m2_synthetic_defects.py"
$BaseProtocol = "docs/mamba_v13_d3_mug500plus_phase_m2_synthetic_defect_protocol_v1.json"
$ZeroStepReport = "docs/mamba_v16_d6a_slot32_implementation_zero_step_complete_result_zh.md"

python -m py_compile $Locker $Generator $Test
if ($LASTEXITCODE -ne 0) { throw "Python compile failed" }
python $Test
if ($LASTEXITCODE -ne 0) { throw "Boundary tests failed" }

$Arguments = @(
    $Locker,
    "--development100_qc_lock_dir", $env:MUG500PLUS_D6_DEVELOPMENT100_QC_LOCK_DIR,
    "--source125_acquisition_lock_dir", $env:MUG500PLUS_D6_SOURCE125_ACQUISITION_LOCK_DIR,
    "--protocol_json", $Protocol,
    "--generator_entry", $Generator,
    "--engine", $Engine,
    "--base_protocol", $BaseProtocol,
    "--zero_step_report", $ZeroStepReport,
    "--test_script", $Test,
    "--out_dir", $env:MUG500PLUS_D6_DEVELOPMENT_PROTOCOL_LOCK_DIR
)

python @Arguments
if ($LASTEXITCODE -ne 0) { throw "Protocol lock failed" }
python @Arguments
if ($LASTEXITCODE -ne 0) { throw "Idempotence check failed" }

$Lock = $env:MUG500PLUS_D6_DEVELOPMENT_PROTOCOL_LOCK_DIR
foreach ($line in Get-Content -LiteralPath (Join-Path $Lock "files.sha256")) {
    if ($line -notmatch '^([0-9a-f]{64})\s+\*?(.+)$') {
        throw "Malformed files.sha256 line: $line"
    }
    $Expected = $Matches[1]
    $Path = Join-Path $Lock $Matches[2]
    $Actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected) { throw "SHA256 mismatch: $Path" }
    Write-Host "$(Split-Path $Path -Leaf): OK"
}

Write-Host "[done] D6 development generation and source-fourfold protocol frozen"
Write-Host "[authorized-next] frozen development400 generation only"
Write-Host "[locked] generation_not_started=true calibration=false training=false seed1=false confirmation=false"
