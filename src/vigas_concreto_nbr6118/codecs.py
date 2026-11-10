from __future__ import annotations

import json
from fractions import Fraction
from typing import Any, Dict, List, Optional

from vigas_concreto_nbr6118.models import (
    SecaoViga,
    PropriedadesMateriais,
    EsforcosSolicitantes,
    PreferenciasDetalhamento,
    ProjetoViga,
)


def _rejeitar_float(valor: str) -> None:
    raise ValueError(
        f"Ponto flutuante IEEE-754 '{valor}' detectado no JSON. "
        "O padrão LOFRANO TECNOLOGIA exige Zero Float (inteiros ou frações exatas com 'num' e 'den')."
    )


def _par_sem_duplicatas(pares: List[tuple[str, Any]]) -> Dict[str, Any]:
    resultado: Dict[str, Any] = {}
    for chave, valor in pares:
        if chave in resultado:
            raise ValueError(f"Chave duplicada detectada no JSON: '{chave}'")
        resultado[chave] = valor
    return resultado


def serializar_fracao(f: Fraction) -> Dict[str, int]:
    """Serializa uma fração em representação exata canônica."""
    return {"num": f.numerator, "den": f.denominator}


def deserializar_fracao(d: Any) -> Fraction:
    """Deserializa um valor em Fraction sem admitir float."""
    if isinstance(d, Fraction):
        return d
    if isinstance(d, int):
        return Fraction(d, 1)
    if isinstance(d, dict) and "num" in d and "den" in d:
        if not isinstance(d["num"], int) or not isinstance(d["den"], int):
            raise ValueError("Numerador e denominador devem ser inteiros.")
        return Fraction(d["num"], d["den"])
    if isinstance(d, str):
        if "/" in d:
            partes = d.split("/")
            if len(partes) == 2:
                return Fraction(int(partes[0].strip()), int(partes[1].strip()))
        return Fraction(d)
    raise ValueError(f"Formato inválido para fração: {d}")


def converter_para_dict(obj: Any) -> Any:
    """Converte estruturas de dados e dataclasses em dicionários canônicos sem float."""
    if isinstance(obj, Fraction):
        return serializar_fracao(obj)
    if isinstance(obj, (int, str, bool)) or obj is None:
        return obj
    if isinstance(obj, float):
        raise ValueError(f"Valor float {obj} detectado durante serialização canônica.")
    if isinstance(obj, list):
        return [converter_para_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): converter_para_dict(v) for k, v in sorted(obj.items(), key=lambda x: str(x[0]))}
    if hasattr(obj, "__dataclass_fields__"):
        res: Dict[str, Any] = {}
        for campo in obj.__dataclass_fields__:
            val = getattr(obj, campo)
            res[campo] = converter_para_dict(val)
        return res
    raise TypeError(f"Tipo não serializável para JSON canônico: {type(obj)}")


def verificar_profundidade(obj: Any, nivel_atual: int = 1, max_nivel: int = 32) -> None:
    """Garante que o JSON não exceda o limite de 32 níveis de profundidade."""
    if nivel_atual > max_nivel:
        raise ValueError(f"Profundidade máxima de aninhamento ({max_nivel}) excedida.")
    if isinstance(obj, dict):
        for v in obj.values():
            verificar_profundidade(v, nivel_atual + 1, max_nivel)
    elif isinstance(obj, list):
        for item in obj:
            verificar_profundidade(item, nivel_atual + 1, max_nivel)


def carregar_json_canonico(texto_ou_caminho: str) -> Dict[str, Any]:
    """Carrega dados JSON com garantias estritas: sem BOM, sem floats, sem chaves duplicadas."""
    if "\n" not in texto_ou_caminho and (texto_ou_caminho.endswith(".json") or len(texto_ou_caminho) < 256):
        import os
        if os.path.exists(texto_ou_caminho):
            with open(texto_ou_caminho, "rb") as f:
                bytes_conteudo = f.read()
                if bytes_conteudo.startswith(b"\xef\xbb\xbf"):
                    raise ValueError("BOM UTF-8 não permitido no padrão canônico.")
                texto = bytes_conteudo.decode("utf-8")
        else:
            texto = texto_ou_caminho
    else:
        texto = texto_ou_caminho

    if texto.startswith("\ufeff"):
        raise ValueError("BOM UTF-8 não permitido no padrão canônico.")

    dados = json.loads(
        texto,
        parse_float=_rejeitar_float,
        object_pairs_hook=_par_sem_duplicatas,
    )
    verificar_profundidade(dados, 1, 32)
    return dados


