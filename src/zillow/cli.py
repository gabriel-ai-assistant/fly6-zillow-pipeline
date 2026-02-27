from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from .download import download_all
from .ingest import init_db, ingest_all
from .verify_urls import verify_all


def _valid_mode(value: str) -> str:
    if value not in {'ltr', 'flip', 'both'}:
        raise argparse.ArgumentTypeError('mode must be one of: ltr, flip, both')
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='zillow')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('init', help='Initialize SQLite DB and seed series metadata')

    verify_parser = sub.add_parser('verify-urls', help='Verify enabled dataset URLs')
    verify_parser.add_argument('--mode', type=_valid_mode, default='both')

    refresh_parser = sub.add_parser('refresh', help='Download and ingest Zillow datasets')
    refresh_parser.add_argument('--mode', type=_valid_mode, default='both')
    refresh_parser.add_argument('--date', default=date.today().isoformat())

    sub.add_parser('build-zip-cbsa', help='Build ZIP-to-CBSA crosswalk')

    args = parser.parse_args(argv)

    if args.command == 'init':
        conn = init_db()
        conn.close()
        print('initialized')
        return 0

    if args.command == 'verify-urls':
        results, code = verify_all(args.mode)
        print(json.dumps(results, indent=2))
        return code

    if args.command == 'refresh':
        init_conn = init_db()
        init_conn.close()
        manifest = download_all(args.mode, args.date)
        summary = ingest_all(args.mode, args.date)
        print(json.dumps({'manifest': manifest, 'ingest': summary}, indent=2))
        return 0

    if args.command == 'build-zip-cbsa':
        try:
            from . import zip_cbsa

            if hasattr(zip_cbsa, 'build'):
                zip_cbsa.build()
                print('zip-cbsa build complete')
                return 0
            print('zip_cbsa.build is not implemented yet')
            return 1
        except Exception as exc:
            print(f'zip_cbsa build failed: {exc}', file=sys.stderr)
            return 1

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
