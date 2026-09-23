#!/usr/bin/env python3
"""Measure where OpenAI embedding latency is spent. Does not touch the app DB."""

from __future__ import annotations

import socket
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parent / ".env")


def timed(label: str):
    class _Timer:
        def __enter__(self):
            self.t0 = time.perf_counter()
            print(f"→ {label} ...", flush=True)
            return self

        def __exit__(self, exc_type, exc, tb):
            ms = (time.perf_counter() - self.t0) * 1000
            status = "FAIL" if exc else "ok"
            print(f"← {label}: {status} ({ms:.0f} ms)", flush=True)

    return _Timer()


def main() -> None:
    key = os.getenv("OPENAI_API_KEY")
    if not key or not key.strip():
        raise SystemExit("OPENAI_API_KEY missing in backend/.env")

    print("=== OpenAI latency probe ===")
    print(f"key prefix: {key[:8]}...")
    print()

    with timed("DNS resolve api.openai.com"):
        infos = socket.getaddrinfo("api.openai.com", 443, type=socket.SOCK_STREAM)
        print(f"   resolved {len(infos)} addr(s): {infos[0][4][0]}")

    with timed("TCP connect api.openai.com:443"):
        sock = socket.create_connection(("api.openai.com", 443), timeout=20)
        sock.close()

    with timed("HTTPS GET https://api.openai.com/v1/models (auth)"):
        req = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read(200)
            print(f"   status={resp.status}, first_bytes={len(body)}")

    with timed("import openai"):
        from openai import OpenAI

    with timed("create OpenAI client"):
        client = OpenAI(api_key=key, timeout=60.0)

    with timed("embeddings 1 short text"):
        r = client.embeddings.create(
            model="text-embedding-3-small",
            input=["latency probe"],
            dimensions=1536,
        )
        print(f"   dim={len(r.data[0].embedding)}")

    batch = [f"review sample text number {i}" for i in range(51)]
    with timed("embeddings batch of 51 texts (like one product)"):
        r = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch,
            dimensions=1536,
        )
        print(f"   vectors={len(r.data)}, dim={len(r.data[0].embedding)}")

    with timed("chat.completions tiny call (gpt-4o-mini)"):
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Reply with OK"}],
            max_tokens=5,
        )
        print(f"   reply={r.choices[0].message.content!r}")

    print()
    print("Done. Compare steps: if DNS/TCP already slow → network. "
          "If only embeddings/chat slow → OpenAI API path.")


if __name__ == "__main__":
    main()
