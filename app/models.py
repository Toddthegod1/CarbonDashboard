from dataclasses import dataclass

@dataclass
class Activity:
    id: int
    ts: str
    category: str
    amount: float
    unit: str
    note: str
    kg_co2e: float