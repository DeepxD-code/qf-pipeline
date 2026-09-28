#!/bin/sh
# Build the pure-JDK Java backend (no Maven/Gradle needed).
set -e
cd "$(dirname "$0")"
mkdir -p classes
javac -d classes src/qf/Json.java src/qf/Store.java src/qf/Script.java src/qf/Cards.java src/qf/QfServer.java
echo "Built workers/java-backend/classes/qf/QfServer.class"
