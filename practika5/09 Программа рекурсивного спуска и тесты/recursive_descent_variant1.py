#!/usr/bin/env python3
"""Рекурсивный спуск для практической работы № 5, вариант 1."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import re
import sys


TOKEN_RE = re.compile(
    r"(?P<WS>\s+)"
    r"|(?P<BIN>0[bB][01]+)"
    r"|(?P<OCT>0[oO][0-7]+)"
    r"|(?P<DEC>[0-9]+)"
    r"|(?P<ID>[A-Za-z]+)"
    r"|(?P<OP>[=;+\-*/()])"
)


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: int


class SyntaxErrorWithPosition(Exception):
    pass


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    position = 0
    while position < len(text):
        match = TOKEN_RE.match(text, position)
        if match is None:
            raise SyntaxErrorWithPosition(
                f"недопустимый символ {text[position]!r} в позиции {position}"
            )
        kind = match.lastgroup or ""
        value = match.group()
        if kind != "WS":
            if kind == "ID" and not 1 <= len(value) <= 2:
                raise SyntaxErrorWithPosition(
                    f"имя переменной {value!r} должно содержать 1–2 символа"
                )
            tokens.append(Token(kind, value, position))
        position = match.end()
    tokens.append(Token("EOF", "$", len(text)))
    return tokens


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.index]

    def accept_value(self, value: str) -> bool:
        if self.current.value == value:
            self.index += 1
            return True
        return False

    def expect_value(self, value: str) -> None:
        if not self.accept_value(value):
            self.fail(f"ожидался символ {value!r}")

    def expect_kind(self, kind: str) -> Token:
        if self.current.kind != kind:
            self.fail(f"ожидался токен {kind}")
        token = self.current
        self.index += 1
        return token

    def fail(self, message: str) -> None:
        token = self.current
        raise SyntaxErrorWithPosition(
            f"{message}, найдено {token.value!r} в позиции {token.position}"
        )

    def parse(self) -> None:
        self.program()
        self.expect_kind("EOF")

    # P -> A R; R -> ; A R | ε
    def program(self) -> None:
        self.assignment()
        while self.accept_value(";"):
            self.assignment()

    # A -> id = E
    def assignment(self) -> None:
        self.expect_kind("ID")
        self.expect_value("=")
        self.expression()

    # E -> T Q; Q -> + T Q | - T Q | ε
    def expression(self) -> None:
        self.term()
        while self.current.value in {"+", "-"}:
            self.index += 1
            self.term()

    # T -> U M; M -> * U M | / U M | ε
    def term(self) -> None:
        self.unary()
        while self.current.value in {"*", "/"}:
            self.index += 1
            self.unary()

    # U -> - U | F
    def unary(self) -> None:
        if self.accept_value("-"):
            self.unary()
        else:
            self.factor()

    # F -> ( E ) | id | bin | oct | dec
    def factor(self) -> None:
        if self.accept_value("("):
            self.expression()
            self.expect_value(")")
            return
        if self.current.kind in {"ID", "BIN", "OCT", "DEC"}:
            self.index += 1
            return
        self.fail("ожидались скобки, имя переменной или константа")


def recognize(text: str) -> tuple[bool, str]:
    try:
        Parser(tokenize(text)).parse()
        return True, "Accepted"
    except SyntaxErrorWithPosition as error:
        return False, f"Rejected: {error}"


TESTS = [
    ("a=0b101", True),
    ("ab=0o17+10", True),
    ("x=-0b1*(y+2)", True),
    ("a=1;b=0o7;c=a+b", True),
    ("zz=(0b10+0o3)/5", True),
    ("q=--10", True),
    ("abc=1", False),
    ("a=0b102", False),
    ("a=0o8", False),
    ("a=(1+2", False),
    ("a=1+", False),
    ("a=;b=2", False),
]


def self_test() -> int:
    failures = 0
    print("№\tЦепочка\tОжидалось\tРезультат")
    for number, (text, expected) in enumerate(TESTS, 1):
        accepted, message = recognize(text)
        status = "Accepted" if accepted else "Rejected"
        expected_status = "Accepted" if expected else "Rejected"
        ok = accepted == expected
        failures += int(not ok)
        print(f"{number}\t{text}\t{expected_status}\t{status}\t{'OK' if ok else 'FAIL'}")
        if not accepted:
            print(f"  {message}")
    print(f"\nИтог: {len(TESTS) - failures}/{len(TESTS)} тестов пройдено.")
    return 1 if failures else 0


def main() -> int:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("expression", nargs="?")
    argument_parser.add_argument("--self-test", action="store_true")
    args = argument_parser.parse_args()
    if args.self_test:
        return self_test()
    text = args.expression if args.expression is not None else sys.stdin.read().strip()
    accepted, message = recognize(text)
    print(message)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
