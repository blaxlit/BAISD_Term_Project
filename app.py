import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from autogluon.tabular import TabularPredictor

# โหลดโมเดล
try:
    predictor = TabularPredictor.load('ag_fishery_model')
except:
    predictor = None
    print("ไม่พบโมเดล! กรุณารัน train_model.py ก่อน")

app = dash.Dash(__name__)

# รายชื่อข้อมูลสำหรับ Dropdown
TOP_COUNTRIES = ['ญี่ปุ่น', 'จีน', 'สหรัฐอเมริกา', 'ฮ่องกง', 'มาเลเซีย', 'เกาหลีใต้', 'เวียดนาม', 'อินโดนีเซีย', 'ไต้หวัน', 'เมียนมา']
TOP_PRODUCTS = [
    'ปลาทูน่า สคิปแจกและแอตแลนติกโบนิโตอื่นๆ ที่บรรจุภาชนะที่อากาศผ่านเข้าออกไม่ได้',
    'ของผสมที่ใช้ปรุงรส และของผสมที่ใช้ชูรสอื่น ๆ',
    'อาหารสุนัขหรือแมวที่มีปลาบรรจุภาชนะที่อากาศเข้าออกไม่ได้',
    'ลูกปลาอื่น ๆ มีชีวิต',
    'น้ำปลา'
]

# --- UI Layout ---
app.layout = html.Div(style={'fontFamily': 'Tahoma, sans-serif', 'padding': '30px', 'backgroundColor': '#f4f6f9'}, children=[
    
    html.H1("🐟 แดชบอร์ดพยากรณ์มูลค่าการนำเข้า-ส่งออกสินค้าประมงไทย", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    # --- พารามิเตอร์รับค่า (3 คะแนน) ---
    html.Div(style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)', 'marginBottom': '20px'}, children=[
        html.H3("⚙️ ปรับตัวแปรสถานการณ์การค้า:"),
        
        html.Div(style={'display': 'flex', 'gap': '20px'}, children=[
            html.Div(style={'flex': 1}, children=[
                html.Label("ประเภทการค้า:"),
                dcc.Dropdown(id='input-trade', options=[{'label': 'นำเข้า', 'value': 'นำเข้า'}, {'label': 'ส่งออก', 'value': 'ส่งออก'}], value='ส่งออก', clearable=False),
            ]),
            html.Div(style={'flex': 1}, children=[
                html.Label("ประเทศคู่ค้า:"),
                dcc.Dropdown(id='input-country', options=[{'label': c, 'value': c} for c in TOP_COUNTRIES], value='ญี่ปุ่น', clearable=False),
            ]),
            html.Div(style={'flex': 1}, children=[
                html.Label("เดือนที่ต้องการพยากรณ์:"),
                dcc.Slider(id='input-month', min=1, max=12, step=1, value=12, marks={i: str(i) for i in range(1,13)}),
            ]),
        ]),
        html.Br(),
        html.Label("ประเภทสินค้าประมง:"),
        dcc.Dropdown(id='input-product', options=[{'label': p, 'value': p} for p in TOP_PRODUCTS], value=TOP_PRODUCTS[0], clearable=False),
        
        html.Hr(),
        # --- โมดูลเพิ่มเติมออกแบบเอง: Trade Balance Simulator (5 คะแนน) ---
        html.H4("💡 โมดูลเสริม: เครื่องมือวิเคราะห์ผลกำไร/ขาดทุน (Profit Simulator)", style={'color': '#8e44ad'}),
        html.Label("กรอกต้นทุนเฉลี่ยของสินค้าล็อตนี้ (บาท): "),
        dcc.Input(id='input-cost', type='number', value=1000000, step=100000)
    ]),

    # ส่วนแสดงผลพยากรณ์เป็นตัวเลข
    html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
        html.Div(id='output-value', style={'flex': 1, 'fontSize': '20px', 'fontWeight': 'bold', 'color': '#2980b9', 'padding': '20px', 'backgroundColor': '#ebf5fb', 'borderRadius': '10px', 'textAlign': 'center'}),
        html.Div(id='output-profit', style={'flex': 1, 'fontSize': '20px', 'fontWeight': 'bold', 'padding': '20px', 'borderRadius': '10px', 'textAlign': 'center'})
    ]),
    
    # --- กราฟแสดงผล (5 คะแนน) ---
    html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'}, children=[
        dcc.Graph(id='prediction-graph')
    ])
])