def salvar_json_canonico(caminho: str, dados: Any) -> None:
    """Salva dados em formato JSON canônico formatado e determinístico."""
    dict_puro = converter_para_dict(dados)
    verificar_profundidade(dict_puro, 1, 32)
    texto = json.dumps(
        dict_puro,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
        f.write("\n")


def deserializar_projeto(dados: Dict[str, Any]) -> ProjetoViga:
    """Reconstrói um objeto ProjetoViga a partir de um dicionário deserializado."""
    identificacao = dados.get("identificacao", "Viga de Concreto NBR 6118")

    # Seção
    d_sec = dados.get("secao", {})
    secao = SecaoViga(
        largura_bw_cm=deserializar_fracao(d_sec.get("largura_bw_cm", {"num": 20, "den": 1})),
        altura_h_cm=deserializar_fracao(d_sec.get("altura_h_cm", {"num": 50, "den": 1})),
        comprimento_vao_m=deserializar_fracao(d_sec.get("comprimento_vao_m", {"num": 5, "den": 1})),
        tipo_apoio=str(d_sec.get("tipo_apoio", "biapoiada")),
    )

    # Materiais
    d_mat = dados.get("materiais", {})
    c_nom_raw = d_mat.get("cobrimento_nominal_cm")
    materiais = PropriedadesMateriais(
        classe_concreto_fck=int(d_mat.get("classe_concreto_fck", 25)),
        tipo_aco_longitudinal=str(d_mat.get("tipo_aco_longitudinal", "CA_50")),
        tipo_aco_transversal=str(d_mat.get("tipo_aco_transversal", "CA_50")),
        classe_agressividade=str(d_mat.get("classe_agressividade", "CAA_II")),
        cobrimento_nominal_cm=deserializar_fracao(c_nom_raw) if c_nom_raw is not None else None,
    )

    # Esforços
    d_esf = dados.get("esforcos", {})
    mk_d_raw = d_esf.get("momento_fletor_d_kNm")
    vk_d_raw = d_esf.get("forca_cortante_d_kN")
    esforcos = EsforcosSolicitantes(
        momento_fletor_k_kNm=deserializar_fracao(d_esf.get("momento_fletor_k_kNm", {"num": 50, "den": 1})),
        forca_cortante_k_kN=deserializar_fracao(d_esf.get("forca_cortante_k_kN", {"num": 40, "den": 1})),
        momento_fletor_d_kNm=deserializar_fracao(mk_d_raw) if mk_d_raw is not None else None,
        forca_cortante_d_kN=deserializar_fracao(vk_d_raw) if vk_d_raw is not None else None,
    )

    # Detalhamento
    d_det = dados.get("detalhamento", {})
    bit_l_raw = d_det.get("bitola_longitudinal_sugerida_mm")
    bit_t_raw = d_det.get("bitola_estribo_sugerida_mm")
    detalhamento = PreferenciasDetalhamento(
        bitola_longitudinal_sugerida_mm=deserializar_fracao(bit_l_raw) if bit_l_raw is not None else None,
        bitola_estribo_sugerida_mm=deserializar_fracao(bit_t_raw) if bit_t_raw is not None else None,
        numero_ramos_estribo=int(d_det.get("numero_ramos_estribo", 2)),
        d_linha_estimado_cm=deserializar_fracao(d_det.get("d_linha_estimado_cm", {"num": 4, "den": 1})),
    )

    return ProjetoViga(
        identificacao=identificacao,
        secao=secao,
        materiais=materiais,
        esforcos=esforcos,
        detalhamento=detalhamento,
    )
