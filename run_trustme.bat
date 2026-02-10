@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  EVOLV - Regulatory Compliance Engine
::  A WingstarTech Inc. Product
:: ============================================================
::
::  Usage:
::    run_trustme              Run full pipeline (interactive URS)
::    run_trustme -f reqs.txt  URS from file
::    run_trustme --skip-ingest Skip knowledge base refresh
::
:: ============================================================

title EVOLV - Validation Package Generator

echo.
echo ============================================================
echo   Starting EVOLV Engine...
echo   A WingstarTech Inc. Product
echo ============================================================
echo.

:: ── Resolve project root to this script's directory ─────────
set "PROJECT_ROOT=%~dp0"
:: Strip trailing backslash
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

:: ── Parse arguments ─────────────────────────────────────────
set "SKIP_INGEST=0"
set "URS_ARGS="

:parse_args
if "%~1"=="" goto done_args
if /i "%~1"=="--skip-ingest" (
    set "SKIP_INGEST=1"
    shift
    goto parse_args
)
:: Pass all other arguments through to draft_urs.py
set "URS_ARGS=!URS_ARGS! %1"
shift
goto parse_args
:done_args

:: ── Verify Python is available ──────────────────────────────
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not on PATH.
    echo         Install Python 3.10+ and try again.
    exit /b 1
)

:: ── Check API keys ──────────────────────────────────────────
if "%OPENAI_API_KEY%"=="" (
    echo [ERROR] OPENAI_API_KEY environment variable is not set.
    exit /b 1
)
if "%PINECONE_API_KEY%"=="" (
    echo [ERROR] PINECONE_API_KEY environment variable is not set.
    exit /b 1
)

echo   Project root:  %PROJECT_ROOT%
echo.

:: ============================================================
::  STEP 1 / 4  -  Refresh Knowledge Base
:: ============================================================

if "%SKIP_INGEST%"=="1" (
    echo [1/4] Skipping knowledge base refresh (--skip-ingest)
    echo.
) else (
    echo [1/4] Refreshing knowledge base...
    echo ------------------------------------------------------------
    python "%PROJECT_ROOT%\scripts\ingest_docs.py"
    if errorlevel 1 (
        echo.
        echo [ERROR] Knowledge base ingestion failed.
        echo         Check that docs/raw/ contains PDF files and
        echo         API keys are configured.
        exit /b 1
    )
    echo.
)

:: ============================================================
::  STEP 2 / 4  -  Generate User Requirements (URS)
:: ============================================================

echo [2/4] Generating User Requirements Specification...
echo ------------------------------------------------------------
python "%PROJECT_ROOT%\scripts\draft_urs.py" %URS_ARGS%
if errorlevel 1 (
    echo.
    echo [ERROR] URS generation failed.
    exit /b 1
)
echo.

:: ============================================================
::  STEP 3 / 4  -  Build Traceability Matrix (VTM)
:: ============================================================

echo [3/4] Building Validation Traceability Matrix...
echo ------------------------------------------------------------
python "%PROJECT_ROOT%\scripts\generate_vtm.py"
if errorlevel 1 (
    echo.
    echo [ERROR] VTM generation failed.
    exit /b 1
)
echo.

:: ============================================================
::  STEP 4 / 4  -  Generate Validation Summary Report (VSR)
:: ============================================================

echo [4/4] Generating Validation Summary Report...
echo ------------------------------------------------------------
python "%PROJECT_ROOT%\scripts\draft_vsr.py"
if errorlevel 1 (
    echo.
    echo [ERROR] VSR generation failed.
    exit /b 1
)
echo.

:: ============================================================
::  Done
:: ============================================================

echo ============================================================
echo   VALIDATION PACKAGE COMPLETE
echo ============================================================
echo.
echo   Outputs:
echo     URS documents:      %PROJECT_ROOT%\output\urs\
echo     Traceability Matrix: %PROJECT_ROOT%\output\EVOLV_Traceability_Matrix.csv
echo     Health Report:       %PROJECT_ROOT%\output\EVOLV_Health_Report.txt
echo     Summary Report:      %PROJECT_ROOT%\output\vsr\
echo.
echo   Powered by EVOLV | A WingstarTech Inc. Product
echo ============================================================
echo.

endlocal
exit /b 0
