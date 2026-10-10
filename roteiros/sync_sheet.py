import csv
import hashlib
import io
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = os.environ["SHEET_GVIZ_URL"]
DEST = Path("dados/ocorrencias.json")


def fetch_csv():
    # Tenta novamente em caso de falha temporária ou resposta vazia do Google.
    last_error = None
    for attempt in range(1, 4):
        url = f"{BASE_URL}&_={int(time.time())}-{attempt}"
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 GitHubActions-OperacaoEleicoes2026/1.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8-sig")
            if not raw.strip():
                raise RuntimeError("O Google retornou um CSV vazio.")
            # Google pode responder HTML em vez de CSV quando há falha temporária.
            if raw.lstrip().lower().startswith("<!doctype html") or "<html" in raw[:500].lower():
                raise RuntimeError("O Google retornou HTML em vez de CSV.")
            return raw
        except Exception as exc:
            last_error = exc
            print(f"Tentativa {attempt}/3 falhou: {exc}")
            if attempt < 3:
                time.sleep(3 * attempt)
    raise RuntimeError(f"Não foi possível obter a planilha após 3 tentativas: {last_error}")


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


def main():
    started = datetime.now(timezone.utc).isoformat()
    raw = fetch_csv()
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    print(f"Início UTC: {started}")
    print(f"Cabeçalhos recebidos: {reader.fieldnames}")
    print(f"Linhas de dados recebidas da planilha: {len(rows)}")

    if not reader.fieldnames or not rows:
        raise RuntimeError("A planilha não retornou cabeçalhos ou linhas de dados; JSON não será sobrescrito.")

    output = []
    for row in rows:
        timestamp = get_value(row, "Timestamp", "carimbo de data/hora", "Carimbo de data/hora")
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

        key = "|".join([timestamp, responsavel, zona, local, tipo, gravidade, relato])
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

    # Protege contra sobrescrever o JSON com uma leitura inesperadamente menor.
    if DEST.exists():
        try:
            previous = json.loads(DEST.read_text(encoding="utf-8"))
            if isinstance(previous, list) and len(output) < len(previous):
                raise RuntimeError(
                    f"A planilha retornou {len(output)} registros, mas o JSON atual tem "
                    f"{len(previous)}. JSON preservado para evitar perda de dados."
                )
        except json.JSONDecodeError:
            print("Aviso: JSON anterior inválido; será substituído por dados válidos da planilha.")

    DEST.parent.mkdir(parents=True, exist_ok=True)
    temp_dest = DEST.with_suffix(".json.tmp")
    temp_dest.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_dest.replace(DEST)

    latest = max((x["timestamp"] for x in output if x["timestamp"]), default="não disponível")
    print(f"Maior data/hora recebida (texto): {latest}")
    print(f"Sincronizados {len(output)} registros")
    print(f"Com responsável informado: {sum(1 for x in output if x['responsavel'])}")
    print(f"Arquivo gravado: {DEST.as_posix()}")
    print(f"Conclusão UTC: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
