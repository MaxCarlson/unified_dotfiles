# ─── Linux‑style cut, awk, xargs for PowerShell ──────────────────────────────

function cut {
    <#
    .SYNOPSIS
    Extract character ranges from each line, e.g. `cut -c 3-`
    #>
    param(
        [Parameter(Mandatory)]
        [string] $c,                          # e.g. "3-" or "3-5"
        [Parameter(ValueFromPipeline=$true)]
        [string] $line
    )
    process {
        if ($c -match '^(\d+)-(\d*)$') {
            $start = [int]$Matches[1] - 1
            $end   = if ($Matches[2]) { [int]$Matches[2] } else { $line.Length }
            if ($start -lt $line.Length) {
                $length = [Math]::Min($end - $start, $line.Length - $start)
                $line.Substring($start, $length)
            }
        } else {
            Write-Warning "Unsupported range: $c"
            $line
        }
    }
}

function awk {
    <#
    .SYNOPSIS
    Very simple “print $N” support: awk '{print $1}'
    #>
    param(
        [Parameter(Mandatory)]
        [string] $script,                    # only supports '{print $N}'
        [Parameter(ValueFromPipeline=$true)]
        [string] $line
    )
    process {
        if ($script -match '^\{print \$([0-9]+)\}$') {
            $col = [int]$Matches[1] - 1
            $fields = -split $line
            if ($fields.Length -gt $col) { $fields[$col] }
        } else {
            Write-Warning "Unsupported awk script: $script"
            $line
        }
    }
}

function xargs {
    <#
    .SYNOPSIS
    Collects all piped input lines, then invokes a command with them as args:
      ... | xargs git branch -D
    #>
    param(
        [Parameter(Mandatory)]
        [string[]] $Cmd,                    # e.g. 'git','branch','-D'
        [Parameter(ValueFromPipeline=$true)]
        [string] $item
    )
    begin { $argsList = @() }
    process {
        if ($item) { $argsList += $item }
    }
    end {
        if ($argsList.Count) {
            & $Cmd $argsList
        }
    }
}
