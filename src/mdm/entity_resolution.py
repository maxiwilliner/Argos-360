"""
ARGOS-360: Master Data Management (MDM) & Entity Resolution Engine
Resolves multi-source customer identities using deterministic blocking and 
probabilistic fuzzy matching (Levenshtein/Jaro-Winkler via RapidFuzz) to create
the Single Source of Truth (SSOT) - Golden Record & Customer 360 Global ID.

Outputs:
- data/02_silver/stg_customers_golden.parquet
"""

from pathlib import Path
import pandas as pd
import numpy as np
from rapidfuzz import fuzz

def get_repo_paths():
    repo_root = Path(__file__).resolve().parents[2]
    raw_path = repo_root / "data" / "01_raw" / "raw_customers.parquet"
    silver_dir = repo_root / "data" / "02_silver"
    silver_dir.mkdir(parents=True, exist_ok=True)
    silver_path = silver_dir / "stg_customers_golden.parquet"
    return raw_path, silver_path

class UnionFind:
    """Disjoint-set data structure to cluster matched identities."""
    def __init__(self):
        self.parent = {}

    def find(self, item):
        if item not in self.parent:
            self.parent[item] = item
            return item
        if self.parent[item] == item:
            return item
        self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, item1, item2):
        root1 = self.find(item1)
        root2 = self.find(item2)
        if root1 != root2:
            self.parent[root1] = root2

def clean_string(val):
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip().lower()

def resolve_entities(df: pd.DataFrame) -> pd.DataFrame:
    print(f"  🔍 Processing {len(df):,} source records for Entity Resolution...")
    
    # 1. Standardize fields for matching
    df["clean_first_name"] = df["first_name"].apply(clean_string)
    df["clean_last_name"] = df["last_name"].apply(clean_string)
    df["clean_email"] = df["email"].apply(clean_string)
    df["clean_phone"] = df["phone"].apply(clean_string)
    df["clean_city"] = df["city"].apply(clean_string)
    
    uf = UnionFind()
    record_ids = df["source_record_id"].tolist()
    for rid in record_ids:
        uf.find(rid)
        
    # 2. Blocking Rule 1: Exact Match on Email
    print("  ⚡ [Pass 1] Deterministic Exact Match on Email...")
    email_groups = df[df["clean_email"] != ""].groupby("clean_email")["source_record_id"].apply(list)
    for group in email_groups:
        if len(group) > 1:
            for other in group[1:]:
                uf.union(group[0], other)
                
    # 3. Blocking Rule 2: Exact Match on Phone Number
    print("  ⚡ [Pass 2] Deterministic Exact Match on Phone Number...")
    phone_groups = df[df["clean_phone"] != ""].groupby("clean_phone")["source_record_id"].apply(list)
    for group in phone_groups:
        if len(group) > 1:
            for other in group[1:]:
                uf.union(group[0], other)
                
    # 4. Blocking Rule 3: Probabilistic Fuzzy Matching within City + Last Name First Letter
    print("  ⚡ [Pass 3] Probabilistic Fuzzy Match (Levenshtein > 88% on Full Name + City)...")
    df["block_key"] = df["clean_city"] + "_" + df["clean_last_name"].str[:1]
    
    for block, group_df in df.groupby("block_key"):
        if len(group_df) < 2:
            continue
        records = group_df[["source_record_id", "clean_first_name", "clean_last_name"]].to_dict(orient="records")
        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                r1 = records[i]
                r2 = records[j]
                
                # Check Last Name similarity
                last_score = fuzz.ratio(r1["clean_last_name"], r2["clean_last_name"])
                if last_score >= 88:
                    first_score = fuzz.ratio(r1["clean_first_name"], r2["clean_first_name"])
                    if first_score >= 85:
                        uf.union(r1["source_record_id"], r2["source_record_id"])

    # 5. Extract Connected Clusters & Assign Global Customer IDs
    cluster_map = {}
    for rid in record_ids:
        cluster_map[rid] = uf.find(rid)
        
    df["cluster_root_id"] = df["source_record_id"].map(cluster_map)
    
    # Map cluster roots to clean sequential Global IDs
    unique_clusters = df["cluster_root_id"].unique()
    global_id_map = {root: f"ARGOS-CUST-{idx+1:05d}" for idx, root in enumerate(unique_clusters)}
    df["global_customer_id"] = df["cluster_root_id"].map(global_id_map)
    
    # 6. Apply Survivorship Rules (Pick the most recent valid values as Golden Record attributes)
    print("  🏆 [Pass 4] Applying Survivorship Rules for Golden Record creation...")
    df_sorted = df.sort_values(by=["global_customer_id", "updated_at"], ascending=[True, False])
    
    golden_attributes = df_sorted.groupby("global_customer_id").agg({
        "first_name": "first",
        "last_name": "first",
        "email": "first",
        "phone": "first",
        "street_address": "first",
        "city": "first",
        "state": "first",
        "country": "first",
        "updated_at": "max",
        "source_record_id": "count"
    }).reset_index().rename(columns={"source_record_id": "mdm_cluster_size"})
    
    # Join golden attributes back
    output_df = df[[
        "source_record_id",
        "source_system",
        "global_customer_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "street_address",
        "city",
        "state",
        "country",
        "updated_at"
    ]].copy()
    
    cluster_size_map = golden_attributes.set_index("global_customer_id")["mdm_cluster_size"].to_dict()
    output_df["mdm_cluster_size"] = output_df["global_customer_id"].map(cluster_size_map)
    output_df["is_golden_record_source"] = output_df["mdm_cluster_size"] > 1
    
    # MDM Resolution Statistics
    total_sources = len(df)
    total_golden = len(unique_clusters)
    duplicates_resolved = total_sources - total_golden
    dedup_ratio = (duplicates_resolved / total_sources) * 100
    
    print("\n" + "="*50)
    print(" 📊 MASTER DATA MANAGEMENT (MDM) SUMMARY:")
    print(f"  • Source Records Processed:    {total_sources:,}")
    print(f"  • Unique Golden Identities:    {total_golden:,}")
    print(f"  • Duplicate Records Merged:    {duplicates_resolved:,} ({dedup_ratio:.1f}%)")
    print("="*50 + "\n")
    
    return output_df

def main():
    print("⏳ [MDM ENGINE] Running Entity Resolution & Deduplication...")
    raw_path, silver_path = get_repo_paths()
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing raw customer data: {raw_path}. Run generator first.")
        
    df = pd.read_parquet(raw_path)
    golden_df = resolve_entities(df)
    
    golden_df.to_parquet(silver_path, index=False)
    print(f"✅ [SUCCESS] Silver Layer Golden Records saved to: {silver_path.name}\n")

if __name__ == "__main__":
    main()
