import csv
import hashlib
import io
import json
import os
import time
import urllib.request
from pathlib import Path

BASE_URL = os.environ["SHEET_GVIZ_URL"]
URL = f"{BASE_URL}&_={int(time.time())}"

DEST = Path("dados/ocorrencias.json")

request = urllib.request.Request(
    URL,
    headers={"User-Agent": "Mozilla/5.0 GitHubActions-OperacaoEleicoes2026/1.0"},
)

with urllib.request.urlopen(request, timeout=30) as response:
    raw = response.read().decode("utf-8-sig")

rows = list(csv.DictReader(io.StringIO(raw)))

def clean(value):
    return (value or "").strip()

def get_value(row, *names):
    for name in names:
        if name in row:
            value = clean(row[name])
            if value:
                return value
    return ""

def normalize_zone(value):
    return (
        clean(value)
        .replace("º", "")
        .replace("°", "")
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
    timestamp = get_value(row, "Timestamp", "carimbo de data/hora")
    responsavel = get_value(
        row,
        "Responsável pelo Registro",
        "Responsável",
        "responsavel",
        "responsável",
    )
    zona = normalize_zone(get_value(row, "Zona", "zona"))
    local = get_value(row, "Local", "local")
    tipo = get_value(row, "Tipo", "tipo")
    gravidade = get_value(row, "Gravidade", "gravidade")
    relato = get_value(row, "Relato", "relato")

    key = "|".join([
        timestamp, responsavel, zona, local, tipo, gravidade, relato
    ])

    record_id = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]

    output.append({
        "id": record_id,
        "timestamp": timestamp,
        "responsavel": responsavel,
        "zona": zona,
        "local": local,
        "tipo": tipo,
        "gravidade": gravidade,
        "relato": public_summary(tipo, gravidade),
    })

DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(
    json.dumps(output, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"Sincronizados {len(output)} registros")
print(f"Com responsável informado: {sum(1 for x in output if x['responsavel'])}")
