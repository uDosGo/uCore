#!/bin/bash

# Optimized Workflow Quick Start Script
# This script helps you get started with the new TOON and Flow-LLM Router features

set -e

echo "=== uCore Optimized Workflow Quick Start ==="
echo

echo "1. Starting uCore backend..."
cd /Users/fredbook/Code/uCore/backend
python3 -m app &
PID=$!
echo "   Backend started with PID $PID"
echo

echo "2. Waiting for backend to start..."
sleep 3

echo "3. Verifying TOON Context Optimization..."
curl -s http://localhost:8484/api/toon/stats | jq -r '.status'
echo "   TOON server is ready"
echo

echo "4. Verifying Flow-LLM Router..."
curl -s -X POST http://localhost:8484/api/flow-router/route -H 'Content-Type: application/json' -d '{"task":"Test routing"}' | jq -r '.status'
echo "   Flow-LLM Router is ready"
echo

echo "5. Starting frontend..."
cd /Users/fredbook/Code/uCore/frontend
npm run dev &
FRONTEND_PID=$!
echo "   Frontend started with PID $FRONTEND_PID"
echo

echo "6. Opening Cline Kanban UI..."
open http://localhost:5173

echo

echo "=== Quick Start Complete! ==="
echo "- Backend: http://localhost:8484"
echo "- Frontend: http://localhost:5173"
echo "- Cline Kanban UI: http://localhost:5173"
echo "- TOON API: http://localhost:8484/api/toon/encode"
echo "- Flow-LLM Router API: http://localhost:8484/api/flow-router/route"
echo

echo "To stop the services, run:"
echo "  kill $PID $FRONTEND_PID"
echo

echo "For more information, see:"
echo "  docs/OPTIMIZED_WORKFLOW.md"
echo "  IMPLEMENTATION_SUMMARY.md"
echo "  OPTIMIZED_WORKFLOW_REPORT.md"
echo

echo "Enjoy the optimized workflow!"
