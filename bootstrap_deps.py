# -*- coding: utf-8 -*-
"""
bootstrap_deps.py
-----------------
Instalador de dependências para scripts e notebooks.

Uso em SCRIPT (.py):
    import bootstrap_deps as deps
    deps.ensure(requirements_file="requirements.txt")  # reinicia o processo se instalar algo

Uso em NOTEBOOK (Jupyter/VSCode):
    import bootstrap_deps as deps
    deps.ensure_in_notebook(requirements_file="requirements.txt")  # reinicie o kernel após instalar

Observação: para produção, prefira venv + requirements.txt. O bootstrap é uma rede de segurança.
"""
from __future__ import annotations
import sys
import subprocess
import importlib.util
import os
from typing import Iterable, List, Optional
from scipy.stats import chi2  # não é obrigatório; só para manter coerência de imports se você usar em outros trechos

# Pacotes padrão caso não exista requirements.txt (inclui linearmodels)
DEFAULT_REQS = [
    "numpy==2.3.2",
    "pandas==2.3.1",
    "scipy==1.16.1",
    "statsmodels==0.14.5",
    "linearmodels==6.1",
    "pyreadstat==1.3.1",
    "matplotlib==3.10.5",
    "patsy==1.0.1",
    "seaborn==0.13.2",
    "appnope==0.1.4; platform_system=='Darwin'",  # só no macOS
]

# Mapa pacote → módulo importável (quando o nome difere)
PKG_TO_MODULE = {
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "statsmodels": "statsmodels",
    "linearmodels": "linearmodels",
    "pyreadstat": "pyreadstat",
    "matplotlib": "matplotlib",
    "patsy": "patsy",
    "seaborn": "seaborn",
    "appnope": "appnope",
}

def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False

def _missing_modules_from_requirements(reqs: Iterable[str]) -> List[str]:
    missing = []
    for req in reqs:
        # pega só o nome antes de ==, >=, etc.
        name = req.split(";")[0].split("[")[0]
        for sep in ["==", ">=", "<=", "~=", "!=", ">", "<"]:
            name = name.split(sep)[0]
        name = name.strip()
        module = PKG_TO_MODULE.get(name, name)
        # markers de plataforma simples (ex.: appnope só no macOS)
        if ";" in req:
            marker = req.split(";", 1)[1].strip()
            try:
                import platform as _pf
                if "platform_system" in marker and _pf.system() != "Darwin":
                    continue
            except Exception:
                pass
        if not _module_available(module):
            missing.append(req)
    return missing

def _pip_install(args: List[str]) -> None:
    cmd = [sys.executable, "-m", "pip"] + args
    print("[bootstrap] executando:", " ".join(cmd))
    subprocess.check_call(cmd)

def ensure(requirements_file: Optional[str] = None, extra: Optional[Iterable[str]] = None) -> None:
    """
    Garante dependências para SCRIPTS. Se instalar algo, reinicia o processo
    com os mesmos argumentos para carregar os módulos recém-instalados.
    """
    reqs = []
    if requirements_file and os.path.exists(requirements_file):
        # delega toda a resolução ao pip
        reqs = ["-r", requirements_file]
    else:
        # instala apenas o conjunto mínimo faltante
        reqs = DEFAULT_REQS.copy()
        if extra:
            reqs.extend(list(extra))
        missing = _missing_modules_from_requirements(reqs)
        if not missing:
            return
        reqs = missing

    try:
        _pip_install(["install", "--disable-pip-version-check", "--no-input"] + reqs)
    except subprocess.CalledProcessError as e:
        print("[bootstrap] Falha ao instalar dependências:", e, file=sys.stderr)
        raise

    # Reinicia o processo (apenas para scripts .py)
    print("[bootstrap] Dependências instaladas. Reiniciando o processo...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

def ensure_in_notebook(requirements_file: Optional[str] = None, extra: Optional[Iterable[str]] = None) -> None:
    """
    Garante dependências para NOTEBOOKS sem reiniciar o processo automaticamente.
    Após instalar, reinicie o kernel.
    """
    reqs = []
    if requirements_file and os.path.exists(requirements_file):
        reqs = ["-r", requirements_file]
    else:
        reqs = DEFAULT_REQS.copy()
        if extra:
            reqs.extend(list(extra))
        missing = _missing_modules_from_requirements(reqs)
        if not missing:
            print("[bootstrap] Todas as dependências necessárias já estão disponíveis.")
            return
        reqs = missing

    try:
        _pip_install(["install", "--disable-pip-version-check", "--no-input"] + reqs)
        print("[bootstrap] Instalação concluída. Reinicie o kernel para carregar os novos pacotes.")
    except subprocess.CalledProcessError as e:
        print("[bootstrap] Falha ao instalar dependências:", e, file=sys.stderr)
        raise
