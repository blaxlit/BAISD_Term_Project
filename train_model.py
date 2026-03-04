import pandas as pd
from autogluon.tabular import TabularPredictor

def prepare_and_train():
    print("1. กำลังโหลดและทำความสะอาดข้อมูล...")
    # อ่านไฟล์ข้อมูล (ถ้ามีปัญหาภาษาไทย ให้เติม encoding='utf-8' หรือ 'tis-620')
    df = pd.read_csv('import_export.csv', encoding='utf-8')
    
    # --- เริ่มการทำความสะอาดข้อมูล (Data Cleansing - 2 คะแนน) ---
    # 1. เลือกลบคอลัมน์ที่ไม่จำเป็นออก (เช่น วันที่ดึงข้อมูล, รหัสประเทศ)
    df = df.drop(columns=['heading11', 'countryID', 'productDetailEN', 'ETL_DATE', 'weight', 'quantity'])
    
    # 2. จัดการค่าว่าง (Missing Values) ในชื่อประเทศ โดยการลบแถวทิ้ง
    df = df.dropna(subset=['countryNameTH'])
    
    # 3. แปลงค่าคอลัมน์ Tradeflow (1, 2) ให้เป็นข้อความภาษาไทยให้ผู้ใช้เข้าใจง่าย
    df['tradeflow'] = df['tradeflow'].map({1: 'นำเข้า', 2: 'ส่งออก'})
    
    # 4. เปลี่ยนชื่อคอลัมน์ให้เรียกใช้งานง่าย
    df = df.rename(columns={
        'year': 'Year',
        'month': 'Month',
        'countryNameTH': 'Country',
        'productDetailTH': 'Product',
        'tradeflow': 'TradeType',
        'price': 'Target_Value_THB'
    })
    
    # เพื่อให้โมเดลทำงานไวขึ้น (สำหรับโปรเจกต์) เราจะคัดมาเฉพาะข้อมูลของสินค้า Top 10 ที่มีการเทรดเยอะที่สุด
    top_products = df['Product'].value_counts().head(10).index
    top_countries = df['Country'].value_counts().head(10).index
    df = df[df['Product'].isin(top_products) & df['Country'].isin(top_countries)]

    print(f"✅ ข้อมูลหลังทำความสะอาดเสร็จสิ้น เหลือจำนวน {len(df)} แถว")
    print(df.head())
    
    # --- เริ่มการเทรนโมเดล (Machine Learning - 3 คะแนน) ---
    print("\n2. กำลังเทรนโมเดลด้วย AutoGluon... (อาจใช้เวลา 1-3 นาที)")
    # ระบุให้พยากรณ์มูลค่า (Target_Value_THB)
    predictor = TabularPredictor(label='Target_Value_THB', path='ag_fishery_model').fit(df, time_limit=120) # จำกัดเวลาเทรนไม่เกิน 2 นาที
    
    print("\n✅ เทรนเสร็จสมบูรณ์! โมเดลถูกบันทึกไว้ที่โฟลเดอร์ 'ag_fishery_model'")

if __name__ == '__main__':
    prepare_and_train()