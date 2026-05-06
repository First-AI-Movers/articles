#!/usr/bin/env python3
"""One-shot field verification probe (E41g pre-flight).

Confirms whether a named field exists on the Airtable table the cron
reads. Two probe strategies, in order:

  1. Meta API: GET /v0/meta/bases/{baseId}/tables and enumerate field
     names. Requires `schema.bases:read` PAT scope. Reports the table
     and field-name list when it succeeds; reports 403 cleanly when the
     scope is missing.
  2. Data API sort probe: GET /v0/{baseId}/{tableId}?maxRecords=1&
     sort[0][field]=<field>&sort[0][direction]=desc. If Airtable
     accepts the request the field exists; if it returns 422
     UNKNOWN_FIELD_NAME, it does not.

Outputs: a single PASS or FAIL line plus the evidence. Never prints
records, secrets, or article body data. Safe to run from a workflow
step that already has `AIRTABLE_PAT` etc. in env.

Delete this file after E41g is verified.
"""

import os
import sys

import requests


def _meta_probe(pat, base_id, table_name, field_name):
    headers = {"Authorization": f"Bearer {pat}"}
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 403:
        return ("scope-missing", "PAT lacks schema.bases:read; meta probe unavailable")
    resp.raise_for_status()
    tables = resp.json().get("tables", [])
    table = next(
        (t for t in tables if t.get("id") == table_name or t.get("name") == table_name),
        None,
    )
    if not table:
        names = [t.get("name") for t in tables]
        return ("table-missing", f"Table '{table_name}' not found. Visible: {names}")
    field_names = [f.get("name") for f in table.get("fields", [])]
    if field_name in field_names:
        return ("found", f"Table '{table.get('name')}' has field '{field_name}'.")
    return (
        "field-missing",
        f"Table '{table.get('name')}' fields: {sorted(field_names)}. "
        f"'{field_name}' is NOT present.",
    )


def _data_sort_probe(pat, base_id, table_name, field_name):
    headers = {"Authorization": f"Bearer {pat}"}
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    params = {
        "maxRecords": "1",
        "sort[0][field]": field_name,
        "sort[0][direction]": "desc",
        "fields[]": field_name,
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code == 200:
        return ("found", f"Data API accepts sort by '{field_name}'.")
    if resp.status_code == 422:
        try:
            err = resp.json().get("error", {})
        except Exception:
            err = {}
        return (
            "field-missing",
            f"Data API 422 {err.get('type')}: {err.get('message')}",
        )
    resp.raise_for_status()
    return ("unknown", f"unexpected status {resp.status_code}")


def main():
    pat = os.environ.get("AIRTABLE_PAT", "").strip()
    base_id = os.environ.get("AIRTABLE_BASE_ID", "").strip()
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "").strip()
    field_name = os.environ.get("AIRTABLE_VERIFY_FIELD", "Date Added").strip()

    if not pat or not base_id or not table_name:
        print("FAIL: missing required env (AIRTABLE_PAT/BASE_ID/TABLE_NAME).")
        return 2

    print(f"Probing Airtable for field: '{field_name}'")
    print(f"  base id length: {len(base_id)} chars (value redacted)")
    print(f"  table identifier length: {len(table_name)} chars (value redacted)")

    status, detail = _meta_probe(pat, base_id, table_name, field_name)
    print(f"meta probe: {status} :: {detail}")
    if status == "found":
        print(f"PASS: '{field_name}' exists.")
        return 0
    if status == "field-missing" or status == "table-missing":
        print(f"FAIL: {detail}")
        return 1

    # Fall back to data-API sort probe.
    status2, detail2 = _data_sort_probe(pat, base_id, table_name, field_name)
    print(f"data-sort probe: {status2} :: {detail2}")
    if status2 == "found":
        print(f"PASS: '{field_name}' exists (verified via sort acceptance).")
        return 0
    print(f"FAIL: '{field_name}' not verifiable. Stop and report.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
