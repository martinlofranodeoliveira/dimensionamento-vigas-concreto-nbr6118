from __future__ import annotations

import hashlib
import os
import sys
import tarfile
import zipfile
from pathlib import Path


def main() -> int:
    print("=" * 70)
    print("  VERIFICAÇÃO DE INTEGRIDADE DA DISTRIBUIÇÃO - LOFRANO TECNOLOGIA")
    print("=" * 70)

    raiz = Path(__file__).resolve().parent.parent
    dist_dir = raiz / "dist"

    if not dist_dir.exists():
        print(f"Erro: Diretório de distribuição não encontrado: {dist_dir}", file=sys.stderr)
        return 1

    sha_path = dist_dir / "SHA256SUMS"
    if not sha_path.exists():
        print("Erro: Arquivo SHA256SUMS não encontrado.", file=sys.stderr)
        return 1

    linhas = sha_path.read_text(encoding="utf-8").strip().splitlines()
    if not linhas:
        print("Erro: SHA256SUMS está vazio.", file=sys.stderr)
        return 1

    for linha in linhas:
        if not linha.strip():
            continue
        partes = linha.strip().split()
        if len(partes) != 2:
            print(f"Erro na linha do checksum: {linha}", file=sys.stderr)
            return 1
        esperado_hash, nome_arq = partes
        caminho_arq = dist_dir / nome_arq
        if not caminho_arq.exists():
            print(f"Erro: Arquivo {nome_arq} não encontrado.", file=sys.stderr)
            return 1
        obtido_hash = hashlib.sha256(caminho_arq.read_bytes()).hexdigest()
        if obtido_hash != esperado_hash:
            print(f"Erro: Hash divergente para {nome_arq}: {obtido_hash} != {esperado_hash}", file=sys.stderr)
            return 1
        print(f"[OK] Checksum verificado para {nome_arq}")

    # Verificar conteúdo do wheel
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        print("Erro: Nenhum pacote .whl encontrado.", file=sys.stderr)
        return 1
    for w in wheels:
        with zipfile.ZipFile(w, "r") as zf:
            nomes = zf.namelist()
            print(f"[OK] Wheel {w.name} contém {len(nomes)} arquivos.")
            self_contained = any("vigas_concreto_nbr6118" in n for n in nomes)
            if not self_contained:
                print("Erro: Pacote não contém os fontes do módulo.", file=sys.stderr)
                return 1

    # Verificar sdist
    sdists = list(dist_dir.glob("*.tar.gz"))
    if not sdists:
        print("Erro: Nenhum pacote .tar.gz encontrado.", file=sys.stderr)
        return 1
    for s in sdists:
        with tarfile.open(s, "r:gz") as tf:
            nomes = tf.getnames()
            print(f"[OK] sdist {s.name} contém {len(nomes)} arquivos.")

    print("=" * 70)
    print("  INTEGRIDADE DE DISTRIBUIÇÃO 100% VALIDADA COM SUCESSO!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
