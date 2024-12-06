import os
import pytest
from content_splitter.split_content import (
    HTMLFragmentManager,
    split_html_content,
    split_text_content,
    split_content,
    main,
)
from click.testing import CliRunner


# Test fixtures
@pytest.fixture
def sample_html():
    return """
    <div class="content">
        <h1>Title</h1>
        <p>First paragraph with some text.</p>
        <p>Second paragraph with <b>bold text</b> and more content.</p>
    </div>
    """


@pytest.fixture
def sample_text():
    return """
    First sentence goes here. Second sentence is longer.
    Third sentence completes the paragraph! Next sentence starts.
    Final sentence ends with a question?
    """


def test_handle_closing_tag():

    manager = HTMLFragmentManager(100)

    # Test with empty stack

    manager.handle_closing_tag("div")

    # Test with non-matching tag

    manager.stack = ["div"]

    manager.saved_tags = [("<div>", "div")]

    manager.handle_closing_tag("span")

    # Test with matching tag

    manager.handle_closing_tag("div")


def test_handle_closing_tag_with_empty_stack():
    manager = HTMLFragmentManager(100)
    manager.handle_closing_tag("div")
    assert manager.stack == []
    assert manager.saved_tags == []


def test_handle_opening_tag():

    manager = HTMLFragmentManager(100)

    # Test with empty stack

    manager.handle_opening_tag("<div>", "div")

    assert manager.stack == ["div"]

    assert manager.saved_tags == [("<div>", "div")]

    # Test with non-matching tag

    manager.handle_opening_tag("<span>", "span")

    assert manager.stack == ["div", "span"]

    assert manager.saved_tags == [("<div>", "div"), ("<span>", "span")]

    # Test with matching tag

    manager.handle_opening_tag("<div>", "div")

    assert manager.stack == ["div", "span", "div"]

    assert manager.saved_tags == [
        ("<div>", "div"),
        ("<span>", "span"),
        ("<div>", "div"),
    ]


# HTMLFragmentManager tests
def test_html_fragment_manager_initialization():
    fm = HTMLFragmentManager(max_length=100)
    assert fm.max_length == 100
    assert fm.stack == []
    assert fm.current_fragment == []
    assert fm.current_length == 0


def test_html_fragment_manager_tag_hierarchy():
    fm = HTMLFragmentManager(max_length=100)
    fm.handle_opening_tag("<div>", "div")
    fm.handle_opening_tag("<p>", "p")

    opening, closing = fm.get_tag_hierarchy()
    assert opening == "<div><p>"
    assert closing == "</p></div>"


def test_html_fragment_manager_content_limit():
    fm = HTMLFragmentManager(max_length=20)
    assert fm.would_exceed_limit("x" * 21)
    assert not fm.would_exceed_limit("x" * 19)


def test_html_fragment_manager_create_empty_fragment():
    fm = HTMLFragmentManager(max_length=100)
    assert fm.create_fragment() == ""


def test_html_fragment_manager_create_fragment():
    fm = HTMLFragmentManager(max_length=100)
    fm.handle_opening_tag("<div>", "div")
    fm.current_fragment.append("<div>")  # Add opening tag to current_fragment
    fm.add_content("test")
    assert fm.create_fragment() == "<div>test</div>"


def test_html_fragment_manager_handle_closing_tag():
    fm = HTMLFragmentManager(max_length=100)
    fm.handle_opening_tag("<div>", "div")
    fm.handle_opening_tag("<p>", "p")
    fm.handle_closing_tag("p")
    opening, closing = fm.get_tag_hierarchy()
    assert opening == "<div>"
    assert closing == "</div>"


# split_html_content tests
def test_split_html_content_basic(sample_html):
    fragments = list(split_html_content(sample_html, max_length=50))
    assert len(fragments) > 1
    assert all(
        "<div" in f for f in fragments
    )  # All fragments preserve root tag
    assert all(
        "</div>" in f for f in fragments
    )  # All fragments close properly


def test_split_html_content_empty():
    fragments = list(split_html_content("", max_length=100))
    assert fragments == []


def test_split_html_content_empty_input():
    fragments = list(split_html_content("", max_length=100))
    assert fragments == []


