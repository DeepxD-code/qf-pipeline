@echo off
REM Build the pure-JDK renderer (no Maven/Gradle needed).
cd /d %~dp0
if not exist classes mkdir classes
javac -d classes src\Compose.java
if errorlevel 1 exit /b 1
echo Built workers\java-renderer\classes\Compose.class
java -cp classes Compose 2>&1 | findstr usage >nul
