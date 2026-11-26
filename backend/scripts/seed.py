"""
Seed placeholder for Field Service demo data.

Target (when models exist): 12 customers, 15 assets, 20 jobs, 5 technicians,
service history, fictional contacts only.

Usage (later):
  python -m scripts.seed
"""

from __future__ import annotations


def main() -> None:
    print("Field Service seed: PLACEHOLDER")
    print("No ORM models yet — skip until migrations land.")
    print(
        "Planned: org + dispatcher/tech users, 12 customers, 15 assets, "
        "20 work orders, checklists, and history for Service Memory demos."
    )


if __name__ == "__main__":
    main()
