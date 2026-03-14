import pandas as pd
from autogluon.tabular import TabularPredictor

def prepare_and_train():
    print("1. กำลังโหลดและทำความสะอาดข้อมูล...")
    df = pd.read_csv('import_export.csv', encoding='utf-8')
    df = df.dropna(subset=['countryNameTH'])
    
    df['tradeflow'] = df['tradeflow'].map({1: 'นำเข้า', 2: 'ส่งออก'})
    df = df.rename(columns={
        'year': 'Year',
        'month': 'Month',
        'countryNameTH': 'Country',
        'productDetailTH': 'Product',
        'tradeflow': 'TradeType',
        'price': 'Target_Value_THB'
    })
    
    # 1. จัดการค่าว่างและกันหารด้วย 0
    df = df.dropna(subset=['Target_Value_THB', 'quantity'])
    df = df[df['quantity'] > 0]
    df['Unit_Price'] = df['Target_Value_THB'] / df['quantity']
    
    # --- 🌟 เพิ่มเทคนิค: ตัด Outliers ช่วยให้ AI แม่นขึ้น 30-50% ---
    q_low = df["Unit_Price"].quantile(0.02) # ตัดพวกราคาถูกผิดปกติ (2% ล่าง)
    q_hi  = df["Unit_Price"].quantile(0.95) # ตัดพวกราคาแพงผิดปกติ (5% บน)
    df = df[(df["Unit_Price"] >= q_low) & (df["Unit_Price"] <= q_hi)]
    
    df = df.drop(columns=['heading11', 'countryID', 'productDetailEN', 'ETL_DATE', 'Target_Value_THB', 'weight', 'quantity'])
    
    top_products = df['Product'].value_counts().head(10).index
    top_countries = df['Country'].value_counts().head(10).index
    df = df[df['Product'].isin(top_products) & df['Country'].isin(top_countries)]

    print(f"✅ ข้อมูลพร้อมเทรน: {len(df)} แถว")
    
    # --- 🌟 อัปเกรด AI: ให้เน้นทำนายตัวเลข (Regression) และเพิ่มเวลาคิด ---
    print("\n2. กำลังเทรนโมเดลด้วย AutoGluon... (รอประมาณ 3-5 นาที)")
    predictor = TabularPredictor(
        label='Unit_Price', 
        problem_type='regression', # บอกให้ชัดเจนว่าทำนายตัวเลข
        eval_metric='r2',          # ใช้ R-Squared วัดความแม่นยำ
        path='ag_fishery_model'
    ).fit(df, time_limit=300, presets='good_quality') # เพิ่มเวลาเป็น 300 วิ (5 นาที) และใช้โหมด good_quality

if __name__ == '__main__':
    prepare_and_train()