from hub.cli import build_parser


def test_parser_has_record_ledger_and_web():
    parser = build_parser()
    assert parser.parse_args(["ledger"]).func.__name__ == "cmd_ledger"
    assert parser.parse_args(["record", "--change", "atr"]).func.__name__ == "cmd_record"
    assert parser.parse_args(["web"]).func.__name__ == "cmd_web"
