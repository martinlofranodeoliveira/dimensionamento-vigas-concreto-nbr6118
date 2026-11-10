from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz / "src"))

from vigas_concreto_nbr6118.codecs import (
    carregar_json_canonico,
    salvar_json_canonico,
    deserializar_projeto,
)
from vigas_concreto_nbr6118.calculator import dimensionar_viga_concreto
from vigas_concreto_nbr6118.exporters import exportar_csv, gerar_relatorio_memorial
from vigas_concreto_nbr6118.svg_generator import gerar_painel_svg


def main() -> int:
    print("=" * 70)
    print("  GERAÇÃO DE ASSETS E DISTRIBUIÇÃO - LOFRANO TECNOLOGIA")
    print("  dimensionamento-vigas-concreto-nbr6118")
    print("=" * 70)

    docs_dir = raiz / "docs"
    dist_dir = raiz / "dist"
    docs_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)

    # 1. Carregar exemplo de referência
    exemplo_json = raiz / "examples" / "viga_residencial_biapoiada.json"
    dados = carregar_json_canonico(str(exemplo_json))
    projeto = deserializar_projeto(dados)

    # 2. Executar dimensionamento estrutural
    resultado = dimensionar_viga_concreto(projeto)

    # 3. Salvar artefatos em docs/
    resultado_json = docs_dir / "exemplo_resultado.json"
    salvar_json_canonico(str(resultado_json), resultado)
    print(f"[OK] JSON canônico gerado: {resultado_json}")

    resultado_csv = docs_dir / "exemplo_planilha.csv"
    with open(resultado_csv, "w", encoding="utf-8", newline="\n") as f:
        f.write(exportar_csv(resultado))
    print(f"[OK] CSV estruturado gerado: {resultado_csv}")

    resultado_txt = docs_dir / "exemplo_memorial.txt"
    with open(resultado_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write(gerar_relatorio_memorial(resultado))
        f.write("\n")
    print(f"[OK] Memorial técnico TXT gerado: {resultado_txt}")

    resultado_svg = docs_dir / "exemplo.svg"
    with open(resultado_svg, "w", encoding="utf-8", newline="\n") as f:
        f.write(gerar_painel_svg(resultado))
        f.write("\n")
    print(f"[OK] Painel SVG vetorial gerado: {resultado_svg}")

    # 4. Renderizar PNG via Google Chrome Headless
    resultado_png = docs_dir / "exemplo.png"
    chrome_cmd = [
        "google-chrome",
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1440,900",
        f"--screenshot={resultado_png}",
        str(resultado_svg),
    ]
    print(f"Executando renderização com Chrome: {' '.join(chrome_cmd)}")
    subp = subprocess.run(chrome_cmd, capture_output=True, text=True)
    if subp.returncode != 0:
        print(f"Aviso do Chrome: {subp.stderr}")

    if resultado_png.exists() and resultado_png.stat().st_size > 10000:
        print(f"[OK] Imagem PNG renderizada com sucesso: {resultado_png} ({resultado_png.stat().st_size} bytes)")
    else:
        print("Erro: Falha na renderização do PNG headless.", file=sys.stderr)
        return 1

    # 5. Criar ZIP determinístico
    zip_path = dist_dir / "exemplo-vigas-concreto.zip"
    if zip_path.exists():
        zip_path.unlink()

    arquivos_zip = [
        ("README.md", raiz / "README.md"),
        ("LICENSE", raiz / "LICENSE"),
        ("examples/viga_residencial_biapoiada.json", raiz / "examples" / "viga_residencial_biapoiada.json"),
        ("examples/viga_edificio_armadura_dupla.json", raiz / "examples" / "viga_edificio_armadura_dupla.json"),
        ("docs/exemplo.svg", resultado_svg),
        ("docs/exemplo.png", resultado_png),
        ("docs/exemplo_resultado.json", resultado_json),
        ("docs/exemplo_planilha.csv", resultado_csv),
        ("docs/exemplo_memorial.txt", resultado_txt),
    ]

    fixed_time = (2026, 1, 1, 0, 0, 0)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(str(zip_path), flags, 0o644)
    with os.fdopen(fd, "wb") as f_out:
        with zipfile.ZipFile(f_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for arcname, fpath in arquivos_zip:
                data = fpath.read_bytes()
                zinfo = zipfile.ZipInfo(arcname, fixed_time)
                zinfo.external_attr = 0o100644 << 16
                zf.writestr(zinfo, data)
    print(f"[OK] Pacote ZIP determinístico gerado: {zip_path} ({zip_path.stat().st_size} bytes)")

    # 6. Construir sdist e wheel via setuptools.build_meta
    print("Construindo pacotes de distribuição (sdist e wheel)...")
    import setuptools.build_meta as b
    os.chdir(raiz)
    sdist_name = b.build_sdist(str(dist_dir))
    wheel_name = b.build_wheel(str(dist_dir))
    print(f"[OK] sdist construído: {sdist_name}")
    print(f"[OK] wheel construído: {wheel_name}")

    # 7. Gerar SHA256SUMS para todos os artefatos em dist/
    linhas_sha = []
    for f in sorted(dist_dir.iterdir()):
        if f.name == "SHA256SUMS":
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        linhas_sha.append(f"{h}  {f.name}\n")
        print(f"  {h}  {f.name}")

    sha_file = dist_dir / "SHA256SUMS"
    sha_file.write_text("".join(linhas_sha), encoding="utf-8")
    print(f"[OK] SHA256SUMS gerado em: {sha_file}")

    print("=" * 70)
    print("  TODOS OS ASSETS E DISTRIBUIÇÕES FORAM GERADOS COM SUCESSO!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
