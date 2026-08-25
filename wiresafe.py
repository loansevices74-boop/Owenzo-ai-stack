import streamlit as st, pandas as pd, math
from fpdf import FPDF
from ai_router import safe_chat

st.set_page_config(page_title="WireSafe", page_icon="⚡", layout="wide")
st.title("⚡ WireSafe — Electrical Wiring Design")
st.caption("By Owens U. Oriaikhi | COREN Reg. No: R72198")

# BS 7671 copper PVC: size -> (ampacity A, mV/A/m)
CABLES = {1.5:(20,29), 2.5:(27,18), 4:(36,11), 6:(46,7.3), 10:(62,4.4),
          16:(80,2.8), 25:(101,1.75), 35:(126,1.25), 50:(151,0.93),
          70:(192,0.63), 95:(232,0.47), 120:(269,0.38)}
BREAKERS = [6,10,16,20,25,32,40,50,63,80,100,125,160,200,250,315,400]
PRICE_M = {1.5:350, 2.5:550, 4:900, 6:1300, 10:2200, 16:3400, 25:5300,
           35:7400, 50:10500, 70:14800, 95:20000, 120:25000}  # ₦/m placeholders

st.sidebar.header("Design Inputs")
phases = st.sidebar.selectbox("Phases", [1, 3])
pf = st.sidebar.slider("Power factor", 0.7, 1.0, 0.9)
ca = st.sidebar.slider("Ambient correction Ca", 0.7, 1.0, 1.0)
cg = st.sidebar.slider("Grouping correction Cg", 0.7, 1.0, 1.0)
vd_limit = st.sidebar.selectbox("V-drop limit %", [3.0, 4.0, 5.0], index=1)

st.subheader("Load Schedule")
loads = st.data_editor(pd.DataFrame([
    {"Device": "Lighting", "Watts": 500, "Qty": 10},
    {"Device": "AC Unit", "Watts": 2200, "Qty": 2},
    {"Device": "Sockets", "Watts": 1300, "Qty": 6}]), num_rows="dynamic").fillna(0)

length_m = st.number_input("Circuit run length (m)", 1, 500, 30)
demand = st.slider("Demand factor %", 50, 100, 80)

total_w = float((loads["Watts"] * loads["Qty"]).sum())
design_w = total_w * demand / 100
v = 230 if phases == 1 else 400
ib = design_w / (v * pf) if phases == 1 else design_w / (math.sqrt(3) * v * pf)
breaker = next((b for b in BREAKERS if b >= ib), None)

cable, vd_pct, status = None, None, "FAIL"
if breaker:
    for size, (iz, mv) in sorted(CABLES.items()):
        if iz * ca * cg >= breaker:
            vd = 100 * (mv * ib * length_m / 1000) / v
            if vd <= vd_limit:
                cable, vd_pct, status = size, vd, "PASS"
                break

c1, c2, c3, c4 = st.columns(4)
c1.metric("Connected Load (W)", f"{total_w:,.0f}")
c2.metric("Design Load (W)", f"{design_w:,.0f}")
c3.metric("Ib (A)", f"{ib:.1f}")
c4.metric("V-drop %", f"{vd_pct:.2f}" if vd_pct else "—")

if status == "PASS":
    st.success(f"✅ PASS — MCB {breaker}A | Cable {cable} mm² | V-drop {vd_pct:.2f}%")
    cable_m = round(length_m * 1.05, 1)
    boq = pd.DataFrame([
        {"Item": f"PVC copper cable {cable} mm²", "Qty": cable_m, "Unit": "m", "Total (₦)": round(cable_m * PRICE_M[cable])},
        {"Item": f"MCB {breaker}A", "Qty": 1, "Unit": "pc", "Total (₦)": 18000},
        {"Item": "Conduit & accessories", "Qty": 1, "Unit": "lot", "Total (₦)": 25000}])
    st.subheader("BOQ"); st.dataframe(boq, use_container_width=True)
    st.metric("Estimated Cost (₦)", f"{boq['Total (₦)'].sum():,.0f}")

    if st.button("📄 Generate PDF Design Report"):
        ai = safe_chat(f"4-line engineering summary: load {design_w:.0f}W, Ib {ib:.1f}A, MCB {breaker}A, cable {cable}mm2, v-drop {vd_pct:.2f}%",
                       system="You are a COREN-registered electrical engineer writing a client report.")
        pdf = FPDF(); pdf.add_page()
        pdf.set_font("Helvetica", "B", 16); pdf.cell(0, 10, "WireSafe Design Report"); pdf.ln(12)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, f"Engineer: Owens U. Oriaikhi (COREN R72198)\n"
            f"Phases {phases} | PF {pf} | Length {length_m}m | Ib {ib:.1f}A\n"
            f"MCB {breaker}A | Cable {cable}mm2 | V-drop {vd_pct:.2f}%\n\n"
            f"AI Summary [{ai['provider']}]:\n{ai['text']}\n\n"
            "Disclaimer: Design aid - final verification by a COREN-registered engineer required.")
        tmp_path = "/tmp/WireSafe_Report.pdf"
        pdf.output(tmp_path)
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
        st.download_button("📥 Download PDF Design Report", data=pdf_bytes,
                           file_name="WireSafe_Report.pdf", mime="application/pdf")
        st.success("Report ready — click the Download button below.")
else:
    st.error("❌ No suitable cable — reduce load/length or split circuits.")
