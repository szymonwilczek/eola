# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
#
# kernel-doc directive: renders the /** ... */ comments of a C header.
#
#   .. kernel-doc:: libeola/include/eola/document.h
#      :identifiers: eola_document_parse eola_document_next_field
#
#   .. kernel-doc:: libeola/include/eola/document.h
#      :doc: Parsing a document
#
# With neither option every comment in the file is rendered. A path is
# relative to the repository root. A comment that does not parse,
# a parameter or member left undescribed or described but absent,
# and an identifier or DOC: title not found are build warnings.

import os
import re

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.util import logging
from sphinx.util.nodes import nested_parse_with_titles

logger = logging.getLogger(__name__)

HEAD = re.compile(
    r"^(?:(?P<kind>struct|union|enum|typedef)\s+)?"
    r"(?P<name>[A-Za-z_]\w*)(?P<call>\(\))?\s+-\s+(?P<summary>\S.*)$"
)
DOC = re.compile(r"^DOC:\s*(?P<title>\S.*)$")
PARAMETER = re.compile(r"^@(?P<name>\w+|\.\.\.):\s*(?P<description>.*)$")
SECTION = re.compile(
    r"^(?P<name>Return|Returns|Context|Note|Notes|Example|"
    r"Examples|Locking):\s*(?P<text>.*)$"
)
IDENTIFIER = re.compile(r"[A-Za-z_]\w*")
HIGHLIGHTS = [
    (re.compile(r"&(struct|union|enum)\s+(\w+)"), r":c:\1:`\2`"),
    (re.compile(r"(?<![\w`:@])(\w+)\(\)"), r":c:func:`\1()`"),
    (re.compile(r"(?<![\w`@])@(\w+|\.\.\.)"), r"``\1``"),
    (re.compile(r"(?<![\w`%])%([A-Za-z_]\w*)"), r"``\1``"),
]

DIRECTIVES = {
    "function": "c:function",
    "struct": "c:struct",
    "union": "c:union",
    "enum": "c:enum",
    "typedef": "c:type",
    "macro": "c:macro",
}

PARAMETER_TITLES = {
    "struct": "Members",
    "union": "Members",
    "enum": "Constants",
}


class Comment:
    """One kernel-doc comment and the declaration that follows it."""

    def __init__(self, path, line_number):
        self.path = path
        self.line_number = line_number
        self.kind = None
        self.name = None
        self.summary = ""
        self.parameters = []
        self.body = []
        self.declaration = ""


def comment_lines(lines, first_line_number):
    """Yield (line number, text) of one comment, its " * " prefix removed.

    A continuation written as " *<TAB>text" keeps its tab, so the parser
    tells it from the start of a new section.
    """
    for line_number, raw_line in enumerate(lines, first_line_number):
        text = raw_line.strip()
        if text.startswith("*/"):
            return
        if text == "*":
            text = ""
        elif text.startswith("* "):
            text = text[2:].rstrip()
        elif text.startswith("*\t"):
            text = text[1:].rstrip()
        yield line_number, text


def read_declaration(lines, index):
    """Return the text after a comment up to the end of its declaration."""
    collected, depth = [], 0
    while index < len(lines):
        line = lines[index].split("//", 1)[0]
        collected.append(line)
        index += 1
        if line.lstrip().startswith("#define"):
            while line.endswith("\\") and index < len(lines):
                line = lines[index]
                collected.append(line)
                index += 1
            break
        depth += line.count("{") - line.count("}")
        is_aggregate = any(
            keyword in collected[0] for keyword in ("struct", "union", "enum")
        )
        if depth > 0 and not is_aggregate:
            break
        if depth <= 0 and (
            ";" in line or ("{" in "".join(collected) and "}" in line)
        ):
            break
    return "\n".join(collected)


