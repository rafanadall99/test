#!/usr/bin/env python3
import os
import stat

# Lista de scripts a los que quieres dar permiso de ejecución
SCRIPTS = [
    "instalarBIND_DNS_Server.py",
    "instalarDockerCompose.py",
    "instalarWebmin.py",
    "scriptSemilla.py",
]

def hacer_ejecutable(ruta):
    """Añade permiso de ejecución para usuario, grupo y otros."""
    st = os.stat(ruta)
    os.chmod(ruta, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for nombre in SCRIPTS:
        ruta = os.path.join(base_dir, nombre)

        if not os.path.isfile(ruta):
            print(f"[AVISO] No encontrado: {ruta}")
            continue

        try:
            hacer_ejecutable(ruta)
            print(f"[OK] Marcado como ejecutable: {ruta}")
        except PermissionError:
            print(f"[ERROR] Permisos insuficientes para: {ruta} (prueba con sudo)")
        except Exception as e:
            print(f"[ERROR] No se pudo cambiar permisos de {ruta}: {e}")

if __name__ == "__main__":
    main()
