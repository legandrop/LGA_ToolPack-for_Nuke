# git-safe-merge.ps1
# Safe merge tool: pre-flight checks + merge current branch to main
# Aborts on any issue without modifying the repo.
# Designed to be copied to %TEMP% and run from there (survives git checkout).

param(
    [string]$TargetBranch = "main",
    [string]$WorkingDir = ""
)

if ($WorkingDir -and (Test-Path $WorkingDir)) {
    Set-Location $WorkingDir
}

function Write-Abort {
    param([string]$Message)
    Write-Host ""
    Write-Host "  ABORT: $Message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  OK    $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  INFO  $Message" -ForegroundColor Cyan
}

function Invoke-Git {
    param([string]$Arguments)
    $output = Invoke-Expression "git $Arguments 2>&1" | Out-String
    return @{ Output = $output.Trim(); ExitCode = $LASTEXITCODE }
}

$separator = "  " + ("-" * 40)

# -- 0. Verify we are inside a git repo -----------------------------------

$r = Invoke-Git "rev-parse --show-toplevel"
if ($r.ExitCode -ne 0) {
    Write-Abort "not inside a git repository"
}
$gitRoot = $r.Output

Write-Host ""
Write-Host "  git-safe-merge" -ForegroundColor Yellow
Write-Host $separator -ForegroundColor DarkGray
Write-Info "repo: $gitRoot"

# -- 1. Working tree must be clean ----------------------------------------

$r = Invoke-Git "status --porcelain"
if ($r.Output) {
    Write-Abort "working tree not clean`n`n$($r.Output)"
}
Write-Ok "working tree is clean"

if (Test-Path (Join-Path $gitRoot ".git/MERGE_HEAD")) {
    Write-Abort "a merge is currently in progress"
}

$rebaseDirs = @(".git/rebase-merge", ".git/rebase-apply")
foreach ($d in $rebaseDirs) {
    if (Test-Path (Join-Path $gitRoot $d)) {
        Write-Abort "a rebase is currently in progress"
    }
}
Write-Ok "no merge or rebase in progress"

# -- 2. Detect current branch ---------------------------------------------

$r = Invoke-Git "symbolic-ref --short HEAD"
if ($r.ExitCode -ne 0) {
    Write-Abort "detached HEAD state -- checkout a branch first"
}
$currentBranch = $r.Output

if ($currentBranch -eq $TargetBranch) {
    Write-Abort "current branch is $TargetBranch -- switch to your working branch first"
}
Write-Ok "current branch: $currentBranch"

# -- 3. Fetch and verify sync with remote ---------------------------------

Write-Info "fetching from origin..."
$r = Invoke-Git "fetch origin"
if ($r.ExitCode -ne 0) {
    Write-Abort "git fetch failed -- check your network connection"
}

$remoteBranch = "origin/$currentBranch"
$r = Invoke-Git "rev-list --count $currentBranch..$remoteBranch"
if ($r.ExitCode -eq 0 -and [int]$r.Output -gt 0) {
    Write-Abort "$currentBranch is $($r.Output) commit(s) behind $remoteBranch -- pull first"
}
Write-Ok "$currentBranch is up to date with $remoteBranch"

$remoteTarget = "origin/$TargetBranch"
$r = Invoke-Git "rev-parse --verify $TargetBranch"
if ($r.ExitCode -ne 0) {
    Write-Abort "local branch '$TargetBranch' does not exist"
}

$r = Invoke-Git "rev-list --count $TargetBranch..$remoteTarget"
if ($r.ExitCode -eq 0 -and [int]$r.Output -gt 0) {
    Write-Abort "local $TargetBranch is $($r.Output) commit(s) behind $remoteTarget -- update $TargetBranch first"
}
Write-Ok "local $TargetBranch is up to date with $remoteTarget"

# -- 4. Simulate merge (dry run) ------------------------------------------

Write-Info "checking for conflicts..."

$r = Invoke-Git "merge-tree --write-tree $TargetBranch $currentBranch"
if ($r.ExitCode -ne 0) {
    $conflictLines = $r.Output -split "`n" | Where-Object { $_ -match "^CONFLICT" }
    $fileList = ""
    if ($conflictLines) {
        $fileList = "`n`n  Conflicting files:`n"
        foreach ($line in $conflictLines) {
            if ($line -match "CONFLICT.*:\s+(.+)$") {
                $fileList += "    - $($Matches[1])`n"
            } else {
                $fileList += "    - $line`n"
            }
        }
    }
    Write-Abort "merge would create conflicts$fileList"
}
Write-Ok "no conflicts detected"

$r = Invoke-Git "rev-list --count $TargetBranch..$currentBranch"
$commitCount = $r.Output
$commitWord = if ([int]$commitCount -eq 1) { "commit" } else { "commits" }

$r = Invoke-Git "diff --stat $TargetBranch...$currentBranch"
$diffStat = $r.Output

# -- 5. Summary ------------------------------------------------------------

Write-Host ""
Write-Host $separator -ForegroundColor DarkGray
Write-Host "  READY TO MERGE" -ForegroundColor Green
Write-Host ""
Write-Host "  Branch:    $currentBranch  ->  $TargetBranch" -ForegroundColor White
Write-Host "  Commits:   $commitCount $commitWord" -ForegroundColor White
Write-Host "  Conflicts: none" -ForegroundColor White
Write-Host ""
if ($diffStat) {
    Write-Host "  Changes:" -ForegroundColor White
    foreach ($line in ($diffStat -split "`n")) {
        Write-Host "    $line" -ForegroundColor DarkGray
    }
    Write-Host ""
}

# -- 6. Confirmation -------------------------------------------------------

$answer = Read-Host "  Merge $currentBranch -> $TargetBranch ? (y/n)"
if ($answer -ne "y") {
    Write-Host ""
    Write-Host "  Cancelled." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

# -- 7. Execute merge ------------------------------------------------------

Write-Host ""
Write-Info "switching to $TargetBranch..."
$r = Invoke-Git "checkout $TargetBranch"
if ($r.ExitCode -ne 0) {
    Write-Abort "failed to checkout $TargetBranch"
}

Write-Info "merging $currentBranch..."
$r = Invoke-Git "merge $currentBranch"
if ($r.ExitCode -ne 0) {
    Write-Host "  $($r.Output)" -ForegroundColor Red
    Invoke-Git "checkout $currentBranch" | Out-Null
    Write-Abort "merge failed -- switched back to $currentBranch"
}

Write-Info "pushing to origin/$TargetBranch..."
$r = Invoke-Git "push origin $TargetBranch"
if ($r.ExitCode -ne 0) {
    Write-Host "  $($r.Output)" -ForegroundColor Red
    Write-Abort "push failed -- you are now on $TargetBranch with the merge applied locally"
}

Write-Info "switching back to $currentBranch..."
Invoke-Git "checkout $currentBranch" | Out-Null

Write-Host ""
Write-Host $separator -ForegroundColor DarkGray
Write-Host "  DONE" -ForegroundColor Green
Write-Host "  $currentBranch merged into $TargetBranch and pushed to origin" -ForegroundColor White
Write-Host ""
