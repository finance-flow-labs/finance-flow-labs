from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDescriptor:
    name: str
    utility: int
    reliability: int
    legal: int
    cost: int
    maintenance: int


@dataclass(frozen=True)
class SourceEvaluation:
    admitted: bool
    score: float


def evaluate_source(source: SourceDescriptor) -> SourceEvaluation:
    score = (
        source.utility * 30
        + source.reliability * 25
        + source.legal * 20
        + source.cost * 15
        + source.maintenance * 10
    ) / 5
    admitted = source.legal >= 3 and source.reliability >= 3
    return SourceEvaluation(admitted=admitted, score=score)
