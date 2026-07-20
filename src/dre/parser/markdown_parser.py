"""Markdown → AST 解析器。

基于 python-markdown-it-py 将 CommonMark 文本转换为 DRE 内部 AST。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock
from markdown_it.token import Token

from dre.ast.nodes import (
    BlockQuote,
    BulletList,
    CodeBlock,
    Document,
    DocumentNode,
    Heading,
    Image,
    OrderedList,
    Paragraph,
    Table,
    TableOfContents,
    TextRun,
)


# ---------------------------------------------------------------------------
#  Markdown-it 配置
# ---------------------------------------------------------------------------

def _create_md() -> MarkdownIt:
    """Create a MarkdownIt instance with sensible defaults for DRE."""
    md = (
        MarkdownIt("commonmark", {"breaks": False, "html": False})
        .enable("table")
        .enable("strikethrough")
    )
    return md


# ---------------------------------------------------------------------------
#  Token → AST 转换
# ---------------------------------------------------------------------------

class MarkdownParser:
    """Parse Markdown text into a Document AST."""

    def __init__(self):
        self._md = _create_md()
        self._tokens: list[Token] = []
        self._idx: int = 0  # current token index

    # ---- Public API -------------------------------------------------------

    def parse(self, text: str) -> Document:
        """Parse *text* and return the root Document node."""
        if not text or not text.strip():
            return Document(title=None, children=[])

        self._tokens = self._md.parse(text)
        self._idx = 0

        doc = Document()
        # 首行如果是 # 标题则提取为文档标题
        first_heading = self._peek_heading()
        if first_heading is not None and first_heading.level == 1:
            doc.title = first_heading.text
            # 跳过已经提取的 H1
            self._advance_past_heading()

        while self._idx < len(self._tokens):
            node = self._parse_block()
            if node is not None:
                doc.add_child(node)

        return doc

    def parse_file(self, path: str | Path) -> Document:
        """Read a Markdown file and parse it into a Document AST."""
        text = Path(path).read_text(encoding="utf-8")
        return self.parse(text)

    # ---- Block-level parsing ----------------------------------------------

    def _parse_block(self) -> Optional[DocumentNode]:
        """Parse the next block-level token and return an AST node."""
        token = self._peek()
        if token is None:
            return None

        # [TOC] placeholder
        if token.type == "inline" and token.content.strip() == "[TOC]":
            self._advance()
            return TableOfContents()

        dispatch = {
            "heading_open": self._parse_heading,
            "paragraph_open": self._parse_paragraph,
            "bullet_list_open": self._parse_bullet_list,
            "ordered_list_open": self._parse_ordered_list,
            "table_open": self._parse_table,
            "fence": self._parse_fence,
            "code_block": self._parse_fence,  # indented code block
            "blockquote_open": self._parse_blockquote,
            "hr": self._parse_hr,
        }
        handler = dispatch.get(token.type)
        if handler is not None:
            return handler()

        # Skip unhandled tokens
        self._advance()
        return None

    def _parse_heading(self) -> Heading:
        open_token = self._advance()  # heading_open
        level = int(open_token.tag[1])  # "h1" → 1
        inline_token = self._advance()  # inline
        self._advance()  # heading_close
        text = inline_token.content.strip()
        return Heading(level=level, text=text)

    def _parse_paragraph(self) -> Paragraph:
        self._advance()  # paragraph_open
        inline_token = self._advance()  # inline
        self._advance()  # paragraph_close

        para = Paragraph(text=inline_token.content)
        # Process inline tokens
        para.children = self._parse_inline(inline_token)
        return para

    def _parse_bullet_list(self) -> BulletList:
        bl = BulletList(items=[])
        # 消耗 bullet_list_open
        open_token = self._advance()  # bullet_list_open
        tight = open_token.meta.get("tight", True) if open_token.meta else True

        while self._idx < len(self._tokens):
            token = self._peek()
            if token is None or token.type == "bullet_list_close":
                break
            item = self._parse_list_item()
            if item is not None:
                bl.items.append(item)

        self._advance()  # bullet_list_close
        return bl

    def _parse_ordered_list(self) -> OrderedList:
        ol = OrderedList(items=[])
        open_token = self._advance()  # ordered_list_open
        ol.start = int(open_token.attrs.get("start", 1)) if open_token.attrs else 1

        while self._idx < len(self._tokens):
            token = self._peek()
            if token is None or token.type == "ordered_list_close":
                break
            item = self._parse_list_item()
            if item is not None:
                ol.items.append(item)

        self._advance()  # ordered_list_close
        return ol

    def _parse_list_item(self) -> Optional[list[DocumentNode]]:
        """Parse a single list item (li_open ... li_close)."""
        token = self._peek()
        if token is None or token.type != "list_item_open":
            return None

        self._advance()  # list_item_open
        children: list[DocumentNode] = []

        while self._idx < len(self._tokens):
            token = self._peek()
            if token is None or token.type == "list_item_close":
                break

            # 递归解析嵌套列表
            if token.type in ("bullet_list_open", "ordered_list_open"):
                child = self._parse_block()
                if child is not None:
                    children.append(child)
            else:
                # 列表项内的段落
                child = self._parse_block()
                if child is not None:
                    children.append(child)

        self._advance()  # list_item_close
        return children if children else None

    def _parse_table(self) -> Table:
        tbl = Table(headers=[], rows=[])
        self._advance()  # table_open

        # thead
        self._advance()  # thead_open
        self._advance()  # tr_open
        while self._idx < len(self._tokens):
            token = self._peek()
            if token is None or token.type == "thead_close":
                break
            if token.type == "inline":
                tbl.headers.append(token.content.strip())
            self._advance()
        if self._peek() and self._peek().type == "thead_close":
            self._advance()  # thead_close

        # tbody
        if self._peek() and self._peek().type == "tbody_open":
            self._advance()  # tbody_open
        while self._idx < len(self._tokens):
            token = self._peek()
            if token is None or token.type in ("tbody_close", "table_close"):
                break
            if token.type == "tr_open":
                row: list[str] = []
                self._advance()  # tr_open
                while self._idx < len(self._tokens):
                    token = self._peek()
                    if token is None or token.type == "tr_close":
                        break
                    if token.type == "inline":
                        row.append(token.content.strip())
                    self._advance()
                if self._peek() and self._peek().type == "tr_close":
                    self._advance()  # tr_close
                if row:
                    tbl.rows.append(row)
            else:
                self._advance()

        self._advance()  # table_close
        return tbl

    def _parse_fence(self) -> CodeBlock:
        token = self._advance()  # fence or code_block
        info = token.info.strip() if token.info else ""
        lang = info.split()[0] if info else None
        return CodeBlock(language=lang, code=token.content)

    def _parse_blockquote(self) -> BlockQuote:
        self._advance()  # blockquote_open
        text_parts: list[str] = []
        while self._idx < len(self._tokens):
            token = self._peek()
            if token is None or token.type == "blockquote_close":
                break
            if token.type == "inline":
                text_parts.append(token.content)
            self._advance()
        self._advance()  # blockquote_close
        return BlockQuote(text="\n".join(text_parts))

    def _parse_hr(self) -> Optional[DocumentNode]:
        self._advance()  # hr
        return None  # horizontal rules are skipped in the AST

    # ---- Inline parsing ---------------------------------------------------

    def _parse_inline(self, token: Token) -> list[TextRun]:
        """Parse inline content from a token's ``children`` if available.

        Falls back to a single plain TextRun when there are no inline tokens.
        """
        children = token.children
        if not children:
            text = token.content
            return [TextRun(text=text)] if text else []

        runs: list[TextRun] = []
        current = TextRun()
        for child in children:
            if child.type == "text":
                current.append(child.content)
            elif child.type == "softbreak":
                current.append("\n")
            elif child.type == "hardbreak":
                current.append("\n")
            elif child.type == "code_inline":
                if current:
                    runs.append(current)
                runs.append(TextRun(text=child.content, code=True))
                current = TextRun()
            elif child.type == "link_open":
                href = child.attrs.get("href", "") if child.attrs else ""
                # Push current, start new run with link
                if current:
                    runs.append(current)
                current = TextRun(link=href)
            elif child.type == "link_close":
                if current:
                    runs.append(current)
                current = TextRun()
            elif child.type == "strong_open":
                if current:
                    runs.append(current)
                current = TextRun(bold=True)
            elif child.type == "strong_close":
                if current:
                    runs.append(current)
                current = TextRun()
            elif child.type == "em_open":
                if current:
                    runs.append(current)
                current = TextRun(italic=True)
            elif child.type == "em_close":
                if current:
                    runs.append(current)
                current = TextRun()
            elif child.type == "image":
                if current:
                    runs.append(current)
                # Images inside paragraph — we handle these in the inline
                # stream as special runs
                alt = child.content or ""
                src = child.attrs.get("src", "") if child.attrs else ""
                runs.append(TextRun(text=f"![{alt}]({src})", code=False))
                current = TextRun()
            else:
                # Unknown inline token — try to get its content
                current.append(str(child.content or ""))

        if current:
            runs.append(current)

        return [r for r in runs if r]

    # ---- Token stream helpers ---------------------------------------------

    def _peek(self) -> Optional[Token]:
        if self._idx < len(self._tokens):
            return self._tokens[self._idx]
        return None

    def _advance(self) -> Optional[Token]:
        token = self._peek()
        self._idx += 1
        return token

    def _peek_heading(self) -> Optional[Heading]:
        """Look at the first token and return a Heading if it's H1."""
        saved = self._idx
        try:
            token = self._peek()
            if token and token.type == "heading_open" and token.tag == "h1":
                level = int(token.tag[1])
                self._advance()
                inline = self._advance()
                self._advance()
                text = inline.content.strip() if inline else ""
                return Heading(level=level, text=text)
            return None
        finally:
            self._idx = saved

    def _advance_past_heading(self) -> None:
        """Consume the first heading tokens (3 tokens: open, inline, close)."""
        for _ in range(3):
            self._advance()