# Callback ควบคุมการอัปเดต
@app.callback(
    [Output('output-value', 'children'),
     Output('output-profit', 'children'),
     Output('output-profit', 'style'),
     Output('prediction-graph', 'figure')],
    [Input('input-trade', 'value'),
     Input('input-country', 'value'),
     Input('input-month', 'value'),
     Input('input-product', 'value'),
     Input('input-cost', 'value')]
)
def update_dash(trade_type, country, month, product, cost):
    if predictor is None: return "Error", "Error", {}, px.line()

    # 1. สร้างข้อมูลจำลองทั้ง 12 เดือน เพื่อให้เห็นเทรนด์แบบกราฟหุ้น
    months_list = list(range(1, 13))
    input_data_all = pd.DataFrame({
        'Year': [2568] * 12, 
        'Month': months_list, 
        'Country': [country] * 12, 
        'Product': [product] * 12, 
        'TradeType': [trade_type] * 12
    })
    
    # ให้โมเดลทำนายรวดเดียว 12 เดือน
    try:
        predictions_all = predictor.predict(input_data_all).tolist()
        predictions_all = [max(0, p) for p in predictions_all] # กันตัวเลขติดลบ
    except:
        predictions_all = [0] * 12
        
    # ดึงค่าเฉพาะเดือนที่ผู้ใช้เลือกมาแสดงผล
    predicted_value = predictions_all[month - 1]
        
    # 2. คำนวณกำไร/ขาดทุนจากโมดูลเสริม
    est_cost = cost if cost else 0
    profit = predicted_value - est_cost
    
    # 3. จัดการสีป้ายกำไร/ขาดทุน
    if profit >= 0:
        profit_text = f"📈 คาดการณ์กำไรสุทธิ: +{profit:,.2f} บาท"
        profit_style = {'flex': 1, 'fontSize': '20px', 'fontWeight': 'bold', 'color': '#27ae60', 'padding': '20px', 'backgroundColor': '#e8f8f5', 'borderRadius': '10px', 'textAlign': 'center'}
    else:
        profit_text = f"📉 คาดการณ์ขาดทุน: {profit:,.2f} บาท"
        profit_style = {'flex': 1, 'fontSize': '20px', 'fontWeight': 'bold', 'color': '#c0392b', 'padding': '20px', 'backgroundColor': '#fdedec', 'borderRadius': '10px', 'textAlign': 'center'}

    value_text = f"💰 พยากรณ์มูลค่าการ{trade_type} (เดือน {month}): {predicted_value:,.2f} บาท"
    
    # 4. 🌟 สร้างกราฟเส้น (Line Chart) สไตล์เทรนด์หุ้น
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # วาดเส้นเทรนด์ทั้ง 12 เดือน
    fig.add_trace(go.Scatter(
        x=[f"เดือน {m}" for m in months_list], 
        y=predictions_all, 
        mode='lines+markers',
        name='แนวโน้มทั้งปี',
        line=dict(color='#2980b9', width=3),
        marker=dict(size=8)
    ))
    
    # ไฮไลต์จุด "เดือนที่ผู้ใช้เลือก" ให้เด่นๆ (จุดใหญ่สีแดง)
    fig.add_trace(go.Scatter(
        x=[f"เดือน {month}"], 
        y=[predicted_value], 
        mode='markers',
        name='เดือนที่เป้าหมาย',
        marker=dict(color='#e74c3c', size=16, symbol='star')
    ))

    # ตกแต่งกราฟให้สวยงาม
    fig.update_layout(
        title=f"📈 กราฟหุ้นแสดงเทรนด์การ{trade_type}ตลอดปี: สินค้า {product[:30]}...",
        xaxis_title="เดือน (ปี พ.ศ. 2568)",
        yaxis_title="มูลค่าพยากรณ์ (บาท)",
        hovermode="x unified",
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    
    return value_text, profit_text, profit_style, fig

if __name__ == '__main__':
    app.run(debug=True)