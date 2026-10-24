"""Flags: every check that fails, when, by how much, and whether a declared enabler covers it.

The brief allows only flags caused by declared hypothetical enablers. A flag with covered_by set
names the enabler that covers it; a flag without one is unresolved and must be fixed or explained.
"""


def check(name: str, value: float, limit: float, kind: str, unit: str = "", covered_by: str | None = None) -> dict:
    """One check result. kind "max": value must stay at or below limit; "min": at or above."""
    ok = value <= limit if kind == "max" else value >= limit
    return {"check": name, "value": value, "limit": limit, "kind": kind, "unit": unit, "ok": ok, "covered_by": covered_by}


class Flags:
    def __init__(self):
        self.items: dict[str, dict] = {}

    def record(self, result: dict, year: float) -> bool:
        """Keep a failed check (first and last year, how many times, worst value). Returns True if it failed."""
        if result["ok"]:
            return False
        f = self.items.get(result["check"])
        if f is None:
            f = self.items[result["check"]] = {**{k: result[k] for k in ("check", "limit", "kind", "unit", "covered_by")},
                                               "first_year": round(year, 1), "times": 0, "worst": result["value"]}
        f["last_year"] = round(year, 1)
        f["times"] += 1
        worse = result["value"] > f["worst"] if f["kind"] == "max" else result["value"] < f["worst"]
        if worse:
            f["worst"] = result["value"]
        return True

    def note(self, name: str, value: float, unit: str, covered_by: str, year: float = 0.0) -> None:
        """Record a place where the run relies on an enabler (beyond real-world capability): an allowed flag."""
        self.record({"check": name, "value": value, "limit": 0.0, "kind": "max", "unit": unit, "ok": False,
                     "covered_by": covered_by}, year)

    def summary(self) -> dict:
        items = sorted(self.items.values(), key=lambda f: (f["covered_by"] is not None, f["first_year"]))
        return {"unresolved": sum(1 for f in items if f["covered_by"] is None),
                "covered_by_enablers": sum(1 for f in items if f["covered_by"] is not None),
                "flags": items}
