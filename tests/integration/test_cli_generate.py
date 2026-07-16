from lebanese_franco_factory.cli.main import main


def test_cli_generate_conversion(capsys) -> None:
    code = main(["generate", "--dataset", "arabic_to_franco", "--size", "5", "--seed", "3"])
    assert code == 0
    captured = capsys.readouterr().out
    assert "Wrote 5 examples" in captured
