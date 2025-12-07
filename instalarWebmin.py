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
    Configura el repo oficial de Webmin usando el script oficial
    webmin-setup-repo.sh (nuevo repositorio con clave segura).
    """

    # 1) Elimina cualquier repo antiguo de Webmin que use la clave DSA insegura
    old_list = "/etc/apt/sources.list.d/webmin.list"
    if os.path.exists(old_list):
        try:
            os.remove(old_list)
        except OSError as e:
            errors.append(f"No se pudo eliminar {old_list}: {e}")
            raise

    main_sources = "/etc/apt/sources.list"
    if os.path.exists(main_sources):
        try:
            with open(main_sources) as f:
                lines = f.readlines()
            new_lines = [ln for ln in lines if "webmin.com" not in ln]
            if new_lines != lines:
                with open(main_sources, "w") as f:
                    f.writelines(new_lines)
        except OSError as e:
            errors.append(f"No se pudo limpiar {main_sources}: {e}")
            raise

    # 2) Actualiza índices una vez limpio de repos antiguos de Webmin
    run(["apt-get", "update"], errors, "apt-get update (pre-requisitos)")

    # 3) Dependencias necesarias para descargar y ejecutar el script oficial
    run(
        [
            "apt-get",
            "install",
            "-y",
            "curl",
            "ca-certificates",
            "gnupg",
            "software-properties-common",
            "apt-transport-https",
            "wget",
        ],
        errors,
        "Instalando dependencias para Webmin",
    )

    # 4) Descarga y ejecuta el script oficial webmin-setup-repo.sh
    #    --force = no pregunta "Setup Webmin releases repository? (y/N)"
    run(
        [
            "bash",
            "-lc",
            (
                "cd /tmp && "
                "curl -fsSL -o webmin-setup-repo.sh "
                "https://raw.githubusercontent.com/webmin/webmin/master/webmin-setup-repo.sh && "
                "chmod +x webmin-setup-repo.sh && "
                "./webmin-setup-repo.sh --force --stable"
            ),
        ],
        errors,
        "Configurando repositorio oficial de Webmin (webmin-setup-repo.sh)",
    )


def install_webmin_and_bind(errors):
    setup_webmin_repo(errors)

    # Webmin + BIND9 (para módulo BIND DNS Server)
    run(
        [
            "apt-get",
            "install",
            "-y",
            "--install-recommends",
            "webmin",
            "bind9",
            "bind9utils",
        ],
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
        install_webmin_and_bind(errors)
        print_success_banner()
        sys.exit(0)
    except Exception as e:
        print_error_banner(errors, str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
