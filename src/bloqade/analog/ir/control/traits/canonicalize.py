class CanonicalizeTrait:
    @staticmethod
    def canonicalize(expr):
        from bloqade.analog.compiler.rewrite.common.canonicalize import Canonicalizer

        return Canonicalizer().visit(expr)
