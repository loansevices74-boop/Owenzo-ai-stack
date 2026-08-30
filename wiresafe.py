import streamlit as st, pandas as pd, math
from datetime import date
from fpdf import FPDF
from ai_router import safe_chat

st.set_page_config(page_title="WireSafe", page_icon="⚡", layout="wide")

# ============================================================
# PDF REPORT GENERATOR (defined first — used by the UI below)
# ============================================================

def _bs_ref(field):
 """BS 7671 table reference for a given design field."""
 refs = {
 "mcb": "Table 41.3 / Appendix 3",
 "cable": "Table 4E1B (Cu/PVC)",
 "vd": "Table 4E1B volt-drop",
 "correction": "App. 4 — Ca, Cg factors",
 }
 return refs.get(field, "BS 7671")


class _WireSafePDF(FPDF):
 """Custom FPDF with header (project/client/date) + footer (page numbers)."""

 def _init_(self, project="", client="", rpt_date=""):
 super()._init_()
 self.project = project or "—"
 self.client = client or "—"
 self.rpt_date = str(rpt_date) if rpt_date else "—"

 def header(self):
 self.set_font("Helvetica", "B", 14)
 self.cell(0, 8, "WireSafe Design Report", ln=1, align="C")
 self.set_font("Helvetica", "", 9)
 self.cell(0, 5,
 f"Project: {self.project} | Client: {self.client} | Date: {self.rpt_date}",
 ln=1, align="C")
 self.ln(2)
 self.set_draw_color(120, 120, 120)
 self.line(10, 25, 200, 25)
 self.ln(4)

 def footer(self):
 self.set_y(-12)
 self.set_font("Helvetica", "", 8)
 self.cell(0, 5,
 f"Owens U. Oriaikhi (COREN R72198) | WireSafe Design Aid | Page {self.page_no()}",
 align="C")


def _draw_kv_table(pdf, rows, col_w=(90, 100)):
 """2-column key/value table for Design Inputs."""
 pdf.set_fill_color(230, 230, 230)
 pdf.cell(col_w[0], 6, "Parameter", border=1, fill=True)
 pdf.cell(col_w[1], 6, "Value", border=1, fill=True, ln=1)
 for k, v in rows:
 pdf.cell(col_w[0], 6, k, border=1)
 pdf.cell(col_w[1], 6, v, border=1, ln=1)


def _draw_results_table(pdf, rows, col_w=(45, 40, 55, 50)):
 """4-column results table: Item | Value | BS 7671 Ref | Status."""
 pdf.set_fill_color(230, 230, 230)
 headers = ["Item", "Value", "BS 7671 Ref", "Status"]
 for i, h in enumerate(headers):
 pdf.cell(col_w[i], 6, h, border=1, fill=True)
 pdf.ln()
 for item, val, ref, status in rows:
 pdf.cell(col_w[0], 6, item, border=1)
 pdf.cell(col_w[1], 6, val, border=1)
 pdf.cell(col_w[2], 6, ref, border=1)
 mark = "[x]" if status in ("PASS", "APPLIED") else "[ ]"
 pdf.cell(col_w[3], 6, f"{mark} {status}", border=1, ln=1)


def _draw_boq_table(pdf, boq_df, col_w=(80, 25, 20, 65)):
 """4-column BOQ table: Item | Qty | Unit | Total (NGN)."""
 pdf.set_fill_color(230, 230, 230)
 headers = ["Item", "Qty", "Unit", "Total (NGN)"]
 for i, h in enumerate(headers):
 pdf.cell(col_w[i], 6, h, border=1, fill=True)
 pdf.ln()
 for _, row in boq_df.iterrows():
 pdf.cell(col_w[0], 6, str(row["Item"]), border=1)
 pdf.cell(col_w[1], 6, str(row["Qty"]), border=1, align="R")
 pdf.cell(col_w[2], 6, str(row["Unit"]), border=1)
 pdf.cell(col_w[3], 6, f"{int(row['Total (NGN)']):,}", border=1, align="R", ln=1)


