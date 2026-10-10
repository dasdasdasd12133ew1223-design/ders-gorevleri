$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$issFile = Join-Path $projectRoot "installer.iss"
$innoCompiler = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
$sourceDir = Join-Path $projectRoot "build\installer-source"
$pyinstallerWorkDir = Join-Path $projectRoot "build\pyinstaller-work"
$pyinstallerSpecDir = Join-Path $projectRoot "build\pyinstaller-spec"
$installer = Join-Path $projectRoot "site\downloads\Ders-Gorevleri-Setup.exe"
$hashFile = Join-Path $projectRoot "site\downloads\SHA256SUMS.txt"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher bulunamadi. Python 3.14'ü kurun."
}
if (-not (Test-Path -LiteralPath $innoCompiler)) {
    throw "Inno Setup 6 derleyicisi bulunamadi. Once Inno Setup 6'yi kurun."
}

& py -3.14 -m PyInstaller --version
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller bulunamadi. Once requirements-build.txt dosyasindaki bagimliliklari kurun."
}

if (Test-Path -LiteralPath $sourceDir) {
    Remove-Item -LiteralPath $sourceDir -Recurse -Force
}
New-Item -ItemType Directory -Path $sourceDir | Out-Null

try {
    $pyinstallerArgs = @(
        "-3.14",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--name",
        "DersGorevleri",
        "--distpath",
        $sourceDir,
        "--workpath",
        $pyinstallerWorkDir,
        "--specpath",
        $pyinstallerSpecDir,
        "--icon",
        (Join-Path $projectRoot "assets\logo.ico"),
        "--add-data",
        "$(Join-Path $projectRoot 'assets');assets",
        "--collect-all",
        "customtkinter",
        "--collect-all",
        "pystray",
        "--collect-all",
        "winotify",
        (Join-Path $projectRoot "app.py")
    )
    & py @pyinstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller derlemesi basarisiz oldu (kod $LASTEXITCODE)."
    }

    $appDirectory = Join-Path $sourceDir "DersGorevleri"
    $appExecutable = Join-Path $appDirectory "DersGorevleri.exe"
    $appIcon = Join-Path $appDirectory "_internal\assets\logo.ico"
    if (-not (Test-Path -LiteralPath $appExecutable)) {
        throw "DersGorevleri.exe PyInstaller ciktisinda bulunamadi."
    }
    if (-not (Test-Path -LiteralPath $appIcon)) {
        throw "Uygulama simgesi PyInstaller ciktisinda bulunamadi."
    }

    Push-Location $projectRoot
    try {
        & $innoCompiler $issFile
    }
    finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup derlemesi basarisiz oldu (kod $LASTEXITCODE)."
    }
    if (-not (Test-Path -LiteralPath $installer)) {
        throw "Derleme tamamlandi ancak kurulum dosyasi bulunamadi."
    }

    $rootDownloads = Join-Path $projectRoot "downloads"
    New-Item -ItemType Directory -Path $rootDownloads -Force | Out-Null
    Copy-Item -LiteralPath $installer -Destination (Join-Path $rootDownloads "Ders-Gorevleri-Setup.exe") -Force

    $hash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash
    $hashLine = "$hash  Ders-Gorevleri-Setup.exe"
    Set-Content -LiteralPath $hashFile -Value $hashLine -Encoding ascii
    Set-Content -LiteralPath (Join-Path $rootDownloads "SHA256SUMS.txt") -Value $hashLine -Encoding ascii
    foreach ($htmlFile in @(
        (Join-Path $projectRoot "index.html"),
        (Join-Path $projectRoot "site\index.html")
    )) {
        $html = [System.IO.File]::ReadAllText($htmlFile)
        $hashPattern = '(<code class="installer-sha256">)[^<]*(</code>)'
        if (-not [regex]::IsMatch($html, $hashPattern)) {
            throw "SHA-256 code alanı bulunamadi: $htmlFile"
        }
        $replacement = [System.Text.RegularExpressions.MatchEvaluator]{
            param($match)
            $match.Groups[1].Value + $hash + $match.Groups[2].Value
        }
        $updatedHtml = [regex]::Replace($html, $hashPattern, $replacement)
        [System.IO.File]::WriteAllText(
            $htmlFile,
            $updatedHtml,
            [System.Text.UTF8Encoding]::new($false)
        )
    }
    Write-Output "Kurulum dosyasi: $installer"
    Write-Output "SHA-256: $hash"
}
finally {
    if (Test-Path -LiteralPath $sourceDir) {
        Remove-Item -LiteralPath $sourceDir -Recurse -Force
    }
}
