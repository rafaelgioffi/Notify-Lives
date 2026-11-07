"""Carregamento dos perfis de divulgação salvos em arquivos JSON."""

import json
import os


PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
PASTA_PERFIS = os.path.join(PASTA_PROJETO, "perfis")


def _ler_perfil(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        perfil = json.load(arquivo)
    perfil["arquivo"] = caminho
    perfil["caminho_imagem"] = os.path.join(PASTA_PROJETO, perfil["imagem"])
    perfil["caminho_video"] = os.path.join(PASTA_PROJETO, perfil["video"])
    return perfil


def carregar_perfis():
    perfis = {}
    for nome_arquivo in sorted(os.listdir(PASTA_PERFIS)):
        if nome_arquivo.lower().endswith(".json"):
            perfil = _ler_perfil(os.path.join(PASTA_PERFIS, nome_arquivo))
            perfis[perfil["id"]] = perfil
    return perfis


PERFIS = carregar_perfis()


def obter_perfil(nome):
    try:
        return PERFIS[nome].copy()
    except KeyError as erro:
        disponiveis = ", ".join(sorted(PERFIS))
        raise ValueError(f"Perfil '{nome}' não existe. Disponíveis: {disponiveis}") from erro
