#!/usr/bin/env python3
"""
instalarWebmin.py
Instala Webmin (puerto 10000) y BIND9 en Ubuntu/Debian
usando el repositorio oficial de Webmin.

Salida:
  - Si todo va bien:
      --------------------------------------------------
      WEBMIN + BIND INSTALADOS
      --------------------------------------------------
  - Si algo falla:
      --------------------------------------------------
      WEBMIN + BIND NO INSTALADOS

      - Errores:
        - ...
      --------------------------------------------------
"""

import os
import subprocess
import sys
import shutil


def run(cmd, errors, description=""):
    """
    Ejecuta un comando sin mostrar nada por pantalla.
    Si falla, guarda el error en 'errors' y lanza excepción.
    """
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


def setup_webmin_repo(errors):
    """
    Configura el repo oficial de Webmin y su clave GPG
    usando keyring en /usr/share/keyrings/webmin-key.asc
    """
    run(["apt-get", "update"], errors, "apt-get update (pre-requisitos)")
    run(
        [
            "apt-get",
            "install",
            "-y",
            "wget",
            "curl",
            "ca-certificates",
            "apt-transport-https",
            "software-properties-common",
            "gnupg",
        ],
        errors,
        "Instalando dependencias para Webmin",
    )

    def fetch_keyring():
        # Intenta primero por HTTPS y, si falla, recurre a HTTP (algunos
        # servidores Ubuntu mínimos carecen de certificados actualizados).
        urls = [
            "https://download.webmin.com/jcameron-key.asc",
            "http://www.webmin.com/jcameron-key.asc",
        ]
        last_error = None
        initial_error_count = len(errors)
        for url in urls:
            try:
                run(
                    [
                        "bash",
                        "-lc",
                        f"curl -fsSL {url} | gpg --dearmor | tee /usr/share/keyrings/webmin.gpg > /dev/null",
                    ],
                    errors,
                    f"Descargando y registrando clave GPG de Webmin ({url})",
                )
                # Limpia cualquier error previo que proviniera de un intento fallido.
                del errors[initial_error_count:]
                return
            except RuntimeError as exc:  # pragma: no cover - controlado por flujo normal
                last_error = exc

        # Si llegamos aquí es que todos los intentos fallaron; conservamos solo el último.
        del errors[initial_error_count:]
        if last_error:
            errors.append(str(last_error))
            raise last_error

    fetch_keyring()

    sources_path = "/etc/apt/sources.list.d/webmin.list"
    content = (
        "deb [signed-by=/usr/share/keyrings/webmin.gpg] "
        "http://download.webmin.com/download/repository sarge contrib\n"
    )

    with open(sources_path, "w") as f:
        f.write(content)

    run(["apt-get", "update"], errors, "apt-get update (repo Webmin)")


def install_webmin_and_bind(errors):
    setup_webmin_repo(errors)

    # Webmin + BIND9 (para módulo BIND DNS Server)
    run(
        ["apt-get", "install", "-y", "--install-recommends", "webmin", "bind9", "bind9utils"],
        errors,
        "Instalando Webmin y BIND9",
    )

    if shutil.which("systemctl") is not None:
        run(
            ["systemctl", "enable", "--now", "webmin"],
            errors,
            "Habilitando y arrancando servicio webmin",
        )
        run(
            ["systemctl", "enable", "--now", "bind9"],
            errors,
            "Habilitando y arrancando servicio bind9",
        )


def print_success_banner():
    print("--------------------------------------------------")
    print("WEBMIN + BIND INSTALADOS")
    print("--------------------------------------------------")


def print_error_banner(errors, exception_msg):
    print("--------------------------------------------------")
    print("WEBMIN + BIND NO INSTALADOS")
    print()
    print("- Errores:")
    if errors:
        for err in errors:
            primera_linea = err.splitlines()[0]
            print(f"  - {primera_linea}")
    else:
        print(f"  - {exception_msg}")
    print("--------------------------------------------------")


def main():
    errors = []
    try:
        check_root()
        check_distro()
        install_webmin_and_bind(errors)
        print_success_banner()
        sys.exit(0)
    except Exception as e:
        print_error_banner(errors, str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
