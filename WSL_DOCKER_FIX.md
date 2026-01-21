# Fixing WSL/Docker Desktop Issues on Windows

## Error Message
```
An error occurred while running a WSL command. Please check your WSL configuration and try again.
running wslexec: An error occurred while running the command. 
DockerDesktop/Wsl/ExecError: c:\windows\system32\wsl.exe --unmount docker_data.vhdx: 
exit status 0xffffffff
```

## Quick Fixes (Try in Order)

### 1. Restart Docker Desktop (Simplest)
1. Right-click Docker Desktop icon in system tray
2. Click "Quit Docker Desktop"
3. Wait 10 seconds
4. Start Docker Desktop again
5. Wait for it to fully start (green icon in system tray)

### 2. Restart WSL (If Docker restart doesn't work)
```powershell
# Open PowerShell as Administrator, then run:
wsl --shutdown
# Wait 10 seconds, then start Docker Desktop again
```

### 3. Restart Docker Desktop Service
```powershell
# Open PowerShell as Administrator
Stop-Service -Name "com.docker.service"
Start-Service -Name "com.docker.service"
# Then start Docker Desktop
```

### 4. Full Docker Desktop Reset (If above don't work)
1. Quit Docker Desktop completely
2. Open PowerShell as Administrator:
```powershell
wsl --shutdown
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data
```
3. Start Docker Desktop (it will recreate WSL distributions)

**Warning**: This will delete all Docker containers, images, and volumes. You'll need to rebuild images.

### 5. Check WSL Status
```powershell
wsl --list --verbose
# Should show "Running" for docker-desktop and docker-desktop-data
```

### 6. Update WSL (If outdated)
```powershell
wsl --update
wsl --shutdown
# Restart Docker Desktop
```

## Prevention Tips

1. **Don't manually unmount WSL distributions** while Docker is running
2. **Close Docker Desktop properly** (don't force quit)
3. **Keep WSL updated**: `wsl --update`
4. **Keep Docker Desktop updated**

## Alternative: Use Docker Without WSL2

If WSL2 continues to cause issues, you can use Docker Desktop with Hyper-V backend:
1. Open Docker Desktop Settings
2. Go to General
3. Uncheck "Use the WSL 2 based engine"
4. Click "Apply & Restart"

**Note**: This uses Hyper-V instead of WSL2, which may have different performance characteristics.

## After Fixing

Once Docker Desktop is working:
1. Wait for Docker Desktop to fully start (green icon)
2. Try: `docker ps` (should show no errors)
3. Try building again: `docker-compose build`
4. Then start services: `docker-compose up -d`
