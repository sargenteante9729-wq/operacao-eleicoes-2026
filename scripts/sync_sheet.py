import csv
import hashlib
import io
import json
import os
import time
import urllib.request
from pathlib import Path

BASE_URL = os.environ["SHEET_GVIZ_URL"]

# Evita que o Google entregue uma versão antiga em cache
separator = "&" if "?" in BASE_URL else "?"
URL = f"{BASE_URL}{separator}_={int(time.time())}"

DEST = Path("data/ocorrencias.json")

request = urllib.request.Request(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0 GitHubActions-OperacaoEleicoes2026/1.0"
    },
)

with urllib.request.urlopen(request, timeout=30) as response:
    raw = response.read().decode("utf-8-sig")

rows = list(csv.DictReader(io.StringIO(raw)))


def clean(value):
    return (value or "").strip()


def normalize_zone(value):
    return (
        clean(value)
        .replace("º", "")
        .replace("ZONA", "")
        .strip()
        .zfill(2)
    )


def public_summary(tipo, gravidade):
    return (
        f"Ocorrência registrada: {tipo or 'não informado'} — "
        f"gravidade {gravidade or 'não informada'}."
    )


output = []

for row in rows:
    timestamp = clean(row.get("Timestamp"))
    zona = normalize_zone(row.get("Zona"))
    local = clean(row.get("Local"))
    tipo = clean(row.get("Tipo"))
    gravidade = clean(row.get("Gravidade"))
    relato = clean(row.get("Relato"))

    key = "|".join([
        timestamp,
        zona,
        local,
        tipo,
        gravidade,
        relato
    ])

    record_id = hashlib.sha1(
        key.encode("utf-8")
    ).hexdigest()[:12]

    output.append({
        "id": record_id,
        "timestamp": timestamp,
        "zona": zona,
        "local": local,
        "tipo": tipo,
        "gravidade": gravidade,
        "relato": public_summary(tipo, gravidade),
    })


DEST.parent.mkdir(parents=True, exist_ok=True)

DEST.write_text(
    json.dumps(
        output,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8",
)

print(f"Sincronizados {len(output)} registros")
