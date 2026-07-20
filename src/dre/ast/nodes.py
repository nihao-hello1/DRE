"""Document AST node definitions.

All document elements inherit from DocumentNode to form a tree structure
rooted at a Document node.  Inline formatting is captured inside Paragraph
via on-the-fly TextRun building during parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
#  Node base
# ---------------------------------------------------------------------------

class DocumentNode:
    """Mixin that provides accept(visitor) for every subclass automatically.

    Subclasses are expected to be frozen / slot-based dataclasses; this mixin
    adds the visitor dispatch without requiring each node type to define it.
    """

    node_type: str = ""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Derive snake_case type name from the class name
        name = cls.__name__
        cls.node_type = "".join(
            f"_{c.lower()}" if c.isupper() else c for c in name
        ).lstrip("_")

    def accept(self, visitor: "NodeVisitor") -> None:
        """Dispatch to visitor.visit_<node_type>(self)."""
        method_name = f"visit_{self.node_type}"
        method = getattr(visitor, method_name, None)
        if method is not None:
            method(self)


class NodeVisitor:
    """Base visitor — provides a default fallback for each node type.

    Override visit_<node_type>() in subclasses to handle specific nodes.
    """

    def visit(self, node: DocumentNode) -> None:
        """Convenience: call node.accept(self)."""
        node.accept(self)

    def visit_document(self, node: "Document") -> None:
        """Override in subclass."""

    def visit_heading(self, node: "Heading") -> None:
        self.visit_paragraph(node)

    def visit_paragraph(self, node: "Paragraph") -> None:
        pass

    def visit_text_run(self, node: "TextRun") -> None:
        pass

    def visit_bullet_list(self, node: "BulletList") -> None:
        pass

    def visit_ordered_list(self, node: "OrderedList") -> None:
        pass

    def visit_table(self, node: "Table") -> None:
        pass

    def visit_image(self, node: "Image") -> None:
        pass

    def visit_code_block(self, node: "CodeBlock") -> None:
        pass

    def visit_block_quote(self, node: "BlockQuote") -> None:
        pass

    def visit_table_of_contents(self, node: "TableOfContents") -> None:
        pass


# ===================================================================
#  Inline nodes  (children of Paragraph)
# ===================================================================

@dataclass
class TextRun(DocumentNode):
    """A contiguous span of formatted text inside a paragraph."""

    text: str = ""
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: Optional[str] = None

    def __bool__(self) -> bool:
        """Empty runs are falsy — convenient for filtering."""
        return bool(self.text)

    def __iadd__(self, other: str) -> "TextRun":
        self.text += other
        return self

    def append(self, text: str) -> None:
        self.text += text


# ===================================================================
#  Block-level nodes  (children of Document / ListItem)
# ===================================================================

@dataclass
class Heading(DocumentNode):
    """Section heading (level 1-6)."""

    level: int = 1
    text: str = ""
    numbering: Optional[str] = None  # assigned by style engine later


@dataclass
class Paragraph(DocumentNode):
    """Body paragraph with zero or more TextRun children."""

    text: str = ""
    children: list[TextRun] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.text and not self.children


@dataclass
class BulletList(DocumentNode):
    """Unordered list."""

    items: list[list[DocumentNode]] = field(default_factory=list)


@dataclass
class OrderedList(DocumentNode):
    """Ordered (numbered) list."""

    items: list[list[DocumentNode]] = field(default_factory=list)
    start: int = 1


@dataclass
class Table(DocumentNode):
    """Markdown table."""

    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    caption: Optional[str] = None

    @property
    def column_count(self) -> int:
        cols = len(self.headers)
        if cols:
            return cols
        for row in self.rows:
            cols = max(cols, len(row))
        return cols


@dataclass
class Image(DocumentNode):
    """Embedded image."""

    alt_text: str = ""
    source: str = ""  # file path or URL
    caption: Optional[str] = None
    width: Optional[int] = None  # px
    height: Optional[int] = None


@dataclass
class CodeBlock(DocumentNode):
    """Fenced code block."""

    language: Optional[str] = None
    code: str = ""
    caption: Optional[str] = None


@dataclass
class BlockQuote(DocumentNode):
    """Block quotation."""

    text: str = ""


@dataclass
class TableOfContents(DocumentNode):
    """Placeholder for the table of contents.

    The renderer will insert a TOC field code at this position.
    """

    title: str = "目  录"
    max_level: int = 3


# ===================================================================
#  Top-level container
# ===================================================================

@dataclass
class Document(DocumentNode):
    """Root of the document AST."""

    title: Optional[str] = None
    children: list[DocumentNode] = field(default_factory=list)

    def add_child(self, node: DocumentNode) -> None:
        self.children.append(node)

    def walk(self) -> list[DocumentNode]:
        """Flatten the tree in document order (DFS)."""
        result: list[DocumentNode] = []

        def _dfs(nodes: list[DocumentNode]) -> None:
            for child in nodes:
                result.append(child)
                if isinstance(child, (BulletList, OrderedList)):
                    for item in child.items:
                        _dfs(item)
                if isinstance(child, Document):
                    _dfs(child.children)

        _dfs(self.children)
        return result

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict (for debugging)."""
        return _node_to_dict(self)


# ---------------------------------------------------------------------------
#  Serialization helper
# ---------------------------------------------------------------------------

def _node_to_dict(node: DocumentNode) -> dict:
    """Convert a DocumentNode tree to nested dicts."""
    d = {"type": node.node_type}

    if isinstance(node, Document):
        d["title"] = node.title
        d["children"] = [_node_to_dict(c) for c in node.children]

    elif isinstance(node, Heading):
        d["level"] = node.level
        d["text"] = node.text

    elif isinstance(node, Paragraph):
        d["text"] = node.text
        d["children"] = [_node_to_dict(c) for c in node.children]

    elif isinstance(node, TextRun):
        d["text"] = node.text
        d["bold"] = node.bold
        d["italic"] = node.italic
        d["code"] = node.code
        d["link"] = node.link

    elif isinstance(node, BulletList):
        d["items"] = [[_node_to_dict(c) for c in item] for item in node.items]

    elif isinstance(node, OrderedList):
        d["items"] = [[_node_to_dict(c) for c in item] for item in node.items]
        d["start"] = node.start

    elif isinstance(node, Table):
        d["headers"] = node.headers
        d["rows"] = node.rows
        d["caption"] = node.caption

    elif isinstance(node, Image):
        d["alt_text"] = node.alt_text
        d["source"] = node.source
        d["caption"] = node.caption

    elif isinstance(node, CodeBlock):
        d["language"] = node.language
        d["code"] = node.code

    elif isinstance(node, BlockQuote):
        d["text"] = node.text

    elif isinstance(node, TableOfContents):
        d["title"] = node.title
        d["max_level"] = node.max_level

    return d
