import pandas as pd
import glob
import time
import sys

def audit_firms():
    print("=== PHASE 1: FIRMS DATASET AUDIT ===")
    start_time = time.time()
    
    csv_files = glob.glob("data/raw/firms_archive/*/*.csv")
    print(f"Found {len(csv_files)} CSV files.")
    
    total_rows = 0
    null_counts = {}
    negative_frp = 0
    bounding_box = {"min_lat": 90, "max_lat": -90, "min_lon": 180, "max_lon": -180}
    dates = []
    
    # Process in chunks to prevent OOM
    for f in csv_files:
        print(f"Processing {f}...")
        for chunk in pd.read_csv(f, chunksize=500000):
            total_rows += len(chunk)
            
            # Bounding box
            bounding_box["min_lat"] = min(bounding_box["min_lat"], chunk["latitude"].min())
            bounding_box["max_lat"] = max(bounding_box["max_lat"], chunk["latitude"].max())
            bounding_box["min_lon"] = min(bounding_box["min_lon"], chunk["longitude"].min())
            bounding_box["max_lon"] = max(bounding_box["max_lon"], chunk["longitude"].max())
            
            # Dates
            dates.append(chunk["acq_date"].min())
            dates.append(chunk["acq_date"].max())
            
            # Null values
            for col in chunk.columns:
                null_counts[col] = null_counts.get(col, 0) + chunk[col].isna().sum()
                
            # FRP Outliers
            negative_frp += (chunk["frp"] <= 0).sum()
            
    print(f"\nTotal Records: {total_rows}")
    print(f"Bounding Box: Lat ({bounding_box['min_lat']:.2f} to {bounding_box['max_lat']:.2f}), Lon ({bounding_box['min_lon']:.2f} to {bounding_box['max_lon']:.2f})")
    print(f"Temporal Range: {min(dates)} to {max(dates)}")
    print(f"Null Values: {null_counts}")
    print(f"Zero/Negative FRP records: {negative_frp}")
    
    # Let's test the Spatial Domain Heuristics using a 100k sample
    print("\n--- Pseudo-Labeling Feasibility (100k Sample) ---")
    sample_df = pd.concat([pd.read_csv(f, nrows=25000) for f in csv_files])
    print(f"Loaded {len(sample_df)} sample records for correlation checks.")
    
    # Since ESA WorldCover raster isn't physically in this repo yet, we'll simulate land cover distributions 
    # to evaluate the signal strength of FRP and Day/Night.
    # We will just print feature stats for the sample.
    print(f"FRP Stats:\n{sample_df['frp'].describe()}")
    print(f"Brightness Stats:\n{sample_df['brightness'].describe()}")
    print(f"DayNight Distribution:\n{sample_df['daynight'].value_counts()}")
    
    elapsed = time.time() - start_time
    print(f"\nAudit completed in {elapsed:.2f} seconds.")

if __name__ == '__main__':
    audit_firms()
