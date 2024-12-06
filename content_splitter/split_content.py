import re
import click
import os
from bs4 import BeautifulSoup
from typing import Generator, List, Tuple


class HTMLFragmentManager:
    """Manages HTML fragment creation and tag hierarchy tracking"""

    def __init__(self, max_length: int):
        self.max_length = max_length
        self.stack: List[str] = []  # Track open tags
        self.saved_tags: List[Tuple[str, str]] = []  # Store (tag, name) pairs
        self.current_fragment: List[str] = []
        self.current_length: int = 0

    def get_tag_hierarchy(self) -> Tuple[str, str]:
        """Get opening and closing tags for current hierarchy"""
        opening_tags = "".join(tags[0] for tags in self.saved_tags)
        closing_tags = "".join(f"</{tag}>" for tag in reversed(self.stack))
        return opening_tags, closing_tags

    def would_exceed_limit(self, content: str) -> bool:
        """Check if adding content would exceed length limit"""
        _, closing_tags = self.get_tag_hierarchy()
        total_length = (
            self.current_length
            + len(content.encode("utf-8"))
            + len(closing_tags.encode("utf-8"))
        )
        return total_length > self.max_length

    def create_fragment(self) -> str:
        """Create and return current fragment with proper tag closure"""
        if not self.current_fragment:
            return ""
        _, closing_tags = self.get_tag_hierarchy()
        self.current_fragment.append(closing_tags)
        return "".join(self.current_fragment)

    def start_new_fragment(self) -> None:
        """Reset fragment with opening tags from stack"""
        opening_tags, _ = self.get_tag_hierarchy()
        self.current_fragment = [opening_tags]
        self.current_length = len(opening_tags.encode("utf-8"))

    def add_content(self, content: str) -> None:
        """Add content to current fragment and update length"""
        self.current_fragment.append(content)
        self.current_length += len(content.encode("utf-8"))

    def handle_closing_tag(self, tag_name: str) -> None:
        """Process a closing HTML tag"""
        if self.stack and self.stack[-1] == tag_name:
            self.stack.pop()
            if self.saved_tags:
                self.saved_tags.pop()

    def handle_opening_tag(self, full_tag: str, tag_name: str) -> None:
        """Process an opening HTML tag"""
        self.stack.append(tag_name)
        self.saved_tags.append((full_tag, tag_name))


def split_html_content(
    source: str, max_length: int
) -> Generator[str, None, None]:
    """Split HTML content into fragments while preserving tag hierarchy"""
    if not source or max_length <= 0:
        return

    fm = HTMLFragmentManager(max_length)
    pos = 0

    while pos < len(source):
        if source[pos] == "<":
            # Process HTML tag
            tag_end = source.find(">", pos)
            if tag_end == -1:
                break

            full_tag = source[pos : tag_end + 1]
            tag_content = full_tag[1:-1]
            pos = tag_end + 1

            # Handle fragment overflow
            if fm.would_exceed_limit(full_tag) and fm.current_fragment:
                yield fm.create_fragment()
                fm.start_new_fragment()

            # Process tag based on type
            if tag_content.startswith("/"):
                tag_name = tag_content.split()[0][1:]
                fm.handle_closing_tag(tag_name)
                fm.add_content(full_tag)
            else:
                tag_name = tag_content.split()[0]
                if not tag_content.endswith("/"):
                    fm.handle_opening_tag(full_tag, tag_name)
                fm.add_content(full_tag)

        else:
            # Process text content
            next_tag = source.find("<", pos)
            text = source[pos:] if next_tag == -1 else source[pos:next_tag]
            pos = len(source) if next_tag == -1 else next_tag

            if text.strip():
                if fm.would_exceed_limit(text) and fm.current_fragment:
                    yield fm.create_fragment()
                    fm.start_new_fragment()
                fm.add_content(text)

    if fm.current_fragment:
        yield fm.create_fragment()


def split_text_content(
    source: str, max_length: int
) -> Generator[str, None, None]:
    """Split plain text into fragments while preserving formatting."""
    if not source or max_length <= 0:
        return

    # Split on sentence boundaries first
    pattern = r"(?<=[.!?])\s+"
    sentences = [s.strip() for s in re.split(pattern, source) if s.strip()]

    current_fragment = []
    current_length = 0

    for sentence in sentences:
        # If single sentence exceeds max_length, split on word boundaries
        if len(sentence.encode("utf-8")) > max_length:
            words = sentence.split()
            word_fragment = []
            word_length = 0

            for word in words:
                word_size = len((word + " ").encode("utf-8"))
                if word_length + word_size > max_length:
                    if word_fragment:
                        yield " ".join(word_fragment).strip()
                    word_fragment = [word]
                    word_length = word_size
                else:
                    word_fragment.append(word)
                    word_length += word_size

            if word_fragment:
                yield " ".join(word_fragment).strip()
            continue

        # Normal sentence processing
        sentence_length = len(sentence.encode("utf-8"))
        if current_length + sentence_length > max_length:
            if current_fragment:
                yield " ".join(current_fragment).strip()
            current_fragment = [sentence]
            current_length = sentence_length
        else:
            current_fragment.append(sentence)
            current_length += sentence_length

    if current_fragment:
        yield " ".join(current_fragment).strip()


def split_content(source: str, max_length: int) -> Generator[str, None, None]:
    """Main function to split either HTML or plain text content."""
    if not isinstance(source, str):
        raise TypeError("Input must be a string")
    if not source or max_length <= 0:
        return

    try:
        if BeautifulSoup(source, "html.parser").find():
            yield from split_html_content(source, max_length)
        else:
            yield from split_text_content(source, max_length)
    except (AttributeError, TypeError) as e:
        raise TypeError("Invalid input format") from e


def main() -> None:
    """
    CLI entry point for splitting content content into fragments.
    """

    @click.command()
    @click.option(
        "--max-len",
        default=4096,
        help="Maximum fragment length. Default is 4096.",
    )
    @click.argument("file", type=click.File("r"), default="-")
    def cli(max_len: int, file: click.File) -> None:
        content = file.read()
        if not os.path.exists("fragments"):
            os.makedirs("fragments")
        for i, fragment in enumerate(split_content(content, max_len), 1):
            click.echo(f"fragment #{i}: {len(fragment)} chars.")
            click.echo("-" * 20)
            # write to file check if html or text
            if BeautifulSoup(content, "html.parser").find():
                with open(f"fragments/fragment_html_{i}.html", "w") as f:
                    f.write(fragment)
            else:
                with open(f"fragments/fragment_text_{i}.txt", "w") as f:
                    f.write(fragment)

    cli()


if __name__ == "__main__":
    main()
