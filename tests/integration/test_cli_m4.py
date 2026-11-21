from __future__ import annotations

import json

from fabline.cli.main import main


def test_demo_and_human_bc_cli(tmp_path, capsys) -> None:
    demo_dir = tmp_path / "demos"
    assert (
        main(
            [
                "demo",
                "--episodes",
                "3",
                "--seed",
                "0",
                "--out",
                str(demo_dir),
            ]
        )
        == 0
    )
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["demos"] == 3
    assert manifest["success_rate"] == 1.0

    report_dir = tmp_path / "bc"
    assert (
        main(
            [
                "human-bc",
                "--dataset",
                str(demo_dir),
                "--out",
                str(report_dir),
                "--episodes",
                "2",
                "--seed",
                "0",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["metrics"]["success_rate"] == 1.0
    assert (report_dir / "report.md").exists()
    assert (report_dir / "results.json").exists()
