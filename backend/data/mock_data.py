"""
mock_data.py — In-memory dataset for local development and testing.

Mirrors the five tables declared in data/schema.json (real Glue/Athena schema):
  cliente_parquet, loja_parquet, produtos_parquet, venda_parquet,
  dataset_completo_parquet

Each table is a list of plain dicts — same shape the real Athena connector
returns — so the execution_service can swap mock for real without changing
anything downstream.

Access via:
    from data.mock_data import MOCK_TABLES
    rows = MOCK_TABLES["venda_parquet"]
"""

import uuid
from datetime import date, timedelta
import random

random.seed(42)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid() -> str:
    return str(uuid.uuid4())


def _date(days_offset: int) -> str:
    return (date(2024, 1, 1) + timedelta(days=days_offset)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Lojas (10 filiais)
# ---------------------------------------------------------------------------

_LOJAS = [
    {"id_identificador": _uid(), "nm_filial": f"Filial {i:02d}", "nu_cnpj": f"00.000.000/{i:04d}-00",
     "ct_cidade": c, "sg_estado": e, "ds_endereco": f"Av. Principal", "nu_endereco": i * 100,
     "ds_complemento": "", "fl_status": i % 5 != 0}
    for i, (c, e) in enumerate([
        ("São Paulo", "SP"), ("Rio de Janeiro", "RJ"), ("Belo Horizonte", "MG"),
        ("Curitiba", "PR"), ("Porto Alegre", "RS"), ("Salvador", "BA"),
        ("Fortaleza", "CE"), ("Recife", "PE"), ("Manaus", "AM"), ("Brasília", "DF"),
    ], start=1)
]

# ---------------------------------------------------------------------------
# Produtos (15 itens)
# ---------------------------------------------------------------------------

_CATEGORIAS = ["Eletrônicos", "Vestuário", "Alimentos", "Esportes", "Casa"]
_PRODUTOS = [
    {"id_identificador": _uid(), "nm_nome": f"Produto {i:02d}",
     "ds_descricao": f"Descrição do produto {i:02d}",
     "nm_categoria": _CATEGORIAS[i % len(_CATEGORIAS)],
     "vl_preco_unitario": round(29.90 + i * 15.50, 2),
     "qt_estoque": random.randint(0, 500)}
    for i in range(1, 16)
]

# ---------------------------------------------------------------------------
# Clientes (30 registros)
# ---------------------------------------------------------------------------

_CIDADES_EST = [
    ("São Paulo", "SP"), ("Rio de Janeiro", "RJ"), ("Curitiba", "PR"),
    ("Belo Horizonte", "MG"), ("Porto Alegre", "RS"), ("Salvador", "BA"),
]
_CLIENTES = [
    {
        "id_identificador": _uid(),
        "nm_nome": f"Nome{i:02d}",
        "ds_sobrenome": f"Sobrenome{i:02d}",
        "nu_cpf": f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}",
        "dt_nascimento": _date(-(365 * random.randint(20, 60))),
        "ct_cidade": _CIDADES_EST[i % len(_CIDADES_EST)][0],
        "sg_estado": _CIDADES_EST[i % len(_CIDADES_EST)][1],
        "ds_endereco": f"Rua {i:02d}",
        "nu_endereco": i * 10,
        "ds_complemento": f"Apto {i}",
        "nu_cep": f"{10000 + i:05d}-{i:03d}",
        "ds_email": f"cliente{i:02d}@email.com",
        "nu_telefone": f"(11) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
    }
    for i in range(1, 31)
]

# ---------------------------------------------------------------------------
# Vendas (100 registros)
# ---------------------------------------------------------------------------

_VENDAS = []
for i in range(100):
    produto = random.choice(_PRODUTOS)
    cliente = random.choice(_CLIENTES)
    loja = random.choice(_LOJAS)
    qtd = random.randint(1, 10)
    _VENDAS.append({
        "id_venda":          _uid(),
        "id_loja":           loja["id_identificador"],
        "id_cliente":        cliente["id_identificador"],
        "id_produto":        produto["id_identificador"],
        "qt_quantidade":     qtd,
        "vl_total_venda":    round(produto["vl_preco_unitario"] * qtd, 2),
        "dt_venda":          _date(random.randint(0, 364)),
        "nm_cliente":        f"{cliente['nm_nome']} {cliente['ds_sobrenome']}",
        "nm_filial":         loja["nm_filial"],
        "nm_produto":        produto["nm_nome"],
        "nm_categoria":      produto["nm_categoria"],
        "vl_preco_unitario": produto["vl_preco_unitario"],
    })

# ---------------------------------------------------------------------------
# dataset_completo_parquet — single-row consolidated view (mock as flat dict)
# ---------------------------------------------------------------------------

_DATASET_COMPLETO = [
    {
        "lojas":    str(_LOJAS),
        "produtos": str(_PRODUTOS),
        "clientes": str(_CLIENTES),
        "vendas":   str(_VENDAS),
    }
]

# ---------------------------------------------------------------------------
# Public export
# ---------------------------------------------------------------------------

MOCK_TABLES = {
    "cliente_parquet":           _CLIENTES,
    "loja_parquet":              _LOJAS,
    "produtos_parquet":          _PRODUTOS,
    "venda_parquet":             _VENDAS,
    "dataset_completo_parquet":  _DATASET_COMPLETO,
}
