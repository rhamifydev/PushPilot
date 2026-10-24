param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

python -m autopush.cli @ArgsList