def _build_report(phases, pf, ca, cg, vd_limit, length_m,
 total_w, design_w, ib, breaker, cable, vd_pct,
 boq_df, eng_summary, project, client, rpt_date):
 """Build the upgraded PDF and return raw bytes for st.download_button."""

 pdf = _WireSafePDF(project=project, client=client, rpt_date=rpt_date)
 pdf.add_page()

 # 1. Design Inputs
 pdf.set_font("Helvetica", "B", 11)
 pdf.cell(0, 7, "Design Inputs", ln=1)
 pdf.set_font("Helvetica", "", 9)
 inputs = [
 ("Phases", f"{phases}"),
 ("Power factor", f"{pf:.2f}"),
 ("Circuit length", f"{length_m} m"),
 ("Connected load", f"{total_w:,.0f} W"),
 ("Design load", f"{design_w:,.0f} W"),
 ("Design current Ib", f"{ib:.1f} A"),
 ("Ca (ambient)", f"{ca:.2f}"),
 ("Cg (grouping)", f"{cg:.2f}"),
 ("V-drop limit", f"{vd_limit:.1f}%"),
 ]
 _draw_kv_table(pdf, inputs)

 # 2. Results & Compliance
 pdf.ln(3)
 pdf.set_font("Helvetica", "B", 11)
 pdf.cell(0, 7, "Results & Compliance Check", ln=1)
 pdf.set_font("Helvetica", "", 9)
 results = [
 ("MCB rating", f"{breaker} A", _bs_ref("mcb"), "PASS"),
 ("Cable size", f"{cable} mm2", _bs_ref("cable"), "PASS"),
 ("Voltage drop", f"{vd_pct:.2f}%", _bs_ref("vd"), "PASS" if vd_pct <= vd_limit else "CHECK"),
 ("Correction", f"Ca={ca:.2f}, Cg={cg:.2f}", _bs_ref("correction"), "APPLIED"),
 ]
 _draw_results_table(pdf, results)

 # 3. BOQ
 pdf.ln(3)
 pdf.set_font("Helvetica", "B", 11)
 pdf.cell(0, 7, "Bill of Quantities (BOQ)", ln=1)
 pdf.set_font("Helvetica", "", 9)
 _draw_boq_table(pdf, boq_df)

 # 4. Cost summary
 pdf.ln(1)
 grand_total = int(boq_df["Total (NGN)"].sum())
 pdf.set_font("Helvetica", "B", 11)
 pdf.cell(0, 7, f"Estimated Material Cost: NGN {grand_total:,}", ln=1, align="R")

 # 5. Engineering Summary
 pdf.ln(4)
 pdf.set_font("Helvetica", "B", 11)
 pdf.cell(0, 7, "Engineering Summary", ln=1)
 pdf.set_font("Helvetica", "", 10)
 pdf.multi_cell(0, 6, eng_summary)

 # 6. Sign-off + Disclaimer
 pdf.ln(4)
 pdf.set_font("Helvetica", "B", 9)
 pdf.cell(0, 6, "Verified by: Owens U. Oriaikhi (COREN Reg. No. R72198)", ln=1)
 pdf.set_font("Helvetica", "I", 8)
 pdf.multi_cell(0, 5,
 "Disclaimer: This report is a design aid generated by WireSafe. "
 "Final verification and sign-off must be performed by a COREN-registered "
 "engineer before installation.")

 return pdf.output()


# ============================================================
# STREAMLIT UI
# ============================================================

st.title("⚡ WireSafe — Electrical Wiring Design")
st.caption("By Owens U. Oriaikhi | COREN Reg. No: R72198")

# BS 7671 copper PVC: size -> (ampacity A, mV/A/m)
CABLES = {1.5:(20,29), 2.5:(27,18), 4:(36,11), 6:(46,7.3), 10:(62,4.4),
 16:(80,2.8), 25:(101,1.75), 35:(126,1.25), 50:(151,0.93),
 70:(192,0.63), 95:(232,0.47), 120:(269,0.38)}
