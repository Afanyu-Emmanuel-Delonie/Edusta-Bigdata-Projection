import pandas as pd

def process_uploaded_csv(file):
    df = pd.read_csv(file)
    # Clean data (remove empty rows, fix capitalization)
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    return df