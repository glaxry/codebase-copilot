$ErrorActionPreference = "Stop"

# Day 7 showcase script: keep the commands explicit so the project can be demoed
# step by step instead of hiding the workflow behind another custom wrapper.

$RepoRoot = Resolve-Path "."
$Metadata = Join-Path $RepoRoot "data\metadata.json"
$BenchmarkReport = Join-Path $RepoRoot "data\day7_demo_benchmark.md"

Write-Host "== Codebase Copilot Day 7 Showcase ==" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/5] Build metadata index" -ForegroundColor Yellow
python python/main.py index --repo $RepoRoot --output $Metadata
Write-Host ""

Write-Host "[2/5] Ask a grounded code question" -ForegroundColor Yellow
python python/main.py ask "Where is the application entry point?" --index $Metadata --answer-mode local --top-k 3
Write-Host ""

Write-Host "[3/5] Run the ReAct agent" -ForegroundColor Yellow
python python/main.py agent "Where is the application entry point?" --index $Metadata --answer-mode local --max-steps 4 --preview-lines 12
Write-Host ""

Write-Host "[4/5] Ask for a grounded patch suggestion" -ForegroundColor Yellow
python python/main.py patch "How should I add input validation to the login flow?" --index $Metadata --answer-mode local --top-k 4
Write-Host ""

Write-Host "[5/5] Run a compact benchmark" -ForegroundColor Yellow
python python/main.py benchmark --sizes 1000,10000 --dimension 64 --query-count 20 --top-k 5 --output $BenchmarkReport
Write-Host ""

Write-Host "Showcase completed." -ForegroundColor Green
Write-Host "Metadata: $Metadata"
Write-Host "Benchmark report: $BenchmarkReport"
