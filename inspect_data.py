import pandas as pd
import json

def analyze():
    out = {}
    
    # Consumer Order History
    try:
        df_coh = pd.read_excel('data/Consumer Order History 1.xlsx', skiprows=4)
        out['consumer_order_history'] = {
            'columns': df_coh.columns.tolist(),
            'sample': df_coh.iloc[0].to_dict() if len(df_coh) > 0 else {}
        }
    except Exception as e:
        out['consumer_order_history'] = str(e)

    # Products Export
    try:
        df_pe = pd.read_excel('data/products-export.xlsx')
        out['products_export'] = {
            'columns': df_pe.columns.tolist(),
            'sample': df_pe.iloc[0].to_dict() if len(df_pe) > 0 else {}
        }
    except Exception as e:
        out['products_export'] = str(e)

    # Medicine Master
    try:
        df_mm = pd.read_csv('data/medicine-master-enhanced.csv')
        out['medicine_master_enhanced'] = {
            'columns': df_mm.columns.tolist(),
            'sample': df_mm.iloc[0].to_dict() if len(df_mm) > 0 else {}
        }
    except Exception as e:
        out['medicine_master_enhanced'] = str(e)

    with open('data_schema.json', 'w') as f:
        json.dump(out, f, indent=2, default=str)

if __name__ == "__main__":
    analyze()
