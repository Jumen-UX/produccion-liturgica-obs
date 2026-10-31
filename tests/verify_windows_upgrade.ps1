<#
  Regression test for the per-user Windows installer.
  Runs on a disposable GitHub Actions Windows runner, never a user's PC.
  Both installers contain the same application build, with different versions;
  testing a genuinely older application still requires manual validation.
#>
param(
    [Parameter(Mandatory = $true)][string]$IsccPath,
    [Parameter(Mandatory = $true)][string]$CurrentInstaller,
    [Parameter(Mandatory = $true)][string]$CurrentVersion
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$installerPath = (Resolve-Path $CurrentInstaller).Path
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\ProduccionLiturgicaOBS'
$installedExe = Join-Path $installDir 'ProduccionLiturgicaOBS.exe'
$dataDir = Join-Path $env:LOCALAPPDATA 'ProduccionLiturgicaOBS'
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall'
$appName = 'Producción Litúrgica OBS'

function Get-AppEntries {
    @(Get-ChildItem -Path $uninstallKey -ErrorAction SilentlyContinue | ForEach-Object {
        Get-ItemProperty -LiteralPath $_.PSPath
    } | Where-Object {
        $_.PSObject.Properties['DisplayName'] -and $_.DisplayName -eq $appName
    })
}

function Assert-Installation([string]$expectedVersion) {
    if (-not (Test-Path -LiteralPath $installedExe)) {
        throw 'No está el ejecutable instalado.'
    }
    $entries = @(Get-AppEntries)
    if ($entries.Count -ne 1) {
        throw "Se esperó una sola entrada en aplicaciones instaladas; hay $($entries.Count)."
    }
    if ($entries[0].DisplayVersion -ne $expectedVersion) {
        throw "Versión instalada inesperada: $($entries[0].DisplayVersion)."
    }
    $locationProperty = $entries[0].PSObject.Properties['InstallLocation']
    if ($locationProperty -and $locationProperty.Value -and
        $locationProperty.Value.TrimEnd('\') -ne $installDir.TrimEnd('\')) {
        throw "La actualización cambió el directorio de instalación: $($entries[0].InstallLocation)."
    }
    return $entries[0]
}

if ((Get-AppEntries).Count -ne 0 -or (Test-Path -LiteralPath $installedExe)) {
    throw 'La prueba exige un runner sin instalaciones previas de esta aplicación.'
}

$oldDir = Join-Path $repoRoot 'dist\upgrade-test-old'
New-Item -ItemType Directory -Path $oldDir -Force | Out-Null
& $IsccPath '/DMyAppVersion=0.0.9-ci' "/O$oldDir" (Join-Path $repoRoot 'installer\windows.iss')
if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar el instalador de versión anterior simulada.' }
$oldInstaller = Join-Path $oldDir 'ProduccionLiturgicaOBS-Setup.exe'
if (-not (Test-Path -LiteralPath $oldInstaller)) { throw 'No se generó el instalador anterior simulado.' }

function Install-TestVersion([string]$exe) {
    $process = Start-Process -FilePath $exe -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-' -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "El instalador terminó con código $($process.ExitCode)." }
}

$sentinel = $null
try {
    Install-TestVersion $oldInstaller
    $firstEntry = Assert-Installation '0.0.9-ci'
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    $sentinel = Join-Path $dataDir ('ci-upgrade-' + [guid]::NewGuid().ToString('N') + '.txt')
    Set-Content -LiteralPath $sentinel -Value 'datos-locales-se-conservan' -Encoding utf8 -NoNewline

    Install-TestVersion $installerPath
    $newEntry = Assert-Installation $CurrentVersion
    if ($firstEntry.PSPath -ne $newEntry.PSPath) {
        throw 'La actualización creó una nueva entrada de desinstalación.'
    }
    if (-not (Test-Path -LiteralPath $sentinel) -or
        (Get-Content -LiteralPath $sentinel -Raw) -ne 'datos-locales-se-conservan') {
        throw 'La actualización perdió o modificó datos de usuario.'
    }
    Write-Host 'OK: se actualizó en el mismo directorio, con una entrada y sin perder datos.'

    $uninstaller = Join-Path $installDir 'unins000.exe'
    if (-not (Test-Path -LiteralPath $uninstaller)) {
        throw 'El instalador no creó el desinstalador.'
    }
    $uninstall = Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -Wait -PassThru
    if ($uninstall.ExitCode -ne 0) {
        throw "La desinstalación de prueba devolvió código $($uninstall.ExitCode)."
    }
    if (-not (Test-Path -LiteralPath $sentinel)) {
        throw 'La desinstalación borró datos locales del usuario.'
    }
    Write-Host 'OK: desinstalación conserva datos locales.'
}
finally {
    # Eliminar exclusivamente el marcador temporal que creó esta prueba.
    if ($sentinel -and (Test-Path -LiteralPath $sentinel)) {
        Remove-Item -LiteralPath $sentinel -Force
    }
}
