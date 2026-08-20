"""
ARGOS-360: Pipeline Orchestrator (Cross-Platform / Pure Python)
Executes the full End-to-End Lakehouse pipeline:
1. Ensure Data Directories Exist (Bronze, Silver, Gold)
2. Synthetic Raw Data Generation (Bronze)
3. MDM Entity Resolution with Splink/RapidFuzz (Silver)
4. dbt Snapshots (SCD Type 2)
5. dbt Models Compilation & Execution (Gold Kimball Marts)
6. dbt Data Quality Tests
"""
import subprocess
import sys
import time
from pathlib import Path

def run_step(step_name: str, command: list[str], cwd: Path | None = None):
    print(f"\n========================================================")
    print(f" 🚀 [RUNNING] {step_name}")
    print(f" Command: {' '.join(command)}")
    print(f"========================================================")
    start = time.time()
    result = subprocess.run(command, cwd=cwd)
    duration = time.time() - start
    if result.returncode != 0:
        print(f"❌ [ERROR] {step_name} failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    print(f"✅ [SUCCESS] {step_name} completed in {duration:.2f}s")

def main():
    repo_root = Path(__file__).parent.resolve()
    dbt_dir = repo_root / "dbt_ecommerce"

    # Ensure lakehouse storage directories exist
    (repo_root / "data" / "01_raw").mkdir(parents=True, exist_ok=True)
    (repo_root / "data" / "02_silver").mkdir(parents=True, exist_ok=True)
    (repo_root / "data" / "03_gold").mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print(" 🌟 ARGOS-360: E-COMMERCE CUSTOMER 360 LAKEHOUSE PIPELINE")
    print("="*60)

    # 1. Generate Raw Data
    run_step("1. Raw Data Generation (Bronze Layer)", [sys.executable, str(repo_root / "src" / "generator" / "generate_raw_data.py")])

    # 2. MDM Entity Resolution
    run_step("2. MDM Entity Resolution (Silver Layer)", [sys.executable, str(repo_root / "src" / "mdm" / "entity_resolution.py")])

    # 3. dbt Snapshots (SCD Type 2)
    run_step("3. dbt Snapshots (SCD Type 2)", ["dbt", "snapshot", "--profiles-dir", "."], cwd=dbt_dir)

    # 4. dbt Run (Marts / Kimball Models)
    run_step("4. dbt Models Execution (Gold Layer)", ["dbt", "run", "--profiles-dir", "."], cwd=dbt_dir)

    # 5. dbt Test (Data Quality Assertions)
    run_step("5. dbt Data Quality Tests", ["dbt", "test", "--profiles-dir", "."], cwd=dbt_dir)

    print("\n" + "="*60)
    print(" 🎉 [COMPLETE] Full Lakehouse Pipeline finished successfully!")
    print(" To launch the interactive dashboard, run: make dashboard (or streamlit run app/dashboard.py)")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
