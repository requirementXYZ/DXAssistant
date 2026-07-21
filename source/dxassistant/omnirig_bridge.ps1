param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("status", "align")]
    [string]$Action,
    [int]$FrequencyHz = 0
)

$ErrorActionPreference = "Stop"
$RX_STATE = 2097152
$SPLIT_ON = 32768
$VFO_AB = 256
$FREQ_A = 4
$FREQ_B = 8

function Capabilities($rig) {
    $caps = [ordered]@{
        read_freq_a = [bool]$rig.IsParamReadable($FREQ_A)
        write_freq_a = [bool]$rig.IsParamWriteable($FREQ_A)
        read_freq_b = [bool]$rig.IsParamReadable($FREQ_B)
        write_freq_b = [bool]$rig.IsParamWriteable($FREQ_B)
        read_vfo_ab = [bool]$rig.IsParamReadable($VFO_AB)
        read_split = [bool]$rig.IsParamReadable($SPLIT_ON)
        read_rx = [bool]$rig.IsParamReadable($RX_STATE)
    }
    $missing = @()
    foreach ($name in $caps.Keys) {
        if (-not $caps[$name]) { $missing += $name }
    }
    return [ordered]@{
        compatible = ($missing.Count -eq 0)
        missing = $missing
        parameters = $caps
    }
}

function Snapshot($rig) {
    $capabilities = Capabilities $rig
    return [ordered]@{
        ok = $true
        rig_type = [string]$rig.RigType
        status = [string]$rig.StatusStr
        frequency_a_hz = if ($capabilities.parameters.read_freq_a) { [int]$rig.FreqA } else { 0 }
        frequency_b_hz = if ($capabilities.parameters.read_freq_b) { [int]$rig.FreqB } else { 0 }
        receive_frequency_hz = if ($capabilities.compatible) { [int]$rig.GetRxFrequency() } else { 0 }
        split = if (-not $capabilities.parameters.read_split) { "Unavailable" } elseif ([int]$rig.Split -eq $SPLIT_ON) { "On" } else { "Other" }
        routing = if (-not $capabilities.parameters.read_vfo_ab) { "Unavailable" } elseif ([int]$rig.Vfo -eq $VFO_AB) { "RX-A/TX-B" } else { "Other" }
        tx_state = if (-not $capabilities.parameters.read_rx) { "Unavailable" } elseif ([int]$rig.Tx -eq $RX_STATE) { "RX" } else { "NOT_RX" }
        capabilities = $capabilities
    }
}

try {
    $omni = New-Object -ComObject OmniRig.OmniRigX
    $rig = $omni.Rig1
    if ([int]$rig.Status -ne 4) { throw "OmniRig Rig 1 is not online: $($rig.StatusStr)" }

    if ($Action -eq "align") {
        $capabilities = Capabilities $rig
        if (-not $capabilities.compatible) {
            throw "OmniRig profile '$($rig.RigType)' lacks required DX Assistant capabilities: $($capabilities.missing -join ', ')"
        }
        if ($FrequencyHz -lt 1800000 -or $FrequencyHz -gt 54000000) { throw "Frequency is outside the supported range" }
        if ([int]$rig.Tx -ne $RX_STATE) { throw "Radio is not in receive; tuning was blocked" }
        if ([int]$rig.Split -ne $SPLIT_ON) { throw "Split is not on; tuning was blocked" }
        if ([int]$rig.Vfo -ne $VFO_AB) { throw "Rig routing is not receive A / transmit B; tuning was blocked" }

        $originalA = [int]$rig.FreqA
        $originalB = [int]$rig.FreqB
        $movedA = $false
        $movedB = $false
        try {
            if ([Math]::Abs(([int]$rig.FreqB) - $FrequencyHz) -gt 100) {
                $rig.FreqB = $FrequencyHz
                $movedB = $true
                Start-Sleep -Milliseconds 500
            }
            if ([Math]::Abs(([int]$rig.FreqB) - $FrequencyHz) -gt 100) { throw "VFO B failed frequency verification" }
            if ([int]$rig.Tx -ne $RX_STATE) { throw "Transmit state detected after moving VFO B" }
            if ([Math]::Abs(([int]$rig.FreqA) - $FrequencyHz) -gt 100) {
                $rig.FreqA = $FrequencyHz
                $movedA = $true
                Start-Sleep -Milliseconds 750
            }
            if ([Math]::Abs(([int]$rig.FreqA) - $FrequencyHz) -gt 100) { throw "VFO A failed frequency verification" }
            if ([Math]::Abs(([int]$rig.GetRxFrequency()) - $FrequencyHz) -gt 100) { throw "Receive frequency failed verification" }
            if ([int]$rig.Tx -ne $RX_STATE) { throw "Transmit state detected during verification" }
        } catch {
            if ([int]$rig.Tx -eq $RX_STATE) {
                if ($movedB) { $rig.FreqB = $originalB; Start-Sleep -Milliseconds 500 }
                if ($movedA) { $rig.FreqA = $originalA; Start-Sleep -Milliseconds 750 }
            }
            throw
        }
    }

    Snapshot $rig | ConvertTo-Json -Compress
} catch {
    [ordered]@{ ok = $false; message = $_.Exception.Message } | ConvertTo-Json -Compress
    exit 1
}
