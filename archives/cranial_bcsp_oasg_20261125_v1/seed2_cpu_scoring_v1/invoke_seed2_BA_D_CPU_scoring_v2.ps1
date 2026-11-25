$ErrorActionPreference = 'Stop'
$request = Join-Path $PSScriptRoot 'OASG_seed2_BA_D_CPU_scoring_execution_request_v1.json'
$requestSha = '5e6e26b23737d903e08413681971ae5cc7d3ac47132312ac7e12504e02df347c'
$authorizationSha = 'ba2b06e75de99c426e7d29e2594fa4e6a14436fd24638b993f4bd501ef8bc42b'

function Assert-FrozenFile($Path, $Sha, $Size = $null) {
    $item = Get-Item -LiteralPath $Path
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        ($null -ne $Size -and $item.Length -ne $Size) -or
        (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Sha) {
        throw "Frozen file mismatch: $Path"
    }
}

Assert-FrozenFile $request $requestSha
$scope = Get-Content -LiteralPath $request -Raw | ConvertFrom-Json
if ($scope.request_path -cne $request -or
    $scope.schema -cne 'bcsp-oasg-seed2-ba-d-cpu-score-v1' -or
    $scope.status -cne 'AWAITING_EXPLICIT_USER_AUTHORIZATION' -or
    $scope.execution_authorized -ne $false -or $scope.counts.model_rows -ne 210 -or
    $scope.execution_attempts -ne 1 -or $scope.automatic_retry -or $scope.formal_gate_executed_here -or
    $scope.external_wall_timeout_seconds -ne 18000 -or (Test-Path -LiteralPath $scope.output)) {
    throw 'Unexpected scoring scope or existing output'
}
Assert-FrozenFile $scope.authorization_path $authorizationSha
$authorization = Get-Content -LiteralPath $scope.authorization_path -Raw | ConvertFrom-Json
if ($authorization.schema -cne ($scope.schema + '-authorization') -or
    $authorization.request_sha256 -cne $requestSha -or
    $authorization.explicit_user_authorization -ne $true) {
    throw 'Authorization does not bind the frozen request'
}
foreach ($binding in @($scope.environment.python, $scope.implementation.entry, $scope.archive,
                       $scope.sidecars.bytes, $scope.sidecars.sha256, $scope.sidecars.members,
                       $scope.P3, $scope.prediction_freeze, $scope.local_download_verification)) {
    Assert-FrozenFile $binding.path $binding.sha256 $binding.bytes
}
$python = [string]$scope.environment.python.path
$wrapper = 'import subprocess, sys; sys.exit(subprocess.run([sys.executable, "-B", *sys.argv[1:]], timeout=18000).returncode)'
$pythonArgs = @('-B', '-c', $wrapper, $scope.implementation.entry.path,
                '--request', $request, '--request-sha256', $requestSha,
                '--authorization', $scope.authorization_path, '--authorization-sha256', $authorizationSha)
& $python @pythonArgs
$rc = $LASTEXITCODE
Write-Output "SCORING_EXIT $rc"
exit $rc
