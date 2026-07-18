"""Bool and Int type keywords must type-check in expression position,
e.g. as components of a tuple-set field initializer like
``Set State = [Bool, Message, Message];``."""

from pathlib import Path

from proof_frog import frog_parser, semantic_analysis


def _check_primitive(tmp_path: Path, source: str) -> None:
    file_path = tmp_path / "Test.primitive"
    file_path.write_text(source)
    root = frog_parser.parse_file(str(file_path))
    semantic_analysis.check_well_formed(root, str(file_path))


def test_bool_in_tuple_set_field(tmp_path: Path) -> None:
    _check_primitive(
        tmp_path,
        """
        Primitive P(Set MessageSpace) {
            Set Message = MessageSpace;
            Set State = [Bool, Message, Message];

            State Wrap(Bool choice, Message m0, Message m1);
        }
        """,
    )


def test_int_in_tuple_set_field(tmp_path: Path) -> None:
    _check_primitive(
        tmp_path,
        """
        Primitive P(Set MessageSpace) {
            Set Message = MessageSpace;
            Set Counters = [Int, Message];

            Counters Wrap(Int n, Message m);
        }
        """,
    )
