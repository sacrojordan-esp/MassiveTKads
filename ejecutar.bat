@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo   ANALIZADOR DE CAMPAÑAS TIKTOK ADS
echo ===============================================
echo.
set /p fecha="Ingrese fecha (YYYY-MM-DD) o presione Enter para fecha de ayer: "

if "%fecha%"=="" (
    echo.
    echo Usando fecha de ayer...
    py main.py
) else (
    echo.
    echo Usando fecha %fecha%...
    py main.py %fecha%
)

echo.
echo Proceso terminado.
pause