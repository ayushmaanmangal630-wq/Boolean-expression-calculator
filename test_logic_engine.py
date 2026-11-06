import unittest

from logic_engine import evaluate, parse, simplify, simplify_algebraically, truth_table, variables


class LogicEngineTests(unittest.TestCase):
    def test_implicit_and_and_postfix_not(self):
        result = simplify("A'B + AB")
        self.assertEqual(result["sop"], "B")

    def test_all_operator_families(self):
        cases = [("A⊕B", "A'B + AB'"), ("A⊙B", "A'B' + AB"),
                 ("A↑B", "A' + B'"), ("A↓B", "A'B'")]
        for expr, _ in cases:
            result = simplify(expr)
            names, rows = truth_table(parse(expr))
            for _, bits, expected in rows:
                assignment = dict(zip(names, map(bool, bits)))
                self.assertEqual(evaluate(parse(result["sop"]), assignment), bool(expected))
                self.assertEqual(evaluate(parse(result["pos"]), assignment), bool(expected))

    def test_examples_and_constants(self):
        examples = ["AB + AB'", "(A+B)(A+B')", "A'B + AB + ABC",
                    "(A+B+C)(A+B)", "(A+B)(A'+C)", "0", "1", "AA'"]
        for expr in examples:
            self.assertTrue(simplify(expr)["sop"])

    def test_reported_nested_expression(self):
        expr = "((XY'+XYZ)'+X(Y+XY'))'"
        result = simplify(expr)
        self.assertEqual(result["variables"], ["X", "Y", "Z"])
        self.assertEqual(result["algebraic"], "0")
        self.assertEqual(result["pos"], "0")
        self.assertEqual(result["ones"], [])
        self.assertEqual(len(result["zeros"]), 8)
        self.assertTrue(any(law == "De Morgan's law" for _, law in result["law_steps"]))

    def test_user_wanted_operator_minimum_not_hidden_zero(self):
        # This truth function is constant zero; the equivalent minimum is necessarily 0.
        result = simplify("((XY'+XYZ)'+X(Y+XY'))'")
        self.assertEqual(result["algebraic"], "0")
        self.assertEqual(result["ones"], [])

    def test_demorgan_and_absorption_derivation(self):
        result = simplify("(A+B)'")
        self.assertEqual(result["algebraic"], "A'B'")
        self.assertIn("De Morgan's law", [law for _, law in result["law_steps"]])

    def test_syntax_errors_are_reported(self):
        with self.assertRaisesRegex(ValueError, "closing parenthesis"):
            parse("(A+B")
        with self.assertRaises(ValueError):
            parse("A$")

    def test_exact_limit(self):
        with self.assertRaisesRegex(ValueError, "8 variables"):
            simplify("A+B+C+D+E+F+G+H+I")


if __name__ == "__main__":
    unittest.main()
