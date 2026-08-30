"""Firestore-backed SchedulingConfigRepository (docs/05-DATABASE.md #19):
a singleton document, `schools/{schoolId}/schedulingConfig/current`.
Runtime-verified in Phase 10 — see generic_firestore.py's module
docstring.
"""

from google.cloud.firestore import Client

from app.domain.scheduling import SchedulingConfig

_DOCUMENT_ID = "current"


def _to_document(config: SchedulingConfig) -> dict[str, object]:
    return {
        "softConstraintWeights": dict(config.soft_constraint_weights),
        "solver": {
            "timeoutSeconds": config.timeout_seconds,
            "randomSeed": config.random_seed,
            "initialTemperature": config.initial_temperature,
            "coolingRate": config.cooling_rate,
            "minTemperature": config.min_temperature,
            "qualityDecayK": config.quality_decay_k,
        },
    }


def _from_document(data: dict[str, object]) -> SchedulingConfig:
    solver = data.get("solver", {})
    assert isinstance(solver, dict)
    defaults = SchedulingConfig()
    return SchedulingConfig(
        timeout_seconds=float(solver.get("timeoutSeconds", defaults.timeout_seconds)),
        random_seed=int(solver.get("randomSeed", defaults.random_seed)),
        soft_constraint_weights=dict(
            data.get("softConstraintWeights", defaults.soft_constraint_weights)  # type: ignore[arg-type]
        ),
        initial_temperature=float(solver.get("initialTemperature", defaults.initial_temperature)),
        cooling_rate=float(solver.get("coolingRate", defaults.cooling_rate)),
        min_temperature=float(solver.get("minTemperature", defaults.min_temperature)),
        quality_decay_k=float(solver.get("qualityDecayK", defaults.quality_decay_k)),
    )


class FirestoreSchedulingConfigRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def get(self, school_id: str) -> SchedulingConfig:
        doc_ref = (
            self._client.collection("schools")
            .document(school_id)
            .collection("schedulingConfig")
            .document(_DOCUMENT_ID)
        )
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return SchedulingConfig()
        return _from_document(snapshot.to_dict() or {})

    def save(self, school_id: str, config: SchedulingConfig) -> None:
        doc_ref = (
            self._client.collection("schools")
            .document(school_id)
            .collection("schedulingConfig")
            .document(_DOCUMENT_ID)
        )
        doc_ref.set(_to_document(config))
