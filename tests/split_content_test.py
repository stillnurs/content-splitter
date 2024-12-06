import pytest
from content_splitter.split_content import (
    HTMLFragmentManager,
    split_html_content,
    split_text_content,
    split_content,
)


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


def test_split_html_content_invalid_length():
    fragments = list(split_html_content("<p>test</p>", max_length=0))
    assert fragments == []


def test_split_html_content_nested_tags():
    html = "<div><p><b>Bold</b> text</p></div>"
    fragments = list(split_html_content(html, max_length=20))
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
