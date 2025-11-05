#!/bin/bash
# Test script to verify that signal-mode works correctly

set -e

echo "====================================="
echo "Testing listen --signal-mode"
echo "====================================="
echo ""

# Cleanup function
cleanup() {
    if [ ! -z "$LISTEN_PID" ] && kill -0 $LISTEN_PID 2>/dev/null; then
        echo "Cleaning up: killing process $LISTEN_PID"
        kill -9 $LISTEN_PID 2>/dev/null || true
        wait $LISTEN_PID 2>/dev/null || true
    fi
    rm -f test_output.json
}

trap cleanup EXIT

echo "Step 1: Starting listen in signal mode..."
python3 listen.py --quiet --json --signal-mode -l es -m tiny > test_output.json 2>&1 &
LISTEN_PID=$!

echo "Process ID: $LISTEN_PID"
echo ""

# Wait for process to start
sleep 1

# Check if process is running
if ! kill -0 $LISTEN_PID 2>/dev/null; then
    echo "❌ FAIL: Process died immediately"
    exit 1
fi

echo "✓ Process started successfully"
echo ""

echo "Step 2: Recording for 3 seconds..."
echo "(Please speak something in Spanish during this time)"
sleep 3

echo ""
echo "Step 3: Sending SIGUSR1 to stop recording..."
kill -USR1 $LISTEN_PID

echo "Waiting for process to terminate (max 10 seconds)..."

# Wait for process with timeout
WAIT_COUNT=0
while kill -0 $LISTEN_PID 2>/dev/null; do
    sleep 0.5
    WAIT_COUNT=$((WAIT_COUNT + 1))
    if [ $WAIT_COUNT -gt 20 ]; then
        echo "❌ FAIL: Process did not terminate after 10 seconds"
        echo "Process is still running with PID: $LISTEN_PID"
        ps -p $LISTEN_PID
        exit 1
    fi
done

echo "✓ Process terminated successfully"
echo ""

# Check exit code
wait $LISTEN_PID
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ FAIL: Process exited with code $EXIT_CODE"
    echo "Output:"
    cat test_output.json
    exit 1
fi

echo "✓ Exit code is 0"
echo ""

# Check if output file has content
if [ ! -s test_output.json ]; then
    echo "❌ FAIL: Output file is empty"
    exit 1
fi

echo "✓ Output file has content"
echo ""

# Try to parse JSON
if ! python3 -c "import json; json.load(open('test_output.json'))" 2>/dev/null; then
    echo "❌ FAIL: Output is not valid JSON"
    echo "Output:"
    cat test_output.json
    exit 1
fi

echo "✓ Output is valid JSON"
echo ""

echo "====================================="
echo "Output:"
echo "====================================="
cat test_output.json
echo ""
echo ""

echo "====================================="
echo "✅ ALL TESTS PASSED!"
echo "====================================="
echo ""
echo "Summary:"
echo "  - Process started correctly"
echo "  - Received SIGUSR1 signal"
echo "  - Process terminated cleanly"
echo "  - Exit code was 0"
echo "  - Output is valid JSON"
