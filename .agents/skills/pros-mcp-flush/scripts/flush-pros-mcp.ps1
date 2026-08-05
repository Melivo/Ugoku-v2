[CmdletBinding(SupportsShouldProcess, ConfirmImpact = "Medium")]
param(
  [string]$HomePath = [Environment]::GetFolderPath("UserProfile"),
  [string]$OpenCodeConfig,
  [string]$AnythingLlmConfig,
  [string]$ManagedStatePath,
  [switch]$SkipCredentials,
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $Force -and -not $WhatIfPreference) {
  throw "Refusing to flush Pros MCP state without -Force. Use -WhatIf to preview."
}

if (-not $OpenCodeConfig) {
  $OpenCodeConfig = Join-Path $HomePath ".config\opencode\opencode.jsonc"
}
if (-not $AnythingLlmConfig) {
  $AnythingLlmConfig = Join-Path $HomePath "AppData\Roaming\anythingllm-desktop\storage\plugins\anythingllm_mcp_servers.json"
}
if (-not $ManagedStatePath) {
  $ManagedStatePath = Join-Path $HomePath ".config\pros\mcp\managed-state.json"
}

$node = Get-Command node -ErrorAction Stop
$cleaner = Join-Path $PSScriptRoot "remove-pros-mcp-entries.cjs"
$cleanerArgs = @(
  $cleaner,
  "--opencode", $OpenCodeConfig,
  "--anythingllm", $AnythingLlmConfig
)
if ($WhatIfPreference) {
  $cleanerArgs += "--dry-run"
}

$configReportText = & $node.Source @cleanerArgs
if ($LASTEXITCODE -ne 0) {
  throw "Pros MCP client cleanup failed."
}
$configReport = $configReportText | ConvertFrom-Json

$removedCredentials = @()
$credentialPatterns = @(
  '^pros:hubspot:(mcp-remote|oauth-client)(:chunk:\d+)?$',
  '^pros:qnap:mcp-assistant(:chunk:\d+)?$',
  '^pros:qnap-files:[^:]+(:chunk:\d+)?$',
  '^pros:microsoft-graph:[^:]+(:chunk:\d+)?$',
  '^pros:integrations:microsoft-graph:[^:]+(:chunk:\d+)?$'
)

if (-not $SkipCredentials) {
  if ($env:OS -ne "Windows_NT") {
    throw "Credential cleanup is implemented only for Windows. Use -SkipCredentials only for fixture tests."
  }

  if (-not ("ProsMcpCredentialStore" -as [type])) {
    Add-Type -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class ProsMcpCredentialStore
{
    private const uint Generic = 1;
    private const int NotFound = 1168;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct Credential
    {
        public uint Flags;
        public uint Type;
        public string TargetName;
        public string Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public uint CredentialBlobSize;
        public IntPtr CredentialBlob;
        public uint Persist;
        public uint AttributeCount;
        public IntPtr Attributes;
        public string TargetAlias;
        public string UserName;
    }

    [DllImport("advapi32.dll", EntryPoint = "CredEnumerateW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredEnumerate(string filter, uint flags, out uint count, out IntPtr credentials);

    [DllImport("advapi32.dll", EntryPoint = "CredDeleteW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredDelete(string target, uint type, uint flags);

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern void CredFree(IntPtr buffer);

    public static string[] ListProsTargets()
    {
        uint count;
        IntPtr credentials;
        if (!CredEnumerate("pros:*", 0, out count, out credentials))
        {
            int error = Marshal.GetLastWin32Error();
            if (error == NotFound) return new string[0];
            throw new Win32Exception(error);
        }

        try
        {
            var targets = new List<string>();
            for (int index = 0; index < count; index++)
            {
                IntPtr credentialPointer = Marshal.ReadIntPtr(credentials, index * IntPtr.Size);
                Credential credential = (Credential)Marshal.PtrToStructure(credentialPointer, typeof(Credential));
                targets.Add(credential.TargetName);
            }
            return targets.ToArray();
        }
        finally
        {
            CredFree(credentials);
        }
    }

    public static bool Delete(string target)
    {
        if (CredDelete(target, Generic, 0)) return true;
        int error = Marshal.GetLastWin32Error();
        if (error == NotFound) return false;
        throw new Win32Exception(error);
    }
}
"@
  }

  foreach ($target in [ProsMcpCredentialStore]::ListProsTargets()) {
    $matches = $false
    foreach ($pattern in $credentialPatterns) {
      if ($target -match $pattern) {
        $matches = $true
        break
      }
    }
    if (-not $matches) { continue }

    $removedCredentials += $target
    if (-not $WhatIfPreference -and $PSCmdlet.ShouldProcess($target, "Delete Pros MCP credential")) {
      [void][ProsMcpCredentialStore]::Delete($target)
    }
  }
}

$stateRemoved = Test-Path -LiteralPath $ManagedStatePath -PathType Leaf
if ($stateRemoved -and -not $WhatIfPreference -and $PSCmdlet.ShouldProcess($ManagedStatePath, "Delete Pros MCP managed state")) {
  Remove-Item -LiteralPath $ManagedStatePath -Force
}

$clientIdPresent = $false
if (-not $SkipCredentials) {
  $clientIdPresent = -not [string]::IsNullOrWhiteSpace(
    [Environment]::GetEnvironmentVariable("PROS_MICROSOFT_CLIENT_ID", "User")
  )
  if ($clientIdPresent -and -not $WhatIfPreference -and $PSCmdlet.ShouldProcess("PROS_MICROSOFT_CLIENT_ID", "Delete user environment variable")) {
    [Environment]::SetEnvironmentVariable("PROS_MICROSOFT_CLIENT_ID", $null, "User")
  }
  Remove-Item Env:PROS_MICROSOFT_CLIENT_ID -ErrorAction SilentlyContinue
}

[pscustomobject]@{
  DryRun = [bool]$WhatIfPreference
  OpenCodeRemoved = @($configReport.opencode.removed)
  AnythingLlmRemoved = @($configReport.anythingllm.removed)
  ManagedStateRemoved = $stateRemoved
  UserClientIdRemoved = $clientIdPresent
  CredentialTargetsRemoved = @($removedCredentials)
  CredentialsSkipped = [bool]$SkipCredentials
} | ConvertTo-Json -Depth 4
