#!/usr/bin/env python3
"""
scriptSemilla.py
Lanza, por este orden:
  1) instalarDockerCompose.py
  2) instalarWebmin.py
  3) configurarBIND_DNS_Server.py
Cada script imprime su propio banner de OK/ERROR.
"""

import os
import subprocess
import sys


SCRIPTS = [
    "instalarDockerCompose.py",
    "instalarWebmin.py",
    "instalarBIND_DNS_Server.py",
]


def print_error_banner(errors):
    print("--------------------------------------------------")
    print("SCRIPT SEMILLA FINALIZADO CON ERRORES")
    print()
    print("- Errores:")
    for err in errors:
        print(f"  - {err}")
    print("--------------------------------------------------")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    errors = []

    for script_name in SCRIPTS:
        path = os.path.join(script_dir, script_name)
        if not os.path.exists(path):
            errors.append(f"No se ha encontrado el script: {path}")
            print_error_banner(errors)
            sys.exit(1)

        result = subprocess.run(["python3", path])
        if result.returncode != 0:
            errors.append(f"{script_name} terminó con código {result.returncode}")
            print_error_banner(errors)
            sys.exit(result.returncode)

    # Si todo va bien, no imprime nada extra: ya viste los banners de cada script.
    sys.exit(0)


if __name__ == "__main__":
    main()
