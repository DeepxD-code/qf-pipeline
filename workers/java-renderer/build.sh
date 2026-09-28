#!/bin/sh
# Build the pure-JDK renderer (no Maven/Gradle needed).
set -e
cd "$(dirname "$0")"
mkdir -p classes
javac -d classes src/Compose.java
echo "Built workers/java-renderer/classes/Compose.class"
