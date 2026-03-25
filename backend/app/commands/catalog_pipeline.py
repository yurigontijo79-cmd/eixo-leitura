import argparse
import json
import time
from pathlib import Path

from app.core.db import (
    initialize_database,
    ingest_catalog_records,
    inspect_ingestion_batch,
    inspect_staging_record,
    summarize_ingestion_batch,
)

DEFAULT_SEED_THROTTLE_SECONDS = 0.8


def _read_seed_file(seed_file: str, limit: int | None = None) -> list[str]:
    lines = Path(seed_file).read_text(encoding="utf-8").splitlines()
    seeds: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        seeds.append(line)
        if limit is not None and limit > 0 and len(seeds) >= limit:
            break
    return seeds


def _run_seed_batch(args: argparse.Namespace) -> dict:
    seeds = _read_seed_file(args.seed_file, limit=args.seed_limit)
    if not seeds:
        return {
            "source_name": args.source,
            "seed_file": args.seed_file,
            "seed_count_requested": 0,
            "seed_count_processed": 0,
            "message": "Nenhuma seed válida encontrada no arquivo (linhas vazias e comentários com # são ignorados).",
            "results": [],
            "consolidated": {
                "batches_created": 0,
                "records_fetched_total": 0,
                "records_promoted_total": 0,
                "records_retained_total": 0,
                "records_discarded_total": 0,
                "seeds_failed": 0,
                "seeds_with_promoted": 0,
                "seeds_without_promoted": 0,
            },
        }

    results: list[dict] = []
    fetched_total = 0
    promoted_total = 0
    retained_total = 0
    discarded_total = 0
    failed_count = 0
    promoted_seed_count = 0
    zero_promoted_seed_count = 0

    for index, seed in enumerate(seeds, start=1):
        if index > 1 and args.seed_throttle_seconds > 0:
            time.sleep(args.seed_throttle_seconds)

        result = ingest_catalog_records(
            args.source,
            query=seed,
            max_results=args.max_results,
            source_timeout=args.source_timeout,
            source_retry_max=args.retry_max if args.source == "google_books" else None,
            source_backoff_seconds=args.backoff_seconds if args.source == "google_books" else None,
            source_throttle_seconds=args.throttle_seconds if args.source == "open_library" else None,
        )
        fetched = int(result.get("records_fetched") or 0)
        promoted = int(result.get("records_promoted") or 0)
        retained = int(result.get("records_retained") or 0)
        discarded = int(result.get("records_discarded") or 0)
        status = result.get("status") or "unknown"

        fetched_total += fetched
        promoted_total += promoted
        retained_total += retained
        discarded_total += discarded
        if status != "completed":
            failed_count += 1
        if promoted > 0:
            promoted_seed_count += 1
        else:
            zero_promoted_seed_count += 1

        per_seed = {
            "seed": seed,
            "source_name": args.source,
            "batch_id": result.get("batch_id"),
            "status": status,
            "records_fetched": fetched,
            "records_promoted": promoted,
            "records_retained": retained,
            "records_discarded": discarded,
            "error": result.get("error"),
        }
        results.append(per_seed)

        print(
            f"[seed-batch] {index}/{len(seeds)} seed={seed!r} batch_id={per_seed['batch_id']} "
            f"status={status} fetched={fetched} promoted={promoted} retained={retained} discarded={discarded}"
        )

    return {
        "source_name": args.source,
        "seed_file": args.seed_file,
        "seed_count_requested": len(seeds),
        "seed_count_processed": len(results),
        "results": results,
        "consolidated": {
            "batches_created": len(results),
            "records_fetched_total": fetched_total,
            "records_promoted_total": promoted_total,
            "records_retained_total": retained_total,
            "records_discarded_total": discarded_total,
            "seeds_failed": failed_count,
            "seeds_with_promoted": promoted_seed_count,
            "seeds_without_promoted": zero_promoted_seed_count,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pipeline inicial de ingestão do catálogo EIXO Leitura")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_google = subparsers.add_parser("ingest_google_books", help="Executa ingestão real via Google Books")
    ingest_google.add_argument("--query", required=True, help="Consulta textual para o Google Books")
    ingest_google.add_argument("--max-results", type=int, default=20, help="Quantidade máxima de resultados")
    ingest_google.add_argument("--source-timeout", type=float, required=False, help="Timeout da fonte (segundos)")
    ingest_google.add_argument("--retry-max", type=int, required=False, help="Máximo de retries para Google Books")
    ingest_google.add_argument("--backoff-seconds", type=float, required=False, help="Backoff base para retry (segundos)")

    ingest_open = subparsers.add_parser("ingest_open_library", help="Executa ingestão real via Open Library")
    ingest_open.add_argument("--query", required=True, help="Consulta textual para Open Library")
    ingest_open.add_argument("--max-results", type=int, default=20, help="Quantidade máxima de resultados")
    ingest_open.add_argument("--source-timeout", type=float, required=False, help="Timeout da fonte (segundos)")
    ingest_open.add_argument("--throttle-seconds", type=float, required=False, help="Throttle entre chamadas Open Library (segundos)")

    amazon_stub = subparsers.add_parser("ingest_amazon_stub", help="Stub técnico da integração Amazon/Kindle")
    amazon_stub.add_argument("--query", required=True, help="Consulta planejada para futura integração")

    summary = subparsers.add_parser("summarize_ingestion_batch", help="Resume o resultado de um lote")
    summary.add_argument("--batch-id", required=True, type=int, help="ID do lote de ingestão")

    inspect_batch = subparsers.add_parser("inspect_ingestion_batch", help="Inspeciona um lote com detalhamento por decisão")
    inspect_batch.add_argument("--batch-id", required=True, type=int, help="ID do lote de ingestão")
    inspect_batch.add_argument("--limit", required=False, type=int, default=5, help="Limite de exemplos por status")

    inspect_record = subparsers.add_parser("inspect_staging_record", help="Inspeciona um registro de staging por ID")
    inspect_record.add_argument("--record-id", required=True, type=int, help="ID do registro de staging")

    seed_batch = subparsers.add_parser("ingest_seed_list", help="Executa ingestão em lote a partir de arquivo de seeds")
    seed_batch.add_argument("--source", choices=["google_books", "open_library"], required=True, help="Fonte de ingestão")
    seed_batch.add_argument("--seed-file", required=True, help="Arquivo texto com uma seed por linha")
    seed_batch.add_argument("--max-results", type=int, default=10, help="Quantidade máxima de resultados por seed (recomendado: 5-20)")
    seed_batch.add_argument("--seed-limit", type=int, required=False, help="Limite opcional de seeds processadas")
    seed_batch.add_argument(
        "--seed-throttle-seconds",
        type=float,
        default=DEFAULT_SEED_THROTTLE_SECONDS,
        help="Pausa entre seeds (segundos)",
    )
    seed_batch.add_argument("--source-timeout", type=float, required=False, help="Timeout da fonte (segundos)")
    seed_batch.add_argument("--retry-max", type=int, required=False, help="Máximo de retries para Google Books")
    seed_batch.add_argument("--backoff-seconds", type=float, required=False, help="Backoff base para retry no Google Books")
    seed_batch.add_argument("--throttle-seconds", type=float, required=False, help="Throttle da chamada Open Library")

    return parser


def main() -> None:
    initialize_database()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest_google_books":
        result = ingest_catalog_records(
            "google_books",
            query=args.query,
            max_results=args.max_results,
            source_timeout=args.source_timeout,
            source_retry_max=args.retry_max,
            source_backoff_seconds=args.backoff_seconds,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "ingest_open_library":
        result = ingest_catalog_records(
            "open_library",
            query=args.query,
            max_results=args.max_results,
            source_timeout=args.source_timeout,
            source_throttle_seconds=args.throttle_seconds,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "ingest_amazon_stub":
        payload = {
            "source_name": "amazon_kindle_stub",
            "status": "not_implemented",
            "query": args.query,
            "message": "Integração Amazon/Kindle preparada como stub técnico nesta fase; ingestão real ficará para próxima etapa controlada.",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "summarize_ingestion_batch":
        result = summarize_ingestion_batch(args.batch_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "inspect_ingestion_batch":
        result = inspect_ingestion_batch(args.batch_id, limit_per_status=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "inspect_staging_record":
        result = inspect_staging_record(args.record_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "ingest_seed_list":
        result = _run_seed_batch(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
