# setup_github.ps1
# Sube el proyecto RR AI al repositorio https://github.com/tiagoharari1/HTML-RR
# Ejecutar UNA sola vez desde PowerShell, parado en la carpeta del proyecto:
#   .\setup_github.ps1

$ErrorActionPreference = "Stop"

Write-Host "==> Preparando repositorio en $(Get-Location)" -ForegroundColor Cyan

# 1. Limpiar cualquier .git roto que haya quedado de intentos previos
if (Test-Path .git) {
    Write-Host "==> Borrando .git previo..."
    Remove-Item -Recurse -Force .git
}

# 2. Inicializar repo con rama main
git init -b main

# 3. Identidad del commit (cambiá si querés otro nombre/email)
git config user.email "tiago.harari@despegar.com"
git config user.name  "Tiago Harari"

# 4. Conectar al remoto de GitHub
git remote add origin https://github.com/tiagoharari1/HTML-RR.git

# 5. Stage + primer commit
git add .
git commit -m "Initial commit: RR AI v1 (HTML/B2B Run Rate)"

# 6. Push (Git Credential Manager va a pedir login la primera vez)
git push -u origin main

Write-Host "`n==> Listo. Repo subido a https://github.com/tiagoharari1/HTML-RR" -ForegroundColor Green