BREAKERS = [6,10,16,20,25,32,40,50,63,80,100,125,160,200,250,315,400]
PRICE_M = {1.5:350, 2.5:550, 4:900, 6:1300, 10:2200, 16:3400, 25:5300,
 35:7400, 50:10500, 70:14800, 95:20000, 120:25000} # NGN/m placeholders

# ---- Sidebar: Design Inputs ----
st.sidebar.header("Design Inputs")
phases = st.sidebar.selectbox("Phases", [1, 3])
pf = st.sidebar.slider("Power factor", 0.7, 1.0, 0.9)
ca = st.sidebar.slider("Ambient correction Ca", 0.7, 1.0, 1.0)
cg = st.sidebar.slider("Grouping correction Cg", 0.7, 1.0, 1.0)
vd_limit = st.sidebar.selectbox("V-drop limit %", [3.0, 4.0, 5.0], index=1)

# ---- Sidebar: Project details (NEW) ----
st.sidebar.markdown("---")
st.sidebar.header("Report Details")
project_name = st.sidebar.text_input("Project name", value="", key="ws_project")
client_name = st.sidebar.text_input("Client name", value="", key="ws_client")
report_date = st.sidebar.date_input("Report date", value=date.today(), key="ws_date")

# ---- Load schedule ----
st.subheader("Load Schedule")
loads = st.data_editor(pd.DataFrame([
 {"Device": "Lighting", "Watts": 500, "Qty": 10},
 {"Device": "AC Unit", "Watts": 2200, "Qty": 2},
 {"Device": "Sockets", "Watts": 1300, "Qty": 6}]), num_rows="dynamic").fillna(0)

length_m = st.number_input("Circuit run length (m)", 1, 500, 30)
demand = st.slider("Demand factor %", 50, 100, 80)

# ---- Calculations ----
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

# ---- Metrics ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Connected Load (W)", f"{total_w:,.0f}")
c2.metric("Design Load (W)", f"{design_w:,.0f}")
c3.metric("Ib (A)", f"{ib:.1f}")
c4.metric("V-drop %", f"{vd_pct:.2f}" if vd_pct else "—")

if status == "PASS":
 st.success(f"✅ PASS — MCB {breaker}A | Cable {cable} mm² | V-drop {vd_pct:.2f}%")
 cable_m = round(length_m * 1.05, 1)
 boq = pd.DataFrame([
 {"Item": f"PVC copper cable {cable} mm²", "Qty": cable_m, "Unit": "m", "Total (NGN)": round(cable_m * PRICE_M[cable])},
 {"Item": f"MCB {breaker}A", "Qty": 1, "Unit": "pc", "Total (NGN)": 18000},
 {"Item": "Conduit & accessories", "Qty": 1, "Unit": "lot", "Total (NGN)": 25000}])
 st.subheader("BOQ")
 st.dataframe(boq, use_container_width=True)
 st.metric("Estimated Cost (NGN)", f"{boq['Total (NGN)'].sum():,.0f}")

 # ---- Generate PDF Report (UPGRADED) ----
 if st.button("📄 Generate PDF Design Report"):
 ai = safe_chat(
 f"4-line engineering summary: load {design_w:.0f}W, Ib {ib:.1f}A, "
 f"MCB {breaker}A, cable {cable}mm2, v-drop {vd_pct:.2f}%",
 system="You are a COREN-registered electrical engineer writing a client report.",
 fallback="Design verified against BS 7671 copper PVC cable tables. "
 "All results within regulatory limits."
 )

 pdf_bytes = _build_report(
 phases, pf, ca, cg, vd_limit, length_m,
 total_w, design_w, ib, breaker, cable, vd_pct,
 boq, ai['text'], project_name, client_name, report_date
 )
 st.download_button(
 "📥 Download PDF Design Report",
 data=pdf_bytes,
 file_name="WireSafe_Report.pdf",
 mime="application/pdf",
 )
 st.success("Report ready — click the Download button below.")
else:
 st.error("❌ No suitable cable — reduce load/length or split circuits.")
