$ErrorActionPreference = "Stop"

# Configuration
$RemoteUser = "root"
$RemoteHost = "72.61.221.69" # Updated with provided IP
$RemoteDBName = "capacitacion" # Updated to capacitacion as per user request
$RemoteDumpPath = "/tmp/backup_capacitacion_$(Get-Date -Format 'yyyyMMdd').backup"
$LocalBackupDir = "c:\proyectos\tba\backups"

# Ensure local backup directory exists
if (-not (Test-Path -Path $LocalBackupDir)) {
    New-Item -ItemType Directory -Path $LocalBackupDir | Out-Null
    Write-Host "Created backup directory: $LocalBackupDir"
}

Write-Host "1. Connecting to server to create database dump (Custom Format for pgAdmin)..."
# Using 'su - postgres' to avoid password prompt since we are root
# -Fc: Custom format (needed for pgAdmin Restore)
ssh $RemoteUser@$RemoteHost "su - postgres -c 'pg_dump -p 1437 -Fc $RemoteDBName' > $RemoteDumpPath"

if ($LASTEXITCODE -eq 0) {
    Write-Host "   Dump created successfully at $RemoteDumpPath"
}
else {
    Write-Error "   Failed to create dump on server."
}

Write-Host "2. Downloading dump to local machine..."
scp "$RemoteUser@$RemoteHost`:$RemoteDumpPath" $LocalBackupDir

if ($LASTEXITCODE -eq 0) {
    Write-Host "   Download complete: $LocalBackupDir\$(Split-Path $RemoteDumpPath -Leaf)"
}
else {
    Write-Error "   Failed to download dump."
}

Write-Host "3. Cleaning up remote dump file..."
ssh $RemoteUser@$RemoteHost "rm $RemoteDumpPath"

Write-Host "4. Restoring database to local PostgreSQL..."
$PgRestorePath = "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe"
$LocalDBName = "capacitacion"
$LocalDBUser = "postgres"
$LocalDBPort = "5432" # Updated to 5432 for local
$LocalDBHost = "localhost"

# Set password for pg_restore to avoid prompt
$env:PGPASSWORD = "ñandu2025"

# Create DB if not exists (try/catch or just ignore error)
# We use createdb if available, or just rely on pg_restore -C (create) but -C requires connection to postgres db usually.
# Let's try -C -d postgres
& $PgRestorePath --host $LocalDBHost --port $LocalDBPort --username $LocalDBUser --dbname "postgres" --clean --create --verbose "$LocalBackupDir\$(Split-Path $RemoteDumpPath -Leaf)"

# Restore
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Database restored successfully!"
}
else {
    Write-Error "   Restore failed. Check logs above."
}

# Clear password
$env:PGPASSWORD = $null

Write-Host "Done! Database synchronized."
