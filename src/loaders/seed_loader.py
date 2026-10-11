from pathlib import Path
from typing import Dict, Iterator, List, Optional

from src.models.seed_schema import SeedRecord
from src.utils.io import read_jsonl


class SeedLoader:
    def __init__(self, input_path: Path):
        self.input_path = input_path

    def iter_raw(self) -> Iterator[Dict]:
        if not self.input_path.exists():
            raise FileNotFoundError(
                f"Seed input file not found: {self.input_path}. "
                "Pass --input with the correct seed path or use data/seed_ex.jsonl."
            )
        return read_jsonl(self.input_path)

    def iter_validated(self) -> Iterator[SeedRecord]:
        for record in self.iter_raw():
            yield SeedRecord.from_dict(record)

    def load_all(self) -> List[SeedRecord]:
        return list(self.iter_validated())

    def get_raw_by_id(self, seed_id: str) -> Optional[Dict]:
        for record in self.iter_raw():
            if record.get("seed_id") == seed_id:
                return record
        return None

    def get_by_id(self, seed_id: str) -> Optional[SeedRecord]:
        record = self.get_raw_by_id(seed_id)
        if record is None:
            return None
        return SeedRecord.from_dict(record)