def parse(path):
    """Return the comments of a file and the problems found in it."""
    with open(path, encoding="utf-8") as source:
        lines = source.read().splitlines()
    comments, problems = [], []
    index = 0
    while index < len(lines):
        if lines[index].strip() != "/**":
            index += 1
            continue
        comment = Comment(path, index + 1)
        body = list(comment_lines(lines[index + 1 :], index + 2))
        end = index + 1 + len(body) + 1
        if not body:
            problems.append((index + 1, "empty kernel-doc comment"))
            index = end
            continue

        first_line = body[0][1]
        doc_match = DOC.match(first_line)
        head_match = HEAD.match(first_line)
        if doc_match:
            comment.kind = "doc"
            comment.name = doc_match.group("title")
        elif head_match:
            if head_match.group("kind"):
                comment.kind = head_match.group("kind")
            elif head_match.group("call"):
                comment.kind = "function"
            else:
                comment.kind = "macro"
            comment.name = head_match.group("name")
            comment.summary = head_match.group("summary")
        else:
            problems.append(
                (body[0][0], f"cannot parse kernel-doc head '{first_line}'")
            )
            index = end
            continue

        parameter = None
        for line_number, text in body[1:]:
            parameter_match = PARAMETER.match(text)
            if parameter_match and not comment.body:
                parameter = [
                    parameter_match.group("name"),
                    parameter_match.group("description"),
                    line_number,
                ]
                comment.parameters.append(parameter)
                continue
            continues_parameter = (
                parameter is not None
                and text
                and not comment.body
                and (text[0].isspace() or not SECTION.match(text))
            )
            if continues_parameter:
                parameter[1] += " " + text.strip()
                continue
            parameter = None
            comment.body.append((line_number, text))
        if comment.kind != "doc":
            comment.declaration = read_declaration(lines, end)
        comments.append(comment)
        index = end
    return comments, problems


def highlight(text):
    """Apply kernel-doc inline markup: @arg, %CONST, func(), &struct name."""
    parts = re.split(r"(``.*?``)", text)
    for index in range(0, len(parts), 2):
        for pattern, replacement in HIGHLIGHTS:
            parts[index] = pattern.sub(replacement, parts[index])
    return "".join(parts)


def prototype(comment):
    """Return the signature Sphinx renders for a function or macro."""
    declaration = comment.declaration
    if comment.kind == "function":
        declaration = declaration.split("{", 1)[0].split(";", 1)[0]
        declaration = re.sub(r"^\s*(static\s+)?(inline\s+)?", "", declaration)
    elif comment.kind == "macro" and declaration.lstrip().startswith("#define"):
        macro_match = re.match(r"\s*#define\s+(\w+(?:\([^)]*\))?)", declaration)
        return macro_match.group(1) if macro_match else comment.name
    return " ".join(declaration.split())


def split_top_level(text, separator=","):
    """Split text at separators outside parentheses and brackets."""
    parts, depth, current = [], 0, ""
    for character in text:
        depth += (character in "([") - (character in ")]")
        if character == separator and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += character
    parts.append(current)
    return [part.strip() for part in parts if part.strip()]


def declared_name(declarator):
    """Return the name a parameter or member declarator declares."""
    if declarator == "void":
        return None
    if declarator == "...":
        return "..."
    pointer_match = re.search(r"\(\s*\*\s*(\w+)\s*\)", declarator)
    if pointer_match:
        return pointer_match.group(1)
    declarator = re.sub(r"\[[^\]]*\]", "", declarator)
    names = IDENTIFIER.findall(declarator)
    return names[-1] if names else None


def enum_constants(comment):
    """Return the constants an enum declaration defines."""
    if "{" not in comment.declaration:
        return None
    inner = comment.declaration[
        comment.declaration.index("{") + 1 : comment.declaration.rindex("}")
    ]
    inner = re.sub(r"/\*.*?\*/", "", inner, flags=re.DOTALL)
    constants = {}
    for entry in split_top_level(inner):
        name = entry.split("=", 1)[0].strip()
        if name:
            constants[name] = name
    return constants


def struct_members(comment):
    """Return the members a struct or union declaration declares."""
    if "{" not in comment.declaration:
        return None
    inner = comment.declaration[
        comment.declaration.index("{") + 1 : comment.declaration.rindex("}")
    ]
    inner = re.sub(r"/\*.*?\*/", "", inner, flags=re.DOTALL)
    members = {}
    for member in split_top_level(inner, ";"):
        if member.startswith("#"):
            continue
        member = " ".join(member.split())
        declarators = split_top_level(member)
        base_type = ""
        if declarators:
            base_type = re.sub(r"[\s*]*\w+(\[[^\]]*\])?$", "", declarators[0])
        for position, declarator in enumerate(declarators):
            name = declared_name(declarator)
            if name:
                members[name] = (
                    declarator if position == 0 else f"{base_type} {declarator}"
                )
    return members


def declared(comment):
    """Return the parameter, member, or constant names a declaration has."""
    if comment.kind == "function":
        signature = prototype(comment)
        if "(" not in signature:
            return None
        inner = signature[signature.index("(") + 1 : signature.rindex(")")]
        return {
            declared_name(argument): argument
            for argument in split_top_level(inner)
            if declared_name(argument)
        }
    if comment.kind == "macro":
        macro_match = re.match(r"\s*#define\s+\w+\(([^)]*)\)", comment.declaration)
        if not macro_match:
            return None
        return {
            argument.strip(): argument.strip()
            for argument in macro_match.group(1).split(",")
            if argument.strip()
        }
    if comment.kind in ("struct", "union"):
        return struct_members(comment)
    if comment.kind == "enum":
        return enum_constants(comment)
    return None


