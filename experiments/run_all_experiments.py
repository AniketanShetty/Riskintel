import subprocess
import json
import os
import sys

scripts = [
    "f0_missingness.py",
    "f1_target_leakage.py",
    "f2_contamination.py",
    "f3_duplicates.py",
    "f4_single_feature_auc.py",
    "f5_random_label_test.py",
    "f6_feature_semantics.py"
]

data_path = r"C:\Users\anike\Desktop\Riskintel\data\processed\eligibility_data.csv"
cwd = r"C:\Users\anike\Desktop\Riskintel\experiments\scripts"
outdir = r"C:\Users\anike\Desktop\Riskintel\experiments"

for script in scripts:
    print(f"--- Running {script} ---")
    cmd = [sys.executable, script, "--input", data_path, "--outdir", outdir]
    if script in ["f1_target_leakage.py", "f2_contamination.py", "f4_single_feature_auc.py", "f5_random_label_test.py"]:
        cmd.extend(["--target", "loan_status"])
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error in {script}:\n{res.stderr}")
    else:
        print(res.stdout)
        print(f"Completed {script}.")
