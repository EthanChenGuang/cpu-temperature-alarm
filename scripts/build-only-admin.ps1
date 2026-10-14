Set-Location C:\dev\cpu-high-temperature-alert
$Py = "C:\Users\Guang\AppData\Local\Programs\Python\Python313\python.exe"
$Log = "$env:TEMP\build-only-log.txt"
"" | Set-Content $Log

function Log($m) { Add-Content $Log $m; Write-Host $m }

Log "Python: $(& $Py --version 2>&1)"
& $Py -m pip install -q pyinstaller 2>&1 | ForEach-Object { Log $_ }
Log "pip exit: $LASTEXITCODE"
Log "PyInstaller: $(& $Py -m PyInstaller --version 2>&1)"
Log "Starting build..."
& $Py -m PyInstaller cpu-temp-alert.spec --noconfirm --clean 2>&1 | ForEach-Object { Log $_ }
Log "pyinstaller exit: $LASTEXITCODE"
$exe = "dist\cpu-temp-alert\cpu-temp-alert.exe"
Log "exe exists: $(Test-Path $exe)"
