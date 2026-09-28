@echo off
REM Build the pure-JDK Java backend (no Maven/Gradle needed).
cd /d %~dp0
if not exist classes mkdir classes
javac -d classes src\qf\Json.java src\qf\Store.java src\qf\Script.java src\qf\Cards.java src\qf\QfServer.java
if errorlevel 1 exit /b 1
echo Built workers\java-backend\classes\qf\QfServer.class
