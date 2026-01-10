@echo off
echo Starting Frontend Development Server...
echo.
echo Memory Limit: 4GB
echo Frontend URL: http://localhost:8081
echo Backend API: http://localhost:3001
echo.
echo Press Ctrl+C to stop the server
echo.

set NODE_OPTIONS=--max-old-space-size=4096
npm run dev