def test_split_html_content_nested_tags():
    html = "<div><p><b>Bold</b> text</p></div>"
    fragments = list(split_html_content(html, max_length=20))
    assert all("<div" in f for f in fragments)
    assert all("</div>" in f for f in fragments)


def test_split_html_content_invalid_html():
    html = "<div>test<"  # Invalid HTML with unclosed tag
    fragments = list(split_html_content(html, max_length=20))
    assert len(fragments) > 0


def test_split_html_content_self_closing_tags():
    html = """
    <div>
        <p>Test with self-closing tags</p>
        <br/>
        <img src="test.jpg" />
        <input type="text"/>
    </div>
    """
    fragments = list(split_html_content(html, max_length=50))
    assert len(fragments) > 0
    # Verify self-closing tags don't affect hierarchy
    assert all("<div" in f for f in fragments)
    assert all("</div>" in f for f in fragments)


# split_text_content tests
def test_split_text_content_basic(sample_text):
    fragments = list(split_text_content(sample_text, max_length=50))
    assert len(fragments) > 1
    assert all(len(f.encode("utf-8")) <= 50 for f in fragments)


def test_split_text_content_empty():
    fragments = list(split_text_content("", max_length=100))
    assert fragments == []


def test_split_text_content_single_sentence():
    text = "This is a single sentence."
    fragments = list(split_text_content(text, max_length=100))
    assert len(fragments) == 1
    assert fragments[0] == text.strip()


def test_split_text_content_long_sentence():
    text = (
        "This is a very long sentence that should be split into multiple "
        "fragments based on available space."
    )
    fragments = list(split_text_content(text, max_length=20))
    assert len(fragments) > 1
    assert all(len(f.encode("utf-8")) <= 20 for f in fragments)


# split_content tests
def test_split_content_html_content(sample_html):
    fragments = list(split_content(sample_html, max_length=50))
    assert len(fragments) > 1
    assert all("<div" in f for f in fragments)


def test_split_content_plain_text(sample_text):
    fragments = list(split_content(sample_text, max_length=50))
    assert len(fragments) > 1
    assert all("<" not in f for f in fragments)


def test_split_content_empty():
    fragments = list(split_content("", max_length=100))
    assert fragments == []


def test_split_content_invalid_bs4():
    # This should trigger the except clause in split_content
    with pytest.raises(TypeError):
        list(split_content({"invalid": "input"}, max_length=100))


# Edge cases and error handling
@pytest.mark.parametrize(
    "invalid_input",
    [
        None,
        0,
        [],
        {},
    ],
)
def test_split_content_invalid_input(invalid_input):
    with pytest.raises(TypeError):
        list(split_content(invalid_input, max_length=100))


def test_html_malformed_tags():
    malformed_html = "<div><p>Unclosed paragraph<div>More text</div>"
    fragments = list(split_html_content(malformed_html, max_length=50))
    assert len(fragments) > 0  # Should handle malformed HTML gracefully


def test_unicode_content():
    unicode_text = (
        "Hello 👋 World 🌍 with emoji 😊 "
        "in a very long text that should be split"
    )
    fragments = list(split_text_content(unicode_text, max_length=20))
    assert len(fragments) > 1
    assert all(len(f.encode("utf-8")) <= 20 for f in fragments)


def test_main():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main, ["--max-len", "20"], input="This is a test sentence."
        )
        assert result.exit_code == 0
        assert "fragment #1" in result.output
        assert os.path.exists("fragments")
        assert os.path.exists("fragments/fragment_text_1.txt")


def test_main_html():
    runner = CliRunner()
    with runner.isolated_filesystem():
        html_input = "<div><p>This is a test</p></div>"
        result = runner.invoke(main, ["--max-len", "20"], input=html_input)
        assert result.exit_code == 0
        assert "fragment #1" in result.output
        assert os.path.exists("fragments")
        assert os.path.exists("fragments/fragment_html_1.html")


def test_main_with_file(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test sentence.")

        result = runner.invoke(main, ["--max-len", "20", str(test_file)])
        assert result.exit_code == 0
        assert "fragment #1" in result.output
        assert os.path.exists("fragments")
