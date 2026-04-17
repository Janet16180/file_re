import gzip
import lzma
from pathlib import Path

import pytest

from file_re import file_re

ROOT = Path(__file__).parent


class TestMaxSpanLinesFeature:
    def test_basic_max_span_lines_functionality(self):
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"hi\nword", test_file, max_span_lines=2)

        assert match is not None
        assert match.group(0) == "hi\nword"

    def test_max_span_lines_with_groups(self):
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"(hi)\n(word)", test_file, max_span_lines=2)

        assert match is not None
        assert match.group(0) == "hi\nword"
        assert match.group(1) == "hi"
        assert match.group(2) == "word"

    def test_max_span_lines_with_named_groups(self):
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(
            r"(?P<greeting>hi)\n(?P<noun>word)", test_file, max_span_lines=2
        )

        assert match is not None
        assert match.group(0) == "hi\nword"
        assert match.group("greeting") == "hi"
        assert match.group("noun") == "word"
        assert match.groupdict() == {"greeting": "hi", "noun": "word"}

    def test_max_span_lines_no_match(self):
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(
            r"nonexistent\npattern", test_file, max_span_lines=2
        )

        assert match is None

    def test_max_span_lines_larger_than_file(self):
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"hi\nword", test_file, max_span_lines=10)

        assert match is not None
        assert match.group(0) == "hi\nword"

    def test_max_span_lines_equals_one(self):
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")

        match = file_re.search(r"some", test_file, max_span_lines=1)
        assert match is not None
        assert match.group(0) == "some"

        match = file_re.search(r"text\nhi", test_file, max_span_lines=1)
        assert match is None

    def test_findall_max_span_lines(self):
        test_file = Path(ROOT, "resources", "multiline_test_3.txt")

        matches = file_re.findall(r"hi\nworld", test_file, max_span_lines=2)

        assert len(matches) == 1
        assert matches[0] == "hi\nworld"

    def test_findall_max_span_lines_with_groups(self):
        test_file = Path(ROOT, "resources", "multiline_test_3.txt")

        matches = file_re.findall(r"(hi)\n(world)", test_file, max_span_lines=2)

        assert len(matches) == 1
        assert isinstance(matches[0], tuple)
        assert matches[0] == ("hi", "world")

    def test_max_span_lines_position_tracking(self):
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"hi\nword", test_file, max_span_lines=2)

        assert match is not None
        start_pos = match.start()
        end_pos = match.end()

        assert start_pos >= 0
        assert end_pos > start_pos
        assert (end_pos - start_pos) == len("hi\nword")

    def test_max_span_lines_compressed_files(self, tmp_path):
        src = Path(ROOT, "resources", "multiline_test_2.txt")
        content = src.read_bytes()

        gz_path = tmp_path / "multiline_test_2.txt.gz"
        with gzip.open(gz_path, "wb") as f:
            f.write(content)

        xz_path = tmp_path / "multiline_test_2.txt.xz"
        with lzma.open(xz_path, "wb") as f:
            f.write(content)

        for path in (gz_path, xz_path):
            match = file_re.search(r"hi\nword", path, max_span_lines=2)
            assert match is not None
            assert match.group(0) == "hi\nword"

            matches = file_re.findall(r"hi\nword", path, max_span_lines=2)
            assert matches == ["hi\nword"]

    def test_max_span_lines_invalid_values(self):
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        with pytest.raises(ValueError):
            file_re.search(r"hi", test_file, max_span_lines=0)
        with pytest.raises(ValueError):
            file_re.search(r"hi", test_file, max_span_lines=-5)
