#!/usr/bin/env python3
"""Insert a minimal canonical org hierarchy (BDE -> BN -> CO -> STN).

Safe to run multiple times: checks for existing prefixes/rsids and skips duplicates.
"""
from services.api.app import database, models


HIER = [
    {
        "bde": "1",
        "bns": [
            {
                "bn": "11",
                "cos": [
                    {"co": "111", "stns": ["1111", "1112"]},
                    {"co": "112", "stns": ["1121"]},
                ],
            },
            {
                "bn": "12",
                "cos": [
                    {"co": "121", "stns": ["1211"]},
                ],
            },
        ],
    },
    {
        "bde": "2",
        "bns": [
            {
                "bn": "21",
                "cos": [
                    {"co": "211", "stns": ["2111"]},
                ],
            }
        ],
    },
]


def main():
    db = database.SessionLocal()
    created = 0
    try:
        for b in HIER:
            bde = db.query(models.Brigade).filter_by(brigade_prefix=b["bde"]).first()
            if not bde:
                bde = models.Brigade(brigade_prefix=b["bde"], display=f"Brigade {b['bde']}")
                db.add(bde)
                db.flush()
                created += 1

            for bn in b.get("bns", []):
                batt = db.query(models.Battalion).filter_by(battalion_prefix=bn["bn"], brigade_id=bde.id).first()
                if not batt:
                    batt = models.Battalion(battalion_prefix=bn["bn"], display=f"Battalion {bn['bn']}", brigade_id=bde.id)
                    db.add(batt)
                    db.flush()
                    created += 1

                for co in bn.get("cos", []):
                    comp = db.query(models.Company).filter_by(company_prefix=co["co"], battalion_id=batt.id).first()
                    if not comp:
                        comp = models.Company(company_prefix=co["co"], display=f"Company {co['co']}", battalion_id=batt.id)
                        db.add(comp)
                        db.flush()
                        created += 1

                    for st in co.get("stns", []):
                        stn = db.query(models.Station).filter_by(rsid=st).first()
                        if not stn:
                            stn = models.Station(rsid=st, display=f"Station {st}", company_id=comp.id)
                            db.add(stn)
                            created += 1

        db.commit()
        print(f"Done. Created {created} new org rows (0 means all already existed).")
    except Exception as e:
        db.rollback()
        raise
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
