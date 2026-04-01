from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_day7_docs_manifest_test() -> list[str]:
    required_paths = [
        ROOT / "docs" / "codebase_copilot_architecture.html",
        ROOT / "docs" / "codebase_copilot_architecture_explained.md",
        ROOT / "docs" / "codebase_copilot_flow.html",
        ROOT / "docs" / "codebase_copilot_flow_explained.md",
        ROOT / "docs" / "codebase_copilot_detailed_flow.html",
        ROOT / "docs" / "codebase_copilot_detailed_flow.md",
        ROOT / "docs" / "day7_sample_queries.md",
        ROOT / "docs" / "day7_project_highlights.md",
        ROOT / "docs" / "day7_resume_description.md",
        ROOT / "docs" / "day7_interview_talk.md",
    ]

    missing = [str(path) for path in required_paths if not path.exists()]
    assert not missing, f"Missing showcase documents: {missing}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_readme_tokens = [
        "codebase_copilot_architecture.html",
        "codebase_copilot_flow.html",
        "day7_project_highlights.md",
        "day7_resume_description.md",
        "day7_interview_talk.md",
        "scripts/day7_showcase_commands.ps1",
    ]
    for token in required_readme_tokens:
        assert token in readme, f"README is missing showcase reference: {token}"

    return [path.name for path in required_paths]


def test_day7_docs_manifest() -> None:
    run_day7_docs_manifest_test()


def main() -> int:
    validated = run_day7_docs_manifest_test()
    print("Day 7 docs manifest test passed.")
    for name in validated:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
