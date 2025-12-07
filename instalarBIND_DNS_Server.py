#!/usr/bin/env python3
"""
instalarBIND_DNS_Server.py
Instala BIND9 en Ubuntu/Debian (servicio DNS).
"""

import os
import subprocess
import sys
import shutil


def run(cmd, errors, description=""):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        msg_desc = description or "Error ejecutando comando"
        msg = (
            f"{msg_desc}\n"
            f"Comando: {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        errors.append(msg)
        raise RuntimeError(msg)


def check_root():
    if os.geteuid() != 0:
        raise RuntimeError(
            "Este script debe ejecutarse como root (sudo). "
            "Ejemplo: sudo python3 scriptSemilla.py"
        )


def check_distro():
    os_release = "/etc/os-release"
    if not os.path.exists(os_release):
        return

    with open(os_release) as f:
        data = f.read().lower()

    if "ubuntu" not in data and "debian" not in data:
        raise RuntimeError(
            "La distribución no parece ser Debian/Ubuntu. "
            "Este instalador está pensado para sistemas con apt."
        )


def instalar_bind_dns(errors):
    # Opcional: apt-get update por si hace falta
    run(["apt-get", "update"], errors, "apt-get update (pre-requisitos BIND)")

    run(
        [
            "apt-get",
            "install",
            "-y",
            "bind9",
            "bind9utils",
        ],
        errors,
        "Instalando BIND9",
    )

    if shutil.which("systemctl") is not None:
        # IMPORTANTE: solo start/restart, no enable para evitar el error de "alias"
        try:
            run(
                ["systemctl", "restart", "bind9"],
                errors,
                "Arrancando servicio bind9",
            )
        except RuntimeError:
            # Como plan B, probamos con 'named'
            run(
                ["systemctl", "restart", "named"],
                errors,
                "Arrancando servicio named (BIND9)",
            )


def print_success_banner():
    print("--------------------------------------------------")
    print("BIND DNS INSTALADO")
    print("--------------------------------------------------")


def print_error_banner(errors, exception_msg):
    print("--------------------------------------------------")
    print("BIND DNS NO INSTALADO")
    print()
    print("- Errores:")
    if errors:
        for err in errors:
            print("  ----------------------------------------------")
            for line in err.splitlines():
                print(f"  {line}")
    else:
        print(f"  - {exception_msg}")
    print("--------------------------------------------------")


def main():
    errors = []
    try:
        check_root()
        check_distro()
        instalar_bind_dns(errors)
        print_success_banner()
        sys.exit(0)
    except Exception as e:
        print_error_banner(errors, str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
