#!/usr/bin/env python3
"""
configurarBIND_DNS_Server.py
Configura una zona master 'livingspace.sdslab.cat' en BIND9
usando como IP 192.168.1.149 en los registros A.

Salida:
  - Si todo va bien:
      --------------------------------------------------
      BIND DNS CONFIGURADO
      --------------------------------------------------
  - Si algo falla:
      --------------------------------------------------
      BIND DNS NO CONFIGURADO

      - Errores:
        - ...
      --------------------------------------------------
"""

import os
import subprocess
import sys
import shutil


SERVER_IP = "192.168.1.149"
ZONE_NAME = "livingspace.sdslab.cat"
ZONE_FILE_PATH = "/var/lib/bind/livingspace.sdslab.cat.hosts"
NAMED_LOCAL_PATH = "/etc/bind/named.conf.local"


ZONE_FILE_CONTENT = f"""$ttl 60
livingspace.sdslab.cat. IN  SOA ns1.livingspace.sdslab.cat. grupo3.sarria.salesians.cat. (
            2025102906
            60
            600
            1209600
            60 )
livingspace.sdslab.cat. IN  NS  ns1.livingspace.sdslab.cat.
livingspace.sdslab.cat. 60  IN  A   {SERVER_IP}
ns1.livingspace.sdslab.cat. 60  IN  A   {SERVER_IP}
www.livingspace.sdslab.cat. 60  IN  A   {SERVER_IP}
kuma.livingspace.sdslab.cat.    60  IN  A   {SERVER_IP}
"""


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
            "Este configurador está pensado para sistemas con BIND9 de Debian/Ubuntu."
        )


def ensure_bind_installed(errors):
    run(["apt-get", "update"], errors, "apt-get update (para BIND9)")
    run(
        ["apt-get", "install", "-y", "bind9", "bind9utils"],
        errors,
        "Instalando/verificando instalación de BIND9",
    )


def write_zone_file(errors):
    os.makedirs(os.path.dirname(ZONE_FILE_PATH), exist_ok=True)

    with open(ZONE_FILE_PATH, "w") as f:
        f.write(ZONE_FILE_CONTENT)

    # Permisos típicos: root:bind 0644 (si existe el grupo bind)
    try:
        shutil.chown(ZONE_FILE_PATH, user="root", group="bind")
    except Exception:
        # Si falla, no consideramos fatal; BIND suele poder leer con root:root 0644
        pass

    os.chmod(ZONE_FILE_PATH, 0o644)


def ensure_zone_in_named_conf_local(errors):
    existing = ""
    if os.path.exists(NAMED_LOCAL_PATH):
        with open(NAMED_LOCAL_PATH) as f:
            existing = f.read()

    if f'zone "{ZONE_NAME}"' in existing:
        return  # ya está configurada

    zone_snippet = f"""

zone "{ZONE_NAME}" {{
    type master;
    file "{ZONE_FILE_PATH}";
}};
"""

    with open(NAMED_LOCAL_PATH, "a") as f:
        f.write(zone_snippet)


def reload_bind(errors):
    if shutil.which("systemctl") is not None:
        run(
            ["systemctl", "restart", "bind9"],
            errors,
            "Reiniciando servicio bind9",
        )
    else:
        raise RuntimeError("No se ha encontrado systemctl para reiniciar bind9.")


def print_success_banner():
    print("--------------------------------------------------")
    print("BIND DNS CONFIGURADO")
    print("--------------------------------------------------")


def print_error_banner(errors, exception_msg):
    print("--------------------------------------------------")
    print("BIND DNS NO CONFIGURADO")
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
        ensure_bind_installed(errors)
        write_zone_file(errors)
        ensure_zone_in_named_conf_local(errors)
        reload_bind(errors)
        print_success_banner()
        sys.exit(0)
    except Exception as e:
        print_error_banner(errors, str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
