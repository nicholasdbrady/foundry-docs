import subprocess

from scripts import download_docs


def test_download_file_skips_existing_without_force(monkeypatch, tmp_path):
    dest = tmp_path / "doc.md"
    dest.write_text("cached", encoding="utf-8")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called for cached files")

    monkeypatch.setattr(download_docs.subprocess, "run", fail_if_called)

    assert download_docs.download_file("articles/doc.md", dest) is True
    assert dest.read_text(encoding="utf-8") == "cached"


def test_download_file_force_replaces_existing_after_success(monkeypatch, tmp_path):
    dest = tmp_path / "doc.md"
    dest.write_text("cached", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        output_path = cmd[cmd.index("-o") + 1]
        with open(output_path, "w", encoding="utf-8") as output:
            output.write("fresh")
        return subprocess.CompletedProcess(cmd, 0, stdout="200", stderr="")

    monkeypatch.setattr(download_docs.subprocess, "run", fake_run)

    assert download_docs.download_file("articles/doc.md", dest, force=True) is True
    assert dest.read_text(encoding="utf-8") == "fresh"


def test_download_file_force_keeps_existing_after_failure(monkeypatch, tmp_path):
    dest = tmp_path / "doc.md"
    dest.write_text("cached", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        output_path = cmd[cmd.index("-o") + 1]
        with open(output_path, "w", encoding="utf-8") as output:
            output.write("not found")
        return subprocess.CompletedProcess(cmd, 0, stdout="404", stderr="")

    monkeypatch.setattr(download_docs.subprocess, "run", fake_run)

    assert download_docs.download_file("articles/doc.md", dest, force=True) is False
    assert dest.read_text(encoding="utf-8") == "cached"