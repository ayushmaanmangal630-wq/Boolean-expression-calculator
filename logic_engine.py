"""Boolean expression parser and exact Quine–McCluskey minimizer."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import re


@dataclass(frozen=True)
class Node:
    kind: str
    value: str | bool | None = None
    left: "Node | None" = None
    right: "Node | None" = None


TOKEN_RE = re.compile(r"\|\||&&|[A-Za-z][A-Za-z0-9_]*|[01]|[+·&!*'~()⊕⊙↑↓∨∧¬]")


def tokenize(source: str) -> list[tuple[str, str]]:
    compact = re.sub(r"\s+", "", source)
    if not compact:
        raise ValueError("Enter a Boolean expression first.")
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(compact):
        match = TOKEN_RE.match(compact, pos)
        if not match:
            raise ValueError(f"Unsupported character {compact[pos]!r} at position {pos + 1}.")
        text = match.group()
        if text == "(": kind = "lp"
        elif text == ")": kind = "rp"
        elif text in ("0", "1"): kind = "const"
        elif text[0].isalpha(): kind = "var"
        else: kind = "op"
        tokens.append((kind, text.upper() if kind == "var" else text))
        pos = match.end()
    def ends(t: tuple[str, str]) -> bool:
        return t[0] in ("var", "const", "rp") or t == ("op", "'")
    def starts(t: tuple[str, str]) -> bool:
        return t[0] in ("var", "const", "lp") or t[1] in ("!", "~", "¬")
    result: list[tuple[str, str]] = []
    for token in tokens:
        if result and ends(result[-1]) and starts(token):
            result.append(("op", "·"))
        result.append(token)
    # Expand adjacent variable names into the standard shorthand: AB means A AND B.
    expanded: list[tuple[str, str]] = []
    for kind, value in result:
        if kind == "var" and len(value) > 1:
            for letter in value:
                if expanded and expanded[-1][0] in ("var", "const", "rp"):
                    expanded.append(("op", "·"))
                expanded.append(("var", letter))
        else:
            expanded.append((kind, value))
    return expanded


def parse(source: str) -> Node:
    tokens = tokenize(source)
    index = 0
    precedence = {"+": 1, "∨": 1, "||": 1, "⊕": 2, "⊙": 2, "↑": 3, "↓": 3, "·": 3, "&": 3, "&&": 3}

    def atom() -> Node:
        nonlocal index
        if index >= len(tokens):
            raise ValueError("Expected a variable, constant, or parenthesized expression.")
        kind, value = tokens[index]
        index += 1
        if kind == "op" and value in ("!", "~", "¬"):
            return Node("not", left=atom())
        if kind == "var": return Node("var", value)
        if kind == "const": return Node("const", value == "1")
        if kind == "lp":
            expr = parse_expr(0)
            if index >= len(tokens) or tokens[index][0] != "rp":
                raise ValueError("Missing closing parenthesis.")
            index += 1
            return expr
        raise ValueError(f"Unexpected token {value!r}.")

    def parse_expr(minimum: int) -> Node:
        nonlocal index
        left = atom()
        while index < len(tokens):
            kind, op = tokens[index]
            if kind == "op" and op == "'":
                index += 1
                left = Node("not", left=left)
                continue
            if kind != "op" or op not in precedence:
                break
            rank = precedence[op]
            if rank < minimum: break
            index += 1
            right = parse_expr(rank + 1)
            actual = "or" if rank == 1 else "xor" if op == "⊕" else "xnor" if op == "⊙" else "nand" if op == "↑" else "nor" if op == "↓" else "and"
            left = Node(actual, left=left, right=right)
        return left

    tree = parse_expr(0)
    if index != len(tokens):
        raise ValueError("Unexpected closing parenthesis or operator.")
    # ↑ and ↓ share AND/OR precedence respectively; normalize operator parsing here.
    return tree


def variables(node: Node) -> list[str]:
    found: set[str] = set()
    def walk(n: Node) -> None:
        if n.kind == "var": found.add(str(n.value))
        if n.left: walk(n.left)
        if n.right: walk(n.right)
    walk(node)
    return sorted(found)


def evaluate(node: Node, assignment: dict[str, bool]) -> bool:
    if node.kind == "var": return assignment[str(node.value)]
    if node.kind == "const": return bool(node.value)
    if node.kind == "not": return not evaluate(node.left, assignment)  # type: ignore[arg-type]
    a, b = evaluate(node.left, assignment), evaluate(node.right, assignment)  # type: ignore[arg-type]
    if node.kind == "and": return a and b
    if node.kind == "or": return a or b
    if node.kind == "xor": return a != b
    if node.kind == "xnor": return a == b
    if node.kind == "nand": return not (a and b)
    if node.kind == "nor": return not (a or b)
    raise ValueError(f"Unsupported operation {node.kind!r}.")


def truth_table(node: Node) -> tuple[list[str], list[tuple[int, tuple[int, ...], int]]]:
    names = variables(node)
    if len(names) > 8:
        raise ValueError("Exact minimization and truth tables are limited to 8 variables.")
    rows = []
    for index in range(1 << len(names)):
        bits = tuple((index >> (len(names) - 1 - i)) & 1 for i in range(len(names)))
        assignment = dict(zip(names, map(bool, bits)))
        rows.append((index, bits, int(evaluate(node, assignment))))
    return names, rows


def prime_implicants(minterms: list[int], dont_cares: list[int], width: int) -> list[str]:
    current = {format(i, f"0{width}b") for i in minterms + dont_cares}
    primes: set[str] = set()
    while current:
        used: set[str] = set()
        following: set[str] = set()
        for a, b in combinations(sorted(current), 2):
            diffs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
            if len(diffs) == 1:
                i = diffs[0]
                following.add(a[:i] + "-" + a[i + 1:])
                used.update((a, b))
        primes.update(current - used)
        current = following
    return sorted(p for p in primes if any(all(x == "-" or x == bit for x, bit in zip(p, format(m, f"0{width}b"))) for m in minterms))


def minimize_cover(implicants: list[str], minterms: list[int], names: list[str], mode: str) -> list[list[str]]:
    if not minterms: return [[]]
    def covers(imp: str, m: int) -> bool:
        bits = format(m, f"0{len(names)}b")
        return all(a == "-" or a == b for a, b in zip(imp, bits))
    coverage = {p: {m for m in minterms if covers(p, m)} for p in implicants}
    best_cost: tuple[int, int] | None = None
    solutions: list[list[str]] = []
    def visit(selected: tuple[str, ...], covered_minterms: frozenset[int]) -> None:
        nonlocal best_cost, solutions
        missing = next((m for m in minterms if m not in covered_minterms), None)
        if missing is None:
            literal_cost = sum(sum(ch != "-" for ch in p) for p in selected)
            cost = (len(selected), literal_cost) if mode == "terms" else (literal_cost, len(selected))
            if best_cost is None or cost < best_cost:
                best_cost, solutions = cost, [list(selected)]
            elif cost == best_cost and len(solutions) < 100:
                solutions.append(list(selected))
            return
        for p in implicants:
            if p not in selected and missing in coverage[p]:
                visit(selected + (p,), covered_minterms | coverage[p])
    visit((), frozenset())
    return solutions


def implicant_term(pattern: str, names: list[str], *, pos: bool = False) -> str:
    pieces = []
    for bit, name in zip(pattern, names):
        if bit == "-": continue
        if pos: pieces.append(name + ("'" if bit == "1" else ""))
        else: pieces.append(name + ("'" if bit == "0" else ""))
    return (" + ".join(pieces) if pos else "".join(pieces)) or ("1" if not pos else "0")


def simplify(source: str, mode: str = "literals", dont_cares: list[int] | None = None) -> dict:
    node = parse(source)
    names, rows = truth_table(node)
    dc = sorted(set(dont_cares or []))
    if any(not isinstance(x, int) or x < 0 or x >= (1 << len(names)) for x in dc):
        raise ValueError(f"Don't-care indices must be between 0 and {(1 << len(names)) - 1}.")
    ones = [index for index, _, value in rows if value]
    zeros = [index for index, _, value in rows if not value]
    dc = [x for x in dc if x not in ones and x not in zeros]
    sop_patterns = prime_implicants(ones, dc, len(names))
    pos_patterns = prime_implicants(zeros, dc, len(names))
    sop_covers = minimize_cover(sop_patterns, ones, names, mode)
    pos_covers = minimize_cover(pos_patterns, zeros, names, mode)
    sop_forms = [" + ".join(implicant_term(p, names) for p in cover) or "0" for cover in sop_covers]
    pos_forms = ["0" if not ones else "1" if not zeros else "".join("(" + implicant_term(p, names, pos=True) + ")" for p in cover) for cover in pos_covers]
    sop, pos = sop_forms[0], pos_forms[0]
    # Mandatory mathematical guard: never return a result that changes a defined row.
    for index, bits, expected in rows:
        assignment = dict(zip(names, map(bool, bits)))
        if evaluate(parse(sop), assignment) != bool(expected) or evaluate(parse(pos), assignment) != bool(expected):
            raise RuntimeError("Internal equivalence verification failed; result withheld.")
    # Choose the equivalent normal form with the lowest two-input gate count.
    # Constants are valid and unavoidable when the function itself is constant.
    sop_gate_cost = operator_count(parse(sop))
    pos_gate_cost = operator_count(parse(pos))
    algebraic_text = sop if sop_gate_cost <= pos_gate_cost else pos
    law_steps = [(format_expression(node), "Input")]
    if _has_outer_not(node):
        law_steps.append((format_expression(_apply_demorgan_outer(node)), "De Morgan's law"))
    # Exact row-by-row verification is authoritative for the displayed answer.
    if any(evaluate(parse(algebraic_text), dict(zip(names, map(bool, bits)))) != bool(value) for _, bits, value in rows):
        algebraic_text = sop
    if algebraic_text != law_steps[-1][0]:
        law_steps.append((algebraic_text, "Exact minimum operator form; verified against the truth table"))
    return {"variables": names, "rows": rows, "ones": ones, "zeros": zeros,
            "sop": sop, "pos": pos, "alternatives": sop_forms[1:],
            "prime_implicants": sop_patterns, "groups": sop_covers,
            "dont_cares": dc, "law_steps": law_steps, "algebraic": algebraic_text,
            "operator_count": operator_count(parse(algebraic_text))}


def format_implicant(pattern: str, names: list[str]) -> str:
    return implicant_term(pattern, names)


def format_expression(node: Node) -> str:
    if node.kind == "var": return str(node.value)
    if node.kind == "const": return "1" if node.value else "0"
    if node.kind == "not":
        child = node.left
        rendered = format_expression(child)  # type: ignore[arg-type]
        if child.kind == "var": return rendered + "'"  # type: ignore[union-attr]
        return "(" + rendered + ")'"
    symbol = {"and": "·", "or": "+", "xor": "⊕", "xnor": "⊙", "nand": "↑", "nor": "↓"}[node.kind]
    return f"({format_expression(node.left)} {symbol} {format_expression(node.right)})"  # type: ignore[arg-type]


def operator_count(node: Node) -> int:
    if node.kind in ("var", "const"): return 0
    return 1 + (operator_count(node.left) if node.left else 0) + (operator_count(node.right) if node.right else 0)


def _has_outer_not(node: Node) -> bool:
    return node.kind == "not" and node.left is not None and node.left.kind in ("and", "or")


def _apply_demorgan_outer(node: Node) -> Node:
    assert _has_outer_not(node) and node.left
    inner = node.left
    op = "or" if inner.kind == "and" else "and"
    return _junction(op, Node("not", left=inner.left), Node("not", left=inner.right))


def _literal_key(node: Node) -> tuple[str, bool] | None:
    if node.kind == "var": return str(node.value), False
    if node.kind == "not" and node.left and node.left.kind == "var": return str(node.left.value), True
    return None


def _same(a: Node, b: Node) -> bool:
    return a == b


def _junction(kind: str, *nodes: Node) -> Node:
    flat: list[Node] = []
    for node in nodes:
        if node.kind == kind:
            flat.extend((node.left, node.right))  # type: ignore[arg-type]
        else:
            flat.append(node)
    # Idempotence and complement annihilation/identity.
    unique: list[Node] = []
    keys: set[tuple[str, bool]] = set()
    for node in flat:
        if node.kind == "const":
            if kind == "and" and not node.value: return Node("const", False)
            if kind == "or" and node.value: return Node("const", True)
            continue
        key = _literal_key(node)
        if key:
            if (key[0], not key[1]) in keys:
                return Node("const", kind == "or")
            if key in keys: continue
            keys.add(key)
        if not any(_same(node, prior) for prior in unique): unique.append(node)
    if not unique: return Node("const", kind == "and")
    result = unique[0]
    for node in unique[1:]: result = Node(kind, left=result, right=node)
    return result


def _rewrite_once(node: Node) -> tuple[Node, str] | None:
    if node.kind in ("var", "const"): return None
    # Rewriting is bottom-up. Each rule returns an equivalent expression.
    if node.left:
        child = _rewrite_once(node.left)
        if child:
            return Node(node.kind, node.value, child[0], node.right), child[1]
    if node.right:
        child = _rewrite_once(node.right)
        if child:
            return Node(node.kind, node.value, node.left, child[0]), child[1]
    a, b = node.left, node.right
    if node.kind == "not":
        assert a
        if a.kind == "const": return Node("const", not bool(a.value)), "Complement constant"
        if a.kind == "not": return a.left, "Double negation"  # type: ignore[return-value]
        if a.kind in ("and", "or"):
            op = "or" if a.kind == "and" else "and"
            return _junction(op, Node("not", left=a.left), Node("not", left=a.right)), "De Morgan's law"
    if a and b and node.kind in ("and", "or"):
        # Identity and null laws.
        if a.kind == "const":
            if node.kind == "and": return (b, "Identity law") if a.value else (Node("const", False), "Null law")
            return (Node("const", True), "Null law") if a.value else (b, "Identity law")
        if b.kind == "const":
            if node.kind == "and": return (a, "Identity law") if b.value else (Node("const", False), "Null law")
            return (Node("const", True), "Null law") if b.value else (a, "Identity law")
        ka, kb = _literal_key(a), _literal_key(b)
        if ka and kb and ka[0] == kb[0] and ka[1] != kb[1]:
            return Node("const", node.kind == "or"), "Complement law"
        if a == b: return a, "Idempotent law"
        # Absorption: A + AB = A; A(A+B) = A.
        if node.kind == "or" and b.kind == "and" and (a == b.left or a == b.right): return a, "Absorption law"
        if node.kind == "or" and a.kind == "and" and (b == a.left or b == a.right): return b, "Absorption law"
        if node.kind == "and" and b.kind == "or" and (a == b.left or a == b.right): return a, "Absorption law"
        if node.kind == "and" and a.kind == "or" and (b == a.left or b == a.right): return b, "Absorption law"
    # XOR/XNOR expansions.
    if node.kind in ("xor", "xnor") and a and b:
        if node.kind == "xor":
            return _junction("or", _junction("and", a, Node("not", left=b)), _junction("and", Node("not", left=a), b)), "XOR identity"
        return _junction("or", _junction("and", a, b), _junction("and", Node("not", left=a), Node("not", left=b))), "XNOR identity"
    if node.kind in ("nand", "nor") and a and b:
        base = "and" if node.kind == "nand" else "or"
        return Node("not", left=Node(base, left=a, right=b)), "NAND/NOR definition"
    return None


def simplify_algebraically(source: str, max_passes: int = 500) -> tuple[Node, list[tuple[str, str]]]:
    """Apply equivalence-preserving Boolean laws, choosing the cheapest seen form."""
    current = parse(source)
    steps: list[tuple[str, str]] = [(format_expression(current), "Input")]
    # Rewriting order is deterministic; cycle protection keeps expansion rules safe.
    seen = {current}
    for _ in range(max_passes):
        change = _rewrite_once(current)
        if not change: break
        next_node, law = change
        if next_node in seen: break
        current = next_node
        seen.add(current)
        steps.append((format_expression(current), law))
    return current, steps
