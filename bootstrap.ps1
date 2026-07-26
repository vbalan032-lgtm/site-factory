[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("New", "Attach", "Doctor", "Update", "ConfigureCodex", "Pack", "Verify")]
    [string]$Mode,
    [string]$Target,
    [string]$ProjectId,
    [string]$ProjectName,
    [string[]]$Profile = @("core", "nextjs-ui"),
    [string]$Output,
    [string]$Archive,
    [string]$Checksum,
    [string]$Manifest,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$FactoryRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonMode = if ($Mode -eq "ConfigureCodex") { "configure-codex" } else { $Mode.ToLowerInvariant() }
$Arguments = @("-m", "factory.bootstrap", $PythonMode, "--source", $FactoryRoot)

if ($Target) { $Arguments += @("--target", $Target) }
if ($ProjectId) { $Arguments += @("--project-id", $ProjectId) }
if ($ProjectName) { $Arguments += @("--project-name", $ProjectName) }
if ($Profile) { $Arguments += @("--profiles", ($Profile -join ",")) }
if ($Output) { $Arguments += @("--output", $Output) }
if ($Archive) { $Arguments += @("--archive", $Archive) }
if ($Checksum) { $Arguments += @("--checksum", $Checksum) }
if ($Manifest) { $Arguments += @("--manifest", $Manifest) }
if ($Apply) { $Arguments += "--apply" }

$Python = Get-Command py -ErrorAction SilentlyContinue
if ($Python) {
    & py -3 @Arguments
} else {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $Python) { throw "Python 3.12+ was not found in PATH." }
    & python @Arguments
}
exit $LASTEXITCODE
