function dotcmd {
  param(
    [string]$name,
    [Parameter(ValueFromRemainingArguments = $true)]
    $args
  )

  $dotcmdScript = "$env:DOTFILES\dotcmd_runner.py"  # Adjust if needed
  if (-not (Test-Path $dotcmdScript)) {
    Write-Error "dotcmd not found at $dotcmdScript"
    return
  }

  $cmd = @($name) + $args
  & python $dotcmdScript @cmd
}
