#!/usr/bin/env python3
"""
Fetch VM prices from Scaleway, AWS EC2, and OVHcloud for Paris region.
Outputs: data/prices.json
"""

import gzip
import json
import urllib.request
import os
from datetime import datetime, timezone

SCALEWAY_URL = "https://api.scaleway.com/instance/v1/zones/fr-par-1/products/servers"
AWS_URL = (
    "https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/"
    "ec2-ondemand-without-sec-sel/EU%20%28Paris%29/Linux/index.json"
)
OVH_URL = "https://eu.api.ovh.com/1.0/order/catalog/public/cloud?ovhSubsidiary=FR"


def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "cloud-price-tracker/1.0",
        "Accept-Encoding": "gzip, deflate",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        # AWS returns gzip-compressed content
        if raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        return json.loads(raw)


def fetch_scaleway():
    data = fetch_json(SCALEWAY_URL)
    results = []
    for name, s in data.get("servers", {}).items():
        results.append({
            "name": name,
            "vcpu": s["ncpus"],
            "ram_gb": round(s["ram"] / (1024 ** 3), 1),
            "gpu": s.get("gpu", 0),
            "arch": s.get("arch", "x86_64"),
            "hourly_usd": None,
            "hourly_eur": s["hourly_price"],
            "monthly_eur": s["monthly_price"],
            "monthly_usd": None,
            "currency": "EUR",
            "end_of_service": s.get("end_of_service", False),
        })
    results.sort(key=lambda x: x["monthly_eur"])
    return results


def fetch_aws():
    data = fetch_json(AWS_URL)
    # Structure: { "regions": { "EU (Paris)": { "<name> <size> EU Paris Linux": { ... } } } }
    regions = data.get("regions", {})
    paris = regions.get("EU (Paris)", {})
    results = []
    seen = set()
    for _key, info in paris.items():
        try:
            name = info.get("Instance Type", "")
            if not name or name in seen:
                continue
            seen.add(name)
            vcpu = int(info.get("vCPU", 0))
            ram_str = info.get("Memory", "0 GiB").replace(" GiB", "").replace(",", "")
            ram_gb = float(ram_str)
            price_str = info.get("price", "0")
            hourly = float(price_str)
            # Detect ARM (Graviton) by name prefix
            arch = "arm64" if any(name.startswith(p) for p in ["a1", "m6g", "m7g", "m8g", "c6g", "c7g", "c8g", "r6g", "r7g", "r8g", "t4g", "im4g", "is4g", "hpc7g"]) else "x86_64"
            results.append({
                "name": name,
                "vcpu": vcpu,
                "ram_gb": round(ram_gb, 1),
                "gpu": 0,
                "arch": arch,
                "hourly_usd": hourly,
                "hourly_eur": None,
                "monthly_usd": round(hourly * 730, 4),
                "monthly_eur": None,
                "currency": "USD",
                "end_of_service": False,
            })
        except (ValueError, TypeError):
            continue
    results.sort(key=lambda x: x["hourly_usd"])
    return results


def fetch_ovh():
    data = fetch_json(OVH_URL)

    # Collect all instance addon codes from all plans' instance families
    instance_addon_codes = set()
    for plan in data.get("plans", []):
        for fam in plan.get("addonFamilies", []):
            if fam.get("name") == "instance":
                instance_addon_codes.update(fam.get("addons", []))

    # Build a lookup of addons by planCode
    addon_by_code = {a["planCode"]: a for a in data.get("addons", [])}

    results = []
    seen_names = set()

    for code in instance_addon_codes:
        addon = addon_by_code.get(code)
        if not addon:
            continue

        # Only consumption billing (hourly) addons; skip monthly/postpaid duplicates
        if not code.endswith(".consumption"):
            continue

        blobs = addon.get("blobs") or {}
        technical = blobs.get("technical") or {}
        cpu = technical.get("cpu") or {}
        memory = technical.get("memory") or {}
        gpu_info = technical.get("gpu") or {}

        vcpu = cpu.get("cores", 0)
        ram_mb = memory.get("size", 0)
        ram_gb = round(ram_mb / 1024, 1) if ram_mb else 0
        gpu_count = gpu_info.get("number", 0) if isinstance(gpu_info, dict) else 0

        # Determine arch from commercial brick or name
        commercial = blobs.get("commercial") or {}
        brick = commercial.get("brick", "")
        # ARM instances are typically named with 'a1' prefix
        name = addon.get("invoiceName", code)
        arch = "arm64" if name.lower().startswith("a1-") else "x86_64"

        # Find hourly consumption price (price is in 10^-8 EUR)
        hourly_eur = None
        for pricing in addon.get("pricings", []):
            if "consumption" in pricing.get("capacities", []):
                raw_price = pricing.get("price", 0)
                hourly_eur = round(raw_price / 1e8, 6)
                break

        if hourly_eur is None:
            continue

        # Deduplicate by instance name
        if name in seen_names:
            continue
        seen_names.add(name)

        monthly_eur = round(hourly_eur * 730, 4)
        results.append({
            "name": name,
            "plan_code": code,
            "vcpu": vcpu,
            "ram_gb": ram_gb,
            "gpu": gpu_count,
            "arch": arch,
            "hourly_usd": None,
            "hourly_eur": hourly_eur,
            "monthly_eur": monthly_eur,
            "monthly_usd": None,
            "currency": "EUR",
            "end_of_service": False,
        })
    results.sort(key=lambda x: (x["hourly_eur"] or 0))
    return results


def main():
    os.makedirs("data", exist_ok=True)

    print("Fetching Scaleway...")
    scaleway = fetch_scaleway()
    print(f"  → {len(scaleway)} instance types")

    print("Fetching AWS EC2 (EU Paris)...")
    aws = fetch_aws()
    print(f"  → {len(aws)} instance types")

    print("Fetching OVHcloud...")
    ovh = fetch_ovh()
    print(f"  → {len(ovh)} instance types")

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "region": "Paris (fr-par)",
        "providers": {
            "scaleway": {
                "name": "Scaleway",
                "currency": "EUR",
                "instances": scaleway,
            },
            "aws": {
                "name": "AWS EC2",
                "currency": "USD",
                "instances": aws,
            },
            "ovh": {
                "name": "OVHcloud",
                "currency": "EUR",
                "instances": ovh,
            },
        },
    }

    with open("data/prices.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved data/prices.json")
    print(f"  Scaleway: {len(scaleway)}, AWS: {len(aws)}, OVH: {len(ovh)}")


if __name__ == "__main__":
    main()
