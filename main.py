import subprocess
import os
import time

print("🚀 Starting link.py...")

# Step 1: Run link.py
subprocess.run(["python", "link.py"])

# Step 2: Wait until data.xlsx is created
file_path = "data.xlsx"

while not os.path.exists(file_path):
    print("⏳ Waiting for data.xlsx to be created...")
    time.sleep(2)

print("✅ data.xlsx found!")

# Step 3: Run scrape.py
print("🚀 Starting scrape.py...")
subprocess.run(["python", "scrape.py"])

print("🎉 All tasks completed!")