def check(comment):
    """Return (line, message) for every parameter or member mismatch."""
    declared_names = declared(comment)
    if declared_names is None:
        return []
    what = {
        "struct": "member",
        "union": "member",
        "enum": "constant",
    }.get(comment.kind, "parameter")
    if comment.kind == "function":
        label = f"{comment.name}()"
    else:
        label = f"{comment.kind} {comment.name}"
    described = {
        name: line_number for name, _description, line_number in comment.parameters
    }
    problems = [
        (comment.line_number, f"{what} '{name}' not described in '{label}'")
        for name in declared_names
        if name not in described
    ]
    problems += [
        (line_number, f"excess {what} '{name}' described in '{label}'")
        for name, line_number in described.items()
        if name not in declared_names
    ]
    return problems


def render(comment, output, source_path):
    """Append the reStructuredText of one comment to output."""

    def add(text, line_number):
        output.append(text, source_path, line_number - 1)

    if comment.kind == "doc":
        for line_number, text in comment.body:
            add(highlight(text), line_number)
        add("", comment.line_number)
        return

    if comment.kind in ("function", "macro"):
        signature = prototype(comment)
    else:
        signature = comment.name
    add(f".. {DIRECTIVES[comment.kind]}:: {signature}", comment.line_number)
    add("", comment.line_number)
    add(f"   {highlight(comment.summary)}", comment.line_number)
    add("", comment.line_number)

    declared_names = declared(comment) or {}
    if comment.parameters:
        title = PARAMETER_TITLES.get(comment.kind, "Parameters")
        add(f"   **{title}**", comment.line_number)
        add("", comment.line_number)
        for name, description, line_number in comment.parameters:
            add(f"   ``{declared_names.get(name, name)}``", line_number)
            add(f"     {highlight(description) or '*undescribed*'}", line_number)
            add("", line_number)

    for line_number, text in comment.body:
        section_match = SECTION.match(text)
        if section_match:
            add(f"   **{section_match.group('name')}**", line_number)
            add("", line_number)
            text = section_match.group("text")
            if not text:
                continue
        add(f"   {highlight(text)}" if text else "", line_number)
    add("", comment.line_number)


class KernelDoc(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False
    option_spec = {
        "identifiers": directives.unchanged,
        "doc": directives.unchanged_required,
    }

    def run(self):
        environment = self.state.document.settings.env
        relative_path = self.arguments[0]
        path = os.path.join(environment.config.kerneldoc_srctree, relative_path)
        location = "%s:%s" % self.state_machine.get_source_and_line(self.lineno)
        if not os.path.isfile(path):
            logger.warning(
                f"kernel-doc: no such file {relative_path}", location=location
            )
            return []
        environment.note_dependency(os.path.abspath(path))

        comments, problems = parse(path)
        for line_number, message in problems:
            logger.warning(
                f"kernel-doc: {message}", location=f"{path}:{line_number}"
            )

        wanted = None
        if "identifiers" in self.options:
            wanted = self.options["identifiers"].split() or None
        title = self.options.get("doc")
        if title is not None:
            picked = [
                comment
                for comment in comments
                if comment.kind == "doc" and comment.name == title
            ]
            if not picked:
                logger.warning(
                    f"kernel-doc: no 'DOC: {title}' in {relative_path}",
                    location=location,
                )
        elif wanted:
            by_name = {
                comment.name: comment for comment in comments if comment.kind != "doc"
            }
            picked = []
            for name in wanted:
                if name in by_name:
                    picked.append(by_name[name])
                else:
                    logger.warning(
                        f"kernel-doc: no comment for '{name}' in {relative_path}",
                        location=location,
                    )
        else:
            picked = [comment for comment in comments if comment.kind != "doc"]

        output = ViewList()
        for comment in picked:
            for line_number, message in check(comment):
                logger.warning(
                    f"kernel-doc: {message}", location=f"{path}:{line_number}"
                )
            render(comment, output, path)

        section = nodes.section()
        section.document = self.state.document
        nested_parse_with_titles(self.state, output, section)
        return section.children


def setup(app):
    app.add_config_value(
        "kerneldoc_srctree",
        os.path.abspath(os.path.join(app.confdir, "..")),
        "env",
    )
    app.add_directive("kernel-doc", KernelDoc)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
