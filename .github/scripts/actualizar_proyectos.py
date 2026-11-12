"""Rellena la sección «Últimos proyectos» del README con los repositorios más recientes."""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
README = RAIZ / "README.md"
CONFIG = RAIZ / ".github" / "proyectos.json"
INICIO = "<!-- PROYECTOS:INICIO -->"
FIN = "<!-- PROYECTOS:FIN -->"

# Color y logo (Simple Icons) de cada tecnología para las insignias.
INSIGNIAS = {
    "Kotlin": ("7F52FF", "kotlin"),
    "Java": ("ED8B00", "openjdk"),
    "Python": ("3776AB", "python"),
    "PyQt6": ("41CD52", "qt"),
    "PHP": ("777BB4", "php"),
    "JavaScript": ("F7DF1E", "javascript"),
    "TypeScript": ("3178C6", "typescript"),
    "HTML": ("E34F26", "html5"),
    "CSS": ("1572B6", "css3"),
    "C": ("A8B9CC", "c"),
    "C#": ("512BD4", "dotnet"),
    "C++": ("00599C", "cplusplus"),
    "Dart": ("0175C2", "dart"),
    "Shell": ("4EAA25", "gnubash"),
    "Jetpack Compose": ("4285F4", "jetpackcompose"),
    "XML": ("005FAD", "xml"),
    "React": ("61DAFB", "react"),
    "Next.js": ("000000", "nextdotjs"),
    "Node.js": ("5FA04E", "nodedotjs"),
    "Tailwind CSS": ("06B6D4", "tailwindcss"),
    "Odoo": ("714B67", "odoo"),
}

EMOJI_POR_LENGUAJE = {
    "Kotlin": "📱",
    "Java": "☕",
    "Python": "🐍",
    "HTML": "🌐",
    "CSS": "🎨",
    "JavaScript": "🌐",
    "TypeScript": "🌐",
    "PHP": "🐘",
}


def api(ruta):
    peticion = urllib.request.Request(
        f"https://api.github.com{ruta}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "actualizar-proyectos"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        peticion.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(peticion, timeout=30) as respuesta:
        return json.load(respuesta)


def tiene_commits(repo):
    # GitHub tarda en calcular el tamaño de los repos nuevos, así que se comprueba si hay commits.
    try:
        return bool(api(f"/repos/{repo['full_name']}/commits?per_page=1"))
    except urllib.error.HTTPError as error:
        if error.code == 409:  # repositorio vacío
            return False
        raise


def insignia(nombre):
    color, logo = INSIGNIAS.get(nombre, ("30363D", ""))
    etiqueta = urllib.parse.quote(nombre.replace("-", "--").replace("_", "__").replace(" ", "_"))
    url = f"https://img.shields.io/badge/{etiqueta}-{color}?style=flat-square"
    if logo:
        url += f"&logo={logo}&logoColor=white"
    return f'<img src="{url}" alt="{escape(nombre)}" />'


def tarjeta(repo, extra):
    lenguajes = list(api(f"/repos/{repo['full_name']}/languages"))
    tecnologias = extra.get("tecnologias") or lenguajes[:2]
    emoji = extra.get("emoji") or EMOJI_POR_LENGUAJE.get(lenguajes[0] if lenguajes else "", "📦")
    descripcion = extra.get("descripcion") or repo.get("description") or "Proyecto en desarrollo."
    insignias = "\n".join(f"      {insignia(t)}" for t in tecnologias)
    return (
        '    <td width="50%" valign="top">\n'
        f'      <h3>{emoji} <a href="{repo["html_url"]}">{escape(repo["name"])}</a></h3>\n'
        f"      <p>{escape(descripcion)}</p>\n"
        f"{insignias}\n"
        "    </td>"
    )


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    usuario = os.environ.get("GITHUB_USER", "madebydani")
    excluir = {nombre.lower() for nombre in config.get("excluir", [])}
    excluir.add(usuario.lower())

    repos = api(f"/users/{usuario}/repos?per_page=100&type=owner&sort=created&direction=desc")
    candidatos = [
        r for r in repos
        if not r["fork"] and not r["archived"] and not r["private"]
        and r["name"].lower() not in excluir
    ]
    repos = []
    for repo in candidatos:
        if len(repos) == config.get("max", 4):
            break
        if tiene_commits(repo):
            repos.append(repo)

    personalizados = config.get("personalizados", {})
    celdas = [tarjeta(r, personalizados.get(r["name"], {})) for r in repos]
    filas = ["  <tr>\n" + "\n".join(celdas[i:i + 2]) + "\n  </tr>" for i in range(0, len(celdas), 2)]
    bloque = f"{INICIO}\n<table>\n" + "\n".join(filas) + f"\n</table>\n{FIN}"

    texto = README.read_text(encoding="utf-8")
    patron = re.compile(re.escape(INICIO) + r".*?" + re.escape(FIN), re.S)
    if not patron.search(texto):
        sys.exit("No se encuentran los marcadores de proyectos en el README.")
    nuevo = patron.sub(lambda _: bloque, texto)
    if nuevo != texto:
        README.write_text(nuevo, encoding="utf-8", newline="\n")
        print("README actualizado:", ", ".join(r["name"] for r in repos))
    else:
        print("Sin cambios.")


if __name__ == "__main__":
    main()
