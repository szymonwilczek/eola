#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
"""Check the ABNF of the drafts against itself and the test vectors.

The ABNF blocks of a draft are loaded as one grammar; every rule they
reference is defined there or is a core rule of RFC 5234. When every
rule is defined, each vector of the draft is parsed with the grammar:
a vector whose result is "ok" matches the grammar; a vector with an
error code of a rule the grammar does not state, such as a size limit
or a range, the document type or key a receiver expects, the uniqueness
of a reserved field name, or the signature itself, is skipped; every
other vector does not match.
"""

import pathlib
import re
import sys

from abnf import Rule
from abnf.parser import ParseError

SPEC_DIRECTORY = pathlib.Path(__file__).resolve().parent
VECTORS_DIRECTORY = SPEC_DIRECTORY.parent / "vectors"

ABNF_BLOCK = re.compile(r"^~~~ abnf\n(.*?)^~~~$", re.MULTILINE | re.DOTALL)

# Each draft: the vector directory, the start rule of each check,
# and the error codes of rules the grammar does not state.
DRAFTS = {
    "draft-wilczek-eola-signed-document.md": {
        "vectors": "signed-document",
        "start_rules": {
            "document": "document",
            "hex": "hex-value",
            "decimal": "decimal-value",
            "verify": "signed-document",
        },
        "codes_outside_grammar": {
            "document_too_large",
            "line_too_long",
            "value_hex_length",
            "value_decimal_range",
            "document_type_unexpected",
            "signature_position",
            "signer_position",
            "signer_key_invalid",
            "signer_unexpected",
            "signature_invalid",
        },
    },
}


def load_grammar(draft_path):
    """Return the rules of the ABNF blocks of a draft."""
    text = draft_path.read_text()
    blocks = ABNF_BLOCK.findall(text)
    if not blocks:
        raise SystemExit(f"{draft_path.name}: no ABNF block")

    class Grammar(Rule):
        pass

    source = "".join(blocks)
    Grammar.load_grammar(source.replace("\n", "\r\n"))
    return Grammar


def undefined_rules(grammar):
    """Return the names of rules the grammar references but not defines."""
    return sorted(
        rule.name
        for rule in grammar.rules()
        if getattr(rule, "definition", None) is None
    )


def read_manifest(path):
    """Yield (file name, check, result) for each line of a manifest."""
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        file_name, check, result = line.split(" ")
        yield file_name, check, result


def matches(grammar, start_rule, content):
    """Return whether content matches the start rule of the grammar."""
    try:
        grammar.get(start_rule).parse_all(content.decode("latin-1"))
    except ParseError:
        return False
    return True


def check_draft(draft_name, settings):
    """Return the problems found in one draft and its vectors."""
    problems = []
    grammar = load_grammar(SPEC_DIRECTORY / draft_name)
    for name in undefined_rules(grammar):
        problems.append(f"{draft_name}: rule {name} is not defined")
    if problems:
        return problems

    vector_directory = VECTORS_DIRECTORY / settings["vectors"]
    manifest = vector_directory / "vectors.txt"
    for file_name, check, result in read_manifest(manifest):
        start_rule = settings["start_rules"].get(check.split(":")[0])
        if start_rule is None:
            continue
        content = (vector_directory / file_name).read_bytes()
        if result in settings["codes_outside_grammar"]:
            continue
        expected = result == "ok"
        if matches(grammar, start_rule, content) != expected:
            verb = "does not match" if expected else "matches"
            problems.append(
                f"{settings['vectors']}/{file_name} ({result}) {verb} "
                f"the rule {start_rule}"
            )
    return problems


def main():
    problems = []
    for draft_name, settings in DRAFTS.items():
        problems.extend(check_draft(draft_name, settings))
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
