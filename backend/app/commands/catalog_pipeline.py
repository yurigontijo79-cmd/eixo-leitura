import argparse
import json

from app.core.db import (
    initialize_database,
    ingest_catalog_records,
    inspect_ingestion_batch,
    inspect_staging_record,
    summarize_ingestion_batch,
)


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


if __name__ == "__main__":
    main()
