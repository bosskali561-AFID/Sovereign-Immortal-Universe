#!/usr/bin/env python3
"""Run one offline paper-mode L.S.P.A. cycle from the command line.

Usage: python scripts/run_lspa_cycle.py [seed] [top_n]
"""
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import Base  # noqa: E402
import app.models  # noqa: F401,E402  (register ORM mappings)
from app.services.lspa import run_lspa_cycle  # noqa: E402

Path("data").mkdir(exist_ok=True)
engine = create_engine("sqlite:///./data/app.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 2

doc = run_lspa_cycle(sessionmaker(bind=engine)(), seed=seed, top_n=top_n)
print(json.dumps(doc, indent=2))
