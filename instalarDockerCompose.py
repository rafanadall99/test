#!/usr/bin/env python3
"""
instalarDockerCompose.py
Instala Docker Engine y Docker Compose (plugin v2) en Ubuntu/Debian
usando el repositorio oficial de Docker.
Salida por terminal:
 - SOLO un banner de éxito, o
 - un banner de error con la lista de errores.
"""

import os
import subprocess
import sys
import shutil


def run(cmd, errors, description=""):
    """
    Ejecuta un comando sin mostrar nada por pantalla.
    Si falla, guarda el error en la lista 'errors' y lanza excepción.
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
    """Comprueba que el script se ejecuta como root."""
    if os.geteuid() != 0:
        raise RuntimeError(
            "Este script debe ejecutarse como root (sudo). "
            "Ejemplo: sudo python3 scriptSemilla.py"
        )


def check_distro():
    """Comprueba que estamos en Debian/Ubuntu, en silencio salvo error."""
    os_release = "/etc/os-release"
    if not os.path.exists(os_release):
        # Si no existe, dejamos continuar, pero podría ser raro
        return

    with open(os_release) as f:
        data = f.read().lower()

    if "ubuntu" not in data and "debian" not in data:
        raise RuntimeError(
            "La distribución no parece ser Debian/Ubuntu. "
            "Este instalador está pensado para sistemas con apt."
        )


def get_ubuntu_codename() -> str:
    """Obtiene UBUNTU_CODENAME o VERSION_CODENAME de /etc/os-release."""
    codename = None
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("UBUNTU_CODENAME=") or line.startswith("VERSION_CODENAME="):
                    codename = line.split("=", 1)[1].strip().strip('"')
                    break
    if not codename:
        codename = "noble"  # por defecto, para Ubuntu 24.04
    return codename


def setup_docker_repo(errors):
    """Configura el repositorio oficial de Docker para Ubuntu."""
    # Paquetes necesarios
    run(["apt-get", "update"], errors, "apt-get update (pre-requisitos)")
    run(
        ["apt-get", "install", "-y", "ca-certificates", "curl", "gnupg"],
        errors,
        "Instalando dependencias para el repositorio de Docker",
    )

    keyring_dir = "/etc/apt/keyrings"
    os.makedirs(keyring_dir, exist_ok=True)

    # Clave GPG
    run(
        [
            "bash",
            "-lc",
            "curl -fsSL https://download.docker.com/linux/ubuntu/gpg "
            "-o /etc/apt/keyrings/docker.asc",
        ],
        errors,
        "Descargando clave GPG de Docker",
    )
    os.chmod("/etc/apt/keyrings/docker.asc", 0o644)

    # docker.sources
    codename = get_ubuntu_codename()
    sources_path = "/etc/apt/sources.list.d/docker.sources"
    content = f"""Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: {codename}
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
"""

    with open(sources_path, "w") as f:
        f.write(content)

    run(["apt-get", "update"], errors, "apt-get update (repo oficial Docker)")


def install_docker(errors):
    """Instala Docker Engine y Docker Compose plugin."""
    setup_docker_repo(errors)

    paquetes = [
        "docker-ce",
        "docker-ce-cli",
        "containerd.io",
        "docker-buildx-plugin",
        "docker-compose-plugin",
    ]
    run(
        ["apt-get", "install", "-y"] + paquetes,
        errors,
        f"Instalando paquetes Docker: {' '.join(paquetes)}",
    )

    if shutil.which("systemctl") is not None:
        run(
            ["systemctl", "enable", "--now", "docker"],
            errors,
            "Habilitando y arrancando el servicio docker",
        )


def configure_docker_group(errors):
    """Añade al usuario al grupo docker (si hay SUDO_USER)."""
    run(["groupadd", "-f", "docker"], errors, "Creando grupo docker (si no existía)")

    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        run(
            ["usermod", "-aG", "docker", sudo_user],
            errors,
            f"Añadiendo usuario {sudo_user} al grupo docker",
        )


def show_versions(errors):
    """Comprueba que Docker y docker compose responden (sin imprimir versión)."""
    if shutil.which("docker") is None:
        raise RuntimeError("No se ha encontrado el binario 'docker' en el PATH.")

    run(["docker", "--version"], errors, "Comprobando docker --version")
    run(["docker", "compose", "version"], errors, "Comprobando docker compose version")


def print_success_banner():
    print("--------------------------------------------------")
    print("DOCKER COMPOSE INSTLADO")
    print("--------------------------------------------------")


def print_error_banner(errors, exception_msg):
    print("--------------------------------------------------")
    print("DOCKER COMPOSE NO INSTLADO")
    print()
    print("- Errores:")
    if errors:
        for err in errors:
            # Mostramos solo la primera línea de cada error para no saturar
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
        install_docker(errors)
        configure_docker_group(errors)
        show_versions(errors)
        print_success_banner()
        sys.exit(0)
    except Exception as e:
        print_error_banner(errors, str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
