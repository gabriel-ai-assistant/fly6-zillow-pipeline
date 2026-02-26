from __future__ import annotations

import argparse
import json
from datetime import date

from .init_db import init_db
from .refresh import run_refresh
from .verify_urls import verify_all
from .zip_cbsa import build_zip_to_cbsa


def main() -> None:
    parser = argparse.ArgumentParser(prog="zillow")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    p_verify = sub.add_parser("verify-urls")
    p_verify.add_argument("--mode", choices=["ltr", "flip", "both"], default="both")

    p_refresh = sub.add_parser("refresh")
    p_refresh.add_argument("--mode", choices=["ltr", "flip", "both"], default="both")
    p_refresh.add_argument("--date", dest="run_date", default=date.today().isoformat())

    sub.add_parser("build-zip-cbsa")

    args = parser.parse_args()

    if args.cmd == "init":
        init_db()
        print(json.dumps({"status": "ok", "action": "init"}))
        return
    if args.cmd == "verify-urls":
        print(json.dumps(verify_all(mode=args.mode), indent=2))
        return
    if args.cmd == "refresh":
        init_db()
        print(json.dumps(run_refresh(mode=args.mode, run_date=args.run_date), indent=2))
        return
    if args.cmd == "build-zip-cbsa":
        init_db()
        print(json.dumps(build_zip_to_cbsa(), indent=2))
        return


if __name__ == "__main__":
    main()
