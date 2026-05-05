"""Script de manutencao das traducoes.

Uso:

    python -m scripts.i18n_audit

Sai com codigo 0 se todas as locales estao consistentes com o idioma de
referencia (DEFAULT_LANGUAGE = pt) e codigo 1 caso haja chaves faltando ou
extras. Adequado para rodar em CI antes do merge.
"""
from __future__ import annotations

import sys

from src.i18n.translations import DEFAULT_LANGUAGE, audit_keys


def main() -> int:
    report = audit_keys(reference=DEFAULT_LANGUAGE)
    fail = False
    print(f"Reference language: {DEFAULT_LANGUAGE}\n")

    for lang, diff in report.items():
        missing = diff["missing"]
        extra = diff["extra"]
        status = "OK" if not missing and not extra else "DIVERGENT"
        print(f"[{status}] {lang}")
        if missing:
            fail = True
            print(f"  Missing keys ({len(missing)}):")
            for key in missing:
                print(f"    - {key}")
        if extra:
            fail = True
            print(f"  Extra keys ({len(extra)}):")
            for key in extra:
                print(f"    + {key}")
        print()

    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
