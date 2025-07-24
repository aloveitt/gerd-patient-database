import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile
import os

# Configure page
st.set_page_config(
    page_title="GERD Clinical Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def get_database_connection():
    """Get database connection with caching"""
    return sqlite3.connect("gerd_center.db", check_same_thread=False)

def execute_query(query, params=None, fetch=True):
    """Execute database query safely"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            if query.strip().upper().startswith("SELECT"):
                columns = [description[0] for description in cursor.description]
                data = cursor.fetchall()
                return pd.DataFrame(data, columns=columns) if data else pd.DataFrame()
            else:
                return cursor.fetchall()
        else:
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame() if fetch else False

# Initialize session state
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Search"
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = {}

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
    }
    .patient-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .status-urgent { color: #dc2626; font-weight: bold; }
    .status-warning { color: #d97706; font-weight: bold; }
    .status-success { color: #059669; font-weight: bold; }
    .status-info { color: #0891b2; font-weight: bold; }
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
    }
    .form-section {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Utility functions
def validate_mrn(mrn):
    """Validate MRN format"""
    if not mrn or len(mrn.strip()) < 5 or len(mrn.strip()) > 15:
        return False
    return mrn.strip().isalnum()

def validate_date(date_obj, min_year=1900):
    """Validate date is reasonable"""
    if not date_obj:
        return False
    return date_obj.year >= min_year and date_obj <= date.today()

def get_surgeons():
    """Get list of surgeons"""
    surgeons_df = execute_query("SELECT DISTINCT SurgeonName FROM tblSurgeons ORDER BY SurgeonName")
    return surgeons_df['SurgeonName'].tolist() if not surgeons_df.empty else []

# Add Patient Form
def show_add_patient_form():
    """Show add patient form"""
    st.subheader("➕ Add New Patient")
    
    with st.form("add_patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name*", key="new_first_name")
            last_name = st.text_input("Last Name*", key="new_last_name")
            mrn = st.text_input("MRN*", key="new_mrn")
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], key="new_gender")
        
        with col2:
            dob = st.date_input("Date of Birth", key="new_dob")
            zip_code = st.text_input("ZIP Code", key="new_zip")
            bmi = st.number_input("BMI", min_value=0.0, max_value=100.0, step=0.1, value=None, key="new_bmi")
            referral_source = st.selectbox("Referral Source", ["", "Self", "Physician", "Patient", "Other"], key="new_referral")
        
        referral_details = st.text_area("Referral Details", key="new_referral_details")
        consult_date = st.date_input("Initial Consult Date", key="new_consult_date")
        
        submitted = st.form_submit_button("💾 Save Patient", type="primary")
        
        if submitted:
            # Validate required fields
            errors = []
            if not first_name.strip():
                errors.append("First name is required")
            if not last_name.strip():
                errors.append("Last name is required")
            if not mrn.strip():
                errors.append("MRN is required")
            if not validate_mrn(mrn):
                errors.append("MRN must be 5-15 alphanumeric characters")
            if not validate_date(dob):
                errors.append("Please enter a valid date of birth")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Check for duplicate MRN
                existing = execute_query("SELECT COUNT(*) as count FROM tblPatients WHERE MRN = ?", (mrn.strip(),))
                if not existing.empty and existing.iloc[0]['count'] > 0:
                    st.error("A patient with this MRN already exists!")
                else:
                    # Insert patient
                    success = execute_query("""
                        INSERT INTO tblPatients (FirstName, LastName, MRN, Gender, DOB, ZipCode, BMI, 
                                               ReferralSource, ReferralDetails, InitialConsultDate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (first_name.strip(), last_name.strip(), mrn.strip(), gender, 
                          dob.strftime("%Y-%m-%d"), zip_code.strip(), bmi, referral_source, 
                          referral_details.strip(), consult_date.strftime("%Y-%m-%d")), fetch=False)
                    
                    if success:
                        st.success("Patient added successfully!")
                        st.session_state.show_add_form['patient'] = False
                        st.rerun()

# Add Diagnostic Form
def show_add_diagnostic_form(patient_id):
    """Show add diagnostic form"""
    st.subheader("➕ Add Diagnostic Study")
    
    with st.form("add_diagnostic_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            test_date = st.date_input("Test Date*", value=date.today())
            surgeons = get_surgeons()
            surgeon = st.selectbox("Surgeon", [""] + surgeons)
        
        with col2:
            st.write("**Tests Performed:**")
            endoscopy = st.checkbox("Endoscopy")
            bravo = st.checkbox("Bravo")
            ph_impedance = st.checkbox("pH Impedance")
            endoflip = st.checkbox("EndoFLIP")
            manometry = st.checkbox("Manometry")
            gastric_emptying = st.checkbox("Gastric Emptying")
            imaging = st.checkbox("Imaging")
            upper_gi = st.checkbox("Upper GI")
        
        # Endoscopy findings
        if endoscopy:
            st.write("**Endoscopy Details:**")
            esophagitis_grade = st.selectbox("Esophagitis Grade", ["", "None", "LA A", "LA B", "LA C", "LA D"])
            hernia_size = st.selectbox("Hiatal Hernia Size", ["", "None", "1 cm", "2 cm", "3 cm", "4 cm", "5 cm", "6 cm", ">6 cm"])
            endo_findings = st.text_area("Endoscopy Findings")
        else:
            esophagitis_grade = hernia_size = endo_findings = ""
        
        # pH Study details
        if bravo or ph_impedance:
            st.write("**pH Study Details:**")
            demeester_score = st.number_input("DeMeester Score", min_value=0.0, max_value=500.0, step=0.1, value=None)
            ph_findings = st.text_area("pH Study Findings")
        else:
            demeester_score = ph_findings = None
        
        # Other findings
        if endoflip:
            endoflip_findings = st.text_area("EndoFLIP Findings")
        else:
            endoflip_findings = ""
        
        if manometry:
            manometry_findings = st.text_area("Manometry Findings")
        else:
            manometry_findings = ""
        
        if gastric_emptying:
            percent_retained = st.number_input("% Retained at 4h", min_value=0.0, max_value=100.0, step=0.1, value=None)
            ge_findings = st.text_area("Gastric Emptying Findings")
        else:
            percent_retained = ge_findings = None
        
        if imaging:
            imaging_findings = st.text_area("Imaging Findings")
        else:
            imaging_findings = ""
        
        if upper_gi:
            ugi_findings = st.text_area("Upper GI Findings")
        else:
            ugi_findings = ""
        
        additional_notes = st.text_area("Additional Notes")
        
        submitted = st.form_submit_button("💾 Save Diagnostic Study", type="primary")
        
        if submitted:
            if not validate_date(test_date, 1990):
                st.error("Please enter a valid test date")
            elif not any([endoscopy, bravo, ph_impedance, endoflip, manometry, gastric_emptying, imaging, upper_gi]):
                st.error("Please select at least one test type")
            else:
                success = execute_query("""
                    INSERT INTO tblDiagnostics (
                        PatientID, TestDate, Surgeon,
                        Endoscopy, EsophagitisGrade, HiatalHerniaSize, EndoscopyFindings,
                        Bravo, pHImpedance, DeMeesterScore, pHFindings,
                        EndoFLIP, EndoFLIPFindings,
                        Manometry, ManometryFindings,
                        GastricEmptying, PercentRetained4h, GastricEmptyingFindings,
                        Imaging, ImagingFindings,
                        UpperGI, UpperGIFindings,
                        DiagnosticNotes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    patient_id, test_date.strftime("%Y-%m-%d"), surgeon,
                    endoscopy, esophagitis_grade, hernia_size, endo_findings,
                    bravo, ph_impedance, demeester_score, ph_findings,
                    endoflip, endoflip_findings,
                    manometry, manometry_findings,
                    gastric_emptying, percent_retained, ge_findings,
                    imaging, imaging_findings,
                    upper_gi, ugi_findings,
                    additional_notes
                ), fetch=False)
                
                if success:
                    st.success("Diagnostic study saved successfully!")
                    st.session_state.show_add_form['diagnostic'] = False
                    st.rerun()

# Add Pathology Form
def show_add_pathology_form(patient_id):
    """Show add pathology form"""
    st.subheader("➕ Add Pathology Entry")
    
    with st.form("add_pathology_form"):
        path_date = st.date_input("Pathology Date*", value=date.today())
        
        st.write("**Test Types Performed:**")
        col1, col2 = st.columns(2)
        with col1:
            biopsy = st.checkbox("Biopsy")
            wats3d = st.checkbox("WATS3D")
        with col2:
            esopredict = st.checkbox("EsoPredict")
            tissuecypher = st.checkbox("TissueCypher")
        
        st.write("**Pathology Findings:**")
        barretts = st.checkbox("Barrett's Esophagus")
        if barretts:
            dysplasia_grade = st.selectbox("Dysplasia Grade", 
                ["", "NGIM", "No Dysplasia", "Indeterminate", "Low Grade", "High Grade"])
        else:
            dysplasia_grade = ""
        
        eoe = st.checkbox("Eosinophilic Esophagitis (EoE)")
        if eoe:
            eos_count = st.number_input("Eosinophil Count (per hpf)", min_value=0.0, step=0.1)
        else:
            eos_count = None
        
        col1, col2 = st.columns(2)
        with col1:
            hpylori = st.checkbox("H. pylori")
            gastritis = st.checkbox("Atrophic Gastritis")
        
        other_finding = st.text_input("Other Finding")
        
        st.write("**Risk Assessment Scores:**")
        esopredict_risk = st.text_input("EsoPredict Risk Score")
        tissuecypher_risk = st.text_input("TissueCypher Risk Score")
        
        notes = st.text_area("Additional Notes")
        
        submitted = st.form_submit_button("💾 Save Pathology Entry", type="primary")
        
        if submitted:
            if not validate_date(path_date, 1990):
                st.error("Please enter a valid pathology date")
            elif not any([biopsy, wats3d, esopredict, tissuecypher]):
                st.error("Please select at least one test type")
            else:
                success = execute_query("""
                    INSERT INTO tblPathology (
                        PatientID, PathologyDate, Biopsy, WATS3D, EsoPredict, TissueCypher,
                        Hpylori, Barretts, DysplasiaGrade, AtrophicGastritis, EoE,
                        EosinophilCount, OtherFinding, EsoPredictRisk, TissueCypherRisk, Notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    patient_id, path_date.strftime("%Y-%m-%d"), biopsy, wats3d, esopredict, tissuecypher,
                    hpylori, barretts, dysplasia_grade, gastritis, eoe,
                    eos_count, other_finding, esopredict_risk, tissuecypher_risk, notes
                ), fetch=False)
                
                if success:
                    st.success("Pathology entry saved successfully!")
                    if barretts:
                        if "high grade" in dysplasia_grade.lower():
                            st.warning("🚨 High-grade dysplasia detected - 3-month surveillance recommended!")
                        elif "low grade" in dysplasia_grade.lower():
                            st.warning("⚠️ Low-grade dysplasia detected - 6-month surveillance recommended!")
                        else:
                            st.info("ℹ️ Barrett's detected - surveillance planning recommended")
                    st.session_state.show_add_form['pathology'] = False
                    st.rerun()

# Add Surgical Form
def show_add_surgical_form(patient_id):
    """Show add surgical form"""
    st.subheader("➕ Add Surgical Procedure")
    
    with st.form("add_surgical_form"):
        surgery_date = st.date_input("Surgery Date*", value=date.today())
        surgeons = get_surgeons()
        surgeon = st.selectbox("Surgeon*", [""] + surgeons)
        
        st.write("**Procedures Performed:**")
        
        # Group procedures
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Hernia Repairs:**")
            hiatal_hernia = st.checkbox("Hiatal Hernia Repair")
            paraeso_hernia = st.checkbox("Paraesophageal Hernia Repair")
            mesh_used = st.checkbox("Mesh Used")
            
            st.write("**Fundoplications:**")
            nissen = st.checkbox("Nissen Fundoplication (360°)")
            toupet = st.checkbox("Toupet Fundoplication (270°)")
            dor = st.checkbox("Dor Fundoplication (180°)")
            
            st.write("**Other Anti-Reflux:**")
            tif = st.checkbox("TIF (Transoral Incisionless)")
            linx = st.checkbox("LINX Device")
            stretta = st.checkbox("Stretta Radiofrequency")
        
        with col2:
            st.write("**POEM Procedures:**")
            gpoem = st.checkbox("G-POEM (Gastric)")
            epoem = st.checkbox("E-POEM (Esophageal)")
            zpoem = st.checkbox("Z-POEM (Zenker's)")
            
            st.write("**Bariatric Procedures:**")
            gastric_bypass = st.checkbox("Gastric Bypass")
            sleeve = st.checkbox("Sleeve Gastrectomy")
            
            st.write("**Other Procedures:**")
            heller = st.checkbox("Heller Myotomy")
            pyloroplasty = st.checkbox("Pyloroplasty")
            ablation = st.checkbox("Ablation Therapy")
            revision = st.checkbox("Revision Surgery")
            dilation = st.checkbox("Esophageal Dilation")
            stimulator = st.checkbox("Gastric Stimulator")
            other = st.checkbox("Other Procedure")
        
        operative_notes = st.text_area("Operative Notes")
        
        submitted = st.form_submit_button("💾 Save Surgical Procedure", type="primary")
        
        if submitted:
            if not validate_date(surgery_date, 1980):
                st.error("Please enter a valid surgery date")
            elif not surgeon:
                st.error("Please select a surgeon")
            else:
                # Check for conflicting procedures
                fundos = [nissen, toupet, dor]
                poems = [gpoem, epoem, zpoem]
                bariatrics = [gastric_bypass, sleeve]
                
                if sum(fundos) > 1:
                    st.error("Cannot perform multiple fundoplications in same surgery")
                elif sum(poems) > 1:
                    st.error("Cannot perform multiple POEM procedures in same surgery")
                elif sum(bariatrics) > 1:
                    st.error("Cannot perform multiple bariatric procedures in same surgery")
                else:
                    success = execute_query("""
                        INSERT INTO tblSurgicalHistory (
                            PatientID, SurgeryDate, SurgerySurgeon, Notes,
                            HiatalHernia, ParaesophagealHernia, MeshUsed, GastricBypass, SleeveGastrectomy,
                            Toupet, TIF, Nissen, Dor, HellerMyotomy, Stretta, Ablation, LINX,
                            GPOEM, EPOEM, ZPOEM, Pyloroplasty, Revision, GastricStimulator, Dilation, Other
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        patient_id, surgery_date.strftime("%Y-%m-%d"), surgeon, operative_notes,
                        hiatal_hernia, paraeso_hernia, mesh_used, gastric_bypass, sleeve,
                        toupet, tif, nissen, dor, heller, stretta, ablation, linx,
                        gpoem, epoem, zpoem, pyloroplasty, revision, stimulator, dilation, other
                    ), fetch=False)
                    
                    if success:
                        st.success("Surgical procedure saved successfully!")
                        st.session_state.show_add_form['surgical'] = False
                        st.rerun()

# Add Surveillance Form
def show_add_surveillance_form(patient_id):
    """Show add surveillance form"""
    st.subheader("➕ Add Surveillance Plan")
    
    # Check Barrett's eligibility
    barrett_check = execute_query("""
        SELECT COUNT(*) as count FROM tblPathology 
        WHERE PatientID = ? AND Barretts = 1
    """, (patient_id,))
    
    has_barretts = not barrett_check.empty and barrett_check.iloc[0]['count'] > 0
    
    if not has_barretts:
        st.warning("⚠️ No Barrett's esophagus found in pathology history. Surveillance may not be appropriate.")
    
    # Get latest Barrett's info for recommendations
    latest_barrett = execute_query("""
        SELECT PathologyDate, DysplasiaGrade
        FROM tblPathology
        WHERE PatientID = ? AND Barretts = 1
        ORDER BY PathologyDate DESC
        LIMIT 1
    """, (patient_id,))
    
    if not latest_barrett.empty:
        grade = latest_barrett.iloc[0]['DysplasiaGrade'] or ""
        st.info(f"Latest Barrett's: {latest_barrett.iloc[0]['PathologyDate']} - {grade}")
        
        # Provide recommendations
        if "high grade" in grade.lower():
            recommended_months = 3
            st.error("🚨 High-grade dysplasia - 3-month intervals recommended")
        elif "low grade" in grade.lower():
            recommended_months = 6
            st.warning("⚠️ Low-grade dysplasia - 6-month intervals recommended")
        else:
            recommended_months = 36
            st.info("ℹ️ No/low-grade dysplasia - 3-year intervals recommended")
    else:
        recommended_months = 36
    
    with st.form("add_surveillance_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            undecided = st.checkbox("Plan Undecided")
            if not undecided:
                # Calculate recommended date
                recommended_date = date.today() + timedelta(days=30 * recommended_months)
                next_egd = st.date_input("Next EGD Due Date", value=recommended_date)
            else:
                next_egd = None
        
        with col2:
            if has_barretts and not latest_barrett.empty:
                if st.button(f"🧠 Use Smart Interval ({recommended_months} months)"):
                    next_egd = date.today() + timedelta(days=30 * recommended_months)
        
        create_recall = st.checkbox("Create recall reminder", value=True) if not undecided else False
        
        submitted = st.form_submit_button("💾 Save Surveillance Plan", type="primary")
        
        if submitted:
            if not undecided and not next_egd:
                st.error("Please select a surveillance date or mark as undecided")
            elif not undecided and next_egd <= date.today():
                st.error("Surveillance date must be in the future")
            else:
                next_egd_str = next_egd.strftime("%Y-%m-%d") if next_egd else ""
                
                success = execute_query("""
                    INSERT INTO tblSurveillance (PatientID, NextBarrettsEGD, Undecided, LastModified)
                    VALUES (?, ?, ?, ?)
                """, (patient_id, next_egd_str, undecided, date.today().strftime("%Y-%m-%d")), fetch=False)
                
                if success:
                    # Create recall if requested
                    if create_recall and not undecided:
                        execute_query("""
                            INSERT INTO tblRecall (PatientID, RecallDate, RecallReason, Notes, Completed)
                            VALUES (?, ?, 'Endoscopy', 'Auto-created from Barrett''s Surveillance', 0)
                        """, (patient_id, next_egd_str), fetch=False)
                        st.success("Surveillance plan and recall created successfully!")
                    else:
                        st.success("Surveillance plan saved successfully!")
                    
                    st.session_state.show_add_form['surveillance'] = False
                    st.rerun()

# Add Recall Form
def show_add_recall_form(patient_id):
    """Show add recall form"""
    st.subheader("➕ Add Recall")
    
    with st.form("add_recall_form"):
        recall_date = st.date_input("Recall Date*", value=date.today() + timedelta(days=30))
        recall_reason = st.selectbox("Reason*", 
            ["", "Office Visit", "Endoscopy", "Barrett's Surveillance", 
             "Surveillance Form", "Post-op Follow-up", "Lab Review", "Other"])
        notes = st.text_area("Notes")
        
        submitted = st.form_submit_button("💾 Save Recall", type="primary")
        
        if submitted:
            if not recall_reason:
                st.error("Please select a recall reason")
            elif recall_date < date.today():
                st.error("Recall date should be today or in the future")
            else:
                success = execute_query("""
                    INSERT INTO tblRecall (PatientID, RecallDate, RecallReason, Notes, Completed)
                    VALUES (?, ?, ?, ?, 0)
                """, (patient_id, recall_date.strftime("%Y-%m-%d"), recall_reason, notes), fetch=False)
                
                if success:
                    st.success("Recall saved successfully!")
                    st.session_state.show_add_form['recall'] = False
                    st.rerun()

# Delete confirmation
def confirm_delete(item_type, item_id, item_name=""):
    """Show delete confirmation"""
    key = f"delete_{item_type}_{item_id}"
    if key not in st.session_state:
        st.session_state[key] = False
    
    if not st.session_state[key]:
        if st.button(f"🗑️ Delete", key=f"del_btn_{item_type}_{item_id}"):
            st.session_state[key] = True
            st.rerun()
    else:
        st.warning(f"Are you sure you want to delete this {item_type}?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Delete", key=f"confirm_{item_type}_{item_id}"):
                return True
        with col2:
            if st.button("❌ Cancel", key=f"cancel_{item_type}_{item_id}"):
                st.session_state[key] = False
                st.rerun()
    return False

# Export functions
def export_to_csv(data, filename):
    """Export dataframe to CSV"""
    csv_buffer = io.StringIO()
    data.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def generate_patient_summary_pdf(patient_id):
    """Generate patient summary PDF"""
    try:
        # Get patient data
        patient = execute_query("SELECT * FROM tblPatients WHERE PatientID = ?", (patient_id,))
        if patient.empty:
            return None
        
        patient = patient.iloc[0]
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"Patient Summary: {patient['LastName']}, {patient['FirstName']}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Demographics
        demo_data = [
            ['MRN:', patient['MRN']],
            ['DOB:', patient['DOB']],
            ['Gender:', patient['Gender']],
            ['BMI:', patient['BMI'] or 'Not recorded']
        ]
        demo_table = Table(demo_data)
        demo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(demo_table)
        story.append(Spacer(1, 12))
        
        # Add other sections as needed...
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

# Header
st.markdown("""
<div class="main-header">
    <h1>🏥 Minnesota Reflux & Heartburn Center</h1>
    <p>Clinical Management System</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Patient Search and Navigation
with st.sidebar:
    st.header("🔍 Patient Search")
    
    # Search functionality
    search_term = st.text_input("Search patients (name or MRN):", key="patient_search")
    
    # Add new patient button
    if st.button("➕ Add New Patient", use_container_width=True):
        st.session_state.show_add_form['patient'] = True
        st.session_state.selected_patient = None
        st.session_state.current_tab = "Add Patient"
        st.rerun()
    
    # Load patients
    if search_term:
        patients_df = execute_query("""
            SELECT PatientID, FirstName, LastName, MRN, DOB, Gender
            FROM tblPatients
            WHERE FirstName LIKE ? OR LastName LIKE ? OR MRN LIKE ?
            ORDER BY LastName, FirstName
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
    else:
        patients_df = execute_query("""
            SELECT PatientID, FirstName, LastName, MRN, DOB, Gender
            FROM tblPatients
            ORDER BY LastName, FirstName
            LIMIT 20
        """)
    
    if not patients_df.empty:
        st.subheader("Patients")
        for _, patient in patients_df.iterrows():
            patient_display = f"{patient['LastName']}, {patient['FirstName']} ({patient['MRN']})"
            if st.button(patient_display, key=f"patient_{patient['PatientID']}", use_container_width=True):
                st.session_state.selected_patient = patient['PatientID']
                st.session_state.current_tab = "Demographics"
                st.session_state.show_add_form = {}
                st.rerun()
    
    st.divider()
    
    # Navigation
    st.header("📊 Reports")
    if st.button("📞 Recall Management", use_container_width=True):
        st.session_state.selected_patient = None
        st.session_state.current_tab = "Recalls"
        st.session_state.show_add_form = {}
        st.rerun()
    
    if st.button("🔬 Barrett's Surveillance", use_container_width=True):
        st.session_state.selected_patient = None
        st.session_state.current_tab = "Barrett's"
        st.session_state.show_add_form = {}
        st.rerun()
    
    if st.button("📈 Dashboard", use_container_width=True):
        st.session_state.selected_patient = None
        st.session_state.current_tab = "Dashboard"
        st.session_state.show_add_form = {}
        st.rerun()

# Main content area
if st.session_state.current_tab == "Add Patient":
    show_add_patient_form()

elif st.session_state.selected_patient:
    # Patient selected - show patient tabs
    patient_id = st.session_state.selected_patient
    
    # Get patient info
    patient_info = execute_query("""
        SELECT FirstName, LastName, MRN, DOB, Gender, BMI, ZipCode, ReferralSource, ReferralDetails
        FROM tblPatients WHERE PatientID = ?
    """, (patient_id,))
    
    if not patient_info.empty:
        patient = patient_info.iloc[0]
        
        # Patient header
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.header(f"👤 {patient['LastName']}, {patient['FirstName']}")
        with col2:
            st.write(f"**MRN:** {patient['MRN']}")
        with col3:
            st.write(f"**DOB:** {patient['DOB']}")
        with col4:
            if st.button("🖨️ Print"):
                pdf_data = generate_patient_summary_pdf(patient_id)
                if pdf_data:
                    st.download_button(
                        "📄 Download PDF",
                        pdf_data,
                        f"{patient['LastName']}_{patient['FirstName']}_summary.pdf",
                        "application/pdf"
                    )
        
        # Patient tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "👤 Demographics", 
            "🔍 Diagnostics", 
            "🏥 Surgical", 
            "🧪 Pathology", 
            "📊 Surveillance", 
            "📞 Recalls"
        ])
        
        with tab1:
            st.subheader("Demographics")
            
            if st.button("✏️ Edit Demographics"):
                st.session_state.edit_mode = not st.session_state.edit_mode
                st.rerun()
            
            if st.session_state.edit_mode:
                # Edit mode
                with st.form("edit_demographics"):
                    col1, col2 = st.columns(2)
                    with col1:
                        first_name = st.text_input("First Name", value=patient['FirstName'])
                        last_name = st.text_input("Last Name", value=patient['LastName'])
                        mrn = st.text_input("MRN", value=patient['MRN'])
                        gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], 
                                            index=["", "Male", "Female", "Other"].index(patient['Gender']) if patient['Gender'] else 0)
                    with col2:
                        try:
                            dob = st.date_input("DOB", value=datetime.strptime(patient['DOB'], "%Y-%m-%d").date())
                        except:
                            dob = st.date_input("DOB")
                        bmi = st.number_input("BMI", value=float(patient['BMI']) if patient['BMI'] else None)
                        zip_code = st.text_input("ZIP Code", value=patient['ZipCode'] or "")
                        referral_source = st.selectbox("Referral Source", 
                                                     ["", "Self", "Physician", "Patient", "Other"],
                                                     index=["", "Self", "Physician", "Patient", "Other"].index(patient['ReferralSource']) if patient['ReferralSource'] else 0)
                    
                    referral_details = st.text_area("Referral Details", value=patient['ReferralDetails'] or "")
                    
                    if st.form_submit_button("💾 Save Changes"):
                        success = execute_query("""
                            UPDATE tblPatients SET
                                FirstName = ?, LastName = ?, MRN = ?, Gender = ?, 
                                DOB = ?, BMI = ?, ZipCode = ?, ReferralSource = ?, ReferralDetails = ?
                            WHERE PatientID = ?
                        """, (first_name, last_name, mrn, gender, dob.strftime("%Y-%m-%d"), 
                              bmi, zip_code, referral_source, referral_details, patient_id), fetch=False)
                        
                        if success:
                            st.success("Demographics updated successfully!")
                            st.session_state.edit_mode = False
                            st.rerun()
            else:
                # View mode
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**First Name:** {patient['FirstName']}")
                    st.write(f"**Last Name:** {patient['LastName']}")
                    st.write(f"**MRN:** {patient['MRN']}")
                    st.write(f"**Gender:** {patient['Gender'] or 'Not specified'}")
                with col2:
                    st.write(f"**DOB:** {patient['DOB']}")
                    st.write(f"**BMI:** {patient['BMI'] or 'Not recorded'}")
                    st.write(f"**ZIP Code:** {patient['ZipCode'] or 'Not specified'}")
                    st.write(f"**Referral Source:** {patient['ReferralSource'] or 'Not specified'}")
                
                if patient['ReferralDetails']:
                    st.write(f"**Referral Details:** {patient['ReferralDetails']}")
        
        with tab2:
            st.subheader("Diagnostic Studies")
            
            # Add/Show forms
            if st.session_state.show_add_form.get('diagnostic', False):
                show_add_diagnostic_form(patient_id)
            else:
                if st.button("➕ Add Diagnostic Study"):
                    st.session_state.show_add_form['diagnostic'] = True
                    st.rerun()
            
            # Load and display diagnostics
            diagnostics_df = execute_query("""
                SELECT DiagnosticID, TestDate, Surgeon, Endoscopy, Bravo, pHImpedance, 
                       EndoFLIP, Manometry, GastricEmptying, Imaging, UpperGI,
                       EsophagitisGrade, HiatalHerniaSize, DeMeesterScore, EndoscopyFindings,
                       pHFindings, DiagnosticNotes
                FROM tblDiagnostics
                WHERE PatientID = ?
                ORDER BY TestDate DESC
            """, (patient_id,))
            
            if not diagnostics_df.empty:
                for _, diag in diagnostics_df.iterrows():
                    with st.expander(f"📅 {diag['TestDate']} - Dr. {diag['Surgeon'] or 'Unknown'}"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write("**Tests Performed:**")
                            tests = []
                            if diag['Endoscopy']: tests.append("Endoscopy")
                            if diag['Bravo']: tests.append("Bravo")
                            if diag['pHImpedance']: tests.append("pH Impedance")
                            if diag['EndoFLIP']: tests.append("EndoFLIP")
                            if diag['Manometry']: tests.append("Manometry")
                            if diag['GastricEmptying']: tests.append("Gastric Emptying")
                            if diag['Imaging']: tests.append("Imaging")
                            if diag['UpperGI']: tests.append("Upper GI")
                            
                            for test in tests:
                                st.write(f"• {test}")
                        
                        with col2:
                            st.write("**Key Findings:**")
                            if diag['EsophagitisGrade']:
                                st.write(f"• Esophagitis: {diag['EsophagitisGrade']}")
                            if diag['HiatalHerniaSize']:
                                st.write(f"• Hiatal Hernia: {diag['HiatalHerniaSize']}")
                            if diag['DeMeesterScore']:
                                st.write(f"• DeMeester Score: {diag['DeMeesterScore']}")
                            
                            if diag['EndoscopyFindings']:
                                st.write(f"**Endoscopy:** {diag['EndoscopyFindings']}")
                            if diag['pHFindings']:
                                st.write(f"**pH Study:** {diag['pHFindings']}")
                            if diag['DiagnosticNotes']:
                                st.write(f"**Notes:** {diag['DiagnosticNotes']}")
                        
                        with col3:
                            if confirm_delete("diagnostic", diag['DiagnosticID']):
                                execute_query("DELETE FROM tblDiagnostics WHERE DiagnosticID = ?", 
                                            (diag['DiagnosticID'],), fetch=False)
                                st.success("Diagnostic deleted!")
                                st.rerun()
            else:
                st.info("No diagnostic studies recorded")
        
        with tab3:
            st.subheader("Surgical History")
            
            # Add/Show forms
            if st.session_state.show_add_form.get('surgical', False):
                show_add_surgical_form(patient_id)
            else:
                if st.button("➕ Add Surgery"):
                    st.session_state.show_add_form['surgical'] = True
                    st.rerun()
            
            # Load and display surgeries
            surgical_df = execute_query("""
                SELECT SurgeryID, SurgeryDate, SurgerySurgeon, Notes,
                       HiatalHernia, ParaesophagealHernia, MeshUsed, GastricBypass, SleeveGastrectomy,
                       Toupet, TIF, Nissen, Dor, HellerMyotomy, Stretta, Ablation, LINX,
                       GPOEM, EPOEM, ZPOEM, Pyloroplasty, Revision, GastricStimulator, Dilation, Other
                FROM tblSurgicalHistory
                WHERE PatientID = ?
                ORDER BY SurgeryDate DESC
            """, (patient_id,))
            
            if not surgical_df.empty:
                for _, surgery in surgical_df.iterrows():
                    with st.expander(f"🏥 {surgery['SurgeryDate']} - Dr. {surgery['SurgerySurgeon'] or 'Unknown'}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # List procedures performed
                            procedures = []
                            procedure_map = {
                                'HiatalHernia': 'Hiatal Hernia Repair',
                                'ParaesophagealHernia': 'Paraesophageal Hernia Repair',
                                'MeshUsed': 'Mesh Used',
                                'GastricBypass': 'Gastric Bypass',
                                'SleeveGastrectomy': 'Sleeve Gastrectomy',
                                'Toupet': 'Toupet Fundoplication',
                                'TIF': 'TIF',
                                'Nissen': 'Nissen Fundoplication',
                                'Dor': 'Dor Fundoplication',
                                'HellerMyotomy': 'Heller Myotomy',
                                'Stretta': 'Stretta',
                                'Ablation': 'Ablation',
                                'LINX': 'LINX Device',
                                'GPOEM': 'G-POEM',
                                'EPOEM': 'E-POEM',
                                'ZPOEM': 'Z-POEM',
                                'Pyloroplasty': 'Pyloroplasty',
                                'Revision': 'Revision Surgery',
                                'GastricStimulator': 'Gastric Stimulator',
                                'Dilation': 'Dilation',
                                'Other': 'Other'
                            }
                            
                            for key, name in procedure_map.items():
                                if surgery[key]:
                                    procedures.append(name)
                            
                            if procedures:
                                st.write("**Procedures:**")
                                for proc in procedures:
                                    st.write(f"• {proc}")
                            
                            if surgery['Notes']:
                                st.write("**Notes:**")
                                st.write(surgery['Notes'])
                        
                        with col2:
                            if confirm_delete("surgery", surgery['SurgeryID']):
                                execute_query("DELETE FROM tblSurgicalHistory WHERE SurgeryID = ?", 
                                            (surgery['SurgeryID'],), fetch=False)
                                st.success("Surgery deleted!")
                                st.rerun()
            else:
                st.info("No surgical history recorded")
        
        with tab4:
            st.subheader("Pathology Results")
            
            # Add/Show forms
            if st.session_state.show_add_form.get('pathology', False):
                show_add_pathology_form(patient_id)
            else:
                if st.button("➕ Add Pathology"):
                    st.session_state.show_add_form['pathology'] = True
                    st.rerun()
            
            # Load and display pathology
            pathology_df = execute_query("""
                SELECT PathologyID, PathologyDate, Biopsy, WATS3D, EsoPredict, TissueCypher,
                       Barretts, DysplasiaGrade, EoE, EosinophilCount, Hpylori, AtrophicGastritis,
                       OtherFinding, EsoPredictRisk, TissueCypherRisk, Notes
                FROM tblPathology
                WHERE PatientID = ?
                ORDER BY PathologyDate DESC
            """, (patient_id,))
            
            if not pathology_df.empty:
                for _, path in pathology_df.iterrows():
                    with st.expander(f"🧪 {path['PathologyDate']}"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write("**Tests:**")
                            tests = []
                            if path['Biopsy']: tests.append("Biopsy")
                            if path['WATS3D']: tests.append("WATS3D")
                            if path['EsoPredict']: tests.append("EsoPredict")
                            if path['TissueCypher']: tests.append("TissueCypher")
                            
                            for test in tests:
                                st.write(f"• {test}")
                        
                        with col2:
                            st.write("**Findings:**")
                            if path['Barretts']:
                                grade = path['DysplasiaGrade'] or "No grade specified"
                                if "high grade" in grade.lower():
                                    st.markdown(f"• **Barrett's:** <span class='status-urgent'>{grade}</span>", unsafe_allow_html=True)
                                elif "low grade" in grade.lower():
                                    st.markdown(f"• **Barrett's:** <span class='status-warning'>{grade}</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"• **Barrett's:** <span class='status-info'>{grade}</span>", unsafe_allow_html=True)
                            
                            if path['EoE']:
                                eos_count = path['EosinophilCount'] or "Not specified"
                                st.write(f"• **EoE:** {eos_count} eos/hpf")
                            
                            if path['Hpylori']:
                                st.write("• **H. pylori:** Positive")
                            
                            if path['AtrophicGastritis']:
                                st.write("• **Atrophic Gastritis:** Present")
                            
                            if path['OtherFinding']:
                                st.write(f"• **Other:** {path['OtherFinding']}")
                            
                            if path['EsoPredictRisk']:
                                st.write(f"• **EsoPredict:** {path['EsoPredictRisk']}")
                            
                            if path['TissueCypherRisk']:
                                st.write(f"• **TissueCypher:** {path['TissueCypherRisk']}")
                            
                            if path['Notes']:
                                st.write(f"• **Notes:** {path['Notes']}")
                        
                        with col3:
                            if confirm_delete("pathology", path['PathologyID']):
                                execute_query("DELETE FROM tblPathology WHERE PathologyID = ?", 
                                            (path['PathologyID'],), fetch=False)
                                st.success("Pathology deleted!")
                                st.rerun()
            else:
                st.info("No pathology results recorded")
        
        with tab5:
            st.subheader("Surveillance Plans")
            
            # Add/Show forms
            if st.session_state.show_add_form.get('surveillance', False):
                show_add_surveillance_form(patient_id)
            else:
                if st.button("➕ Add Surveillance Plan"):
                    st.session_state.show_add_form['surveillance'] = True
                    st.rerun()
            
            # Check Barrett's status
            barrett_status = execute_query("""
                SELECT PathologyDate, DysplasiaGrade
                FROM tblPathology
                WHERE PatientID = ? AND Barretts = 1
                ORDER BY PathologyDate DESC
                LIMIT 1
            """, (patient_id,))
            
            if not barrett_status.empty:
                latest_barrett = barrett_status.iloc[0]
                st.success(f"✅ Barrett's confirmed: {latest_barrett['DysplasiaGrade'] or 'No grade'} ({latest_barrett['PathologyDate']})")
                
                # Load surveillance plans
                surveillance_df = execute_query("""
                    SELECT SurveillanceID, NextBarrettsEGD, Undecided, LastModified
                    FROM tblSurveillance
                    WHERE PatientID = ?
                    ORDER BY LastModified DESC
                """, (patient_id,))
                
                if not surveillance_df.empty:
                    for _, surv in surveillance_df.iterrows():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            if surv['Undecided']:
                                st.warning("⚠️ Surveillance plan undecided")
                            else:
                                next_date = surv['NextBarrettsEGD']
                                try:
                                    egd_date = datetime.strptime(next_date, "%Y-%m-%d").date()
                                    today = date.today()
                                    days_until = (egd_date - today).days
                                    
                                    if days_until < 0:
                                        st.error(f"🚨 Surveillance OVERDUE: {next_date} ({abs(days_until)} days ago)")
                                    elif days_until <= 90:
                                        st.warning(f"⚠️ Surveillance due soon: {next_date} (in {days_until} days)")
                                    else:
                                        st.info(f"📅 Next surveillance: {next_date} (in {days_until} days)")
                                except:
                                    st.write(f"📅 Next surveillance: {next_date}")
                            
                            st.caption(f"Last modified: {surv['LastModified']}")
                        
                        with col2:
                            if confirm_delete("surveillance", surv['SurveillanceID']):
                                execute_query("DELETE FROM tblSurveillance WHERE SurveillanceID = ?", 
                                            (surv['SurveillanceID'],), fetch=False)
                                st.success("Surveillance plan deleted!")
                                st.rerun()
                else:
                    st.warning("⚠️ No surveillance plan on file for Barrett's patient")
            else:
                st.info("ℹ️ No Barrett's esophagus in pathology history")
        
        with tab6:
            st.subheader("Recalls & Follow-up")
            
            # Add/Show forms
            if st.session_state.show_add_form.get('recall', False):
                show_add_recall_form(patient_id)
            else:
                if st.button("➕ Add Recall"):
                    st.session_state.show_add_form['recall'] = True
                    st.rerun()
            
            # Load recalls
            recalls_df = execute_query("""
                SELECT RecallID, RecallDate, RecallReason, Notes, Completed
                FROM tblRecall
                WHERE PatientID = ?
                ORDER BY RecallDate ASC
            """, (patient_id,))
            
            if not recalls_df.empty:
                for _, recall in recalls_df.iterrows():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if recall['Completed']:
                            st.success(f"✅ {recall['RecallReason']} - {recall['RecallDate']} (Completed)")
                        else:
                            try:
                                recall_date = datetime.strptime(recall['RecallDate'], "%Y-%m-%d").date()
                                today = date.today()
                                days_until = (recall_date - today).days
                                
                                if days_until < 0:
                                    st.error(f"🚨 OVERDUE: {recall['RecallReason']} - {recall['RecallDate']} ({abs(days_until)} days ago)")
                                elif days_until == 0:
                                    st.warning(f"⚠️ DUE TODAY: {recall['RecallReason']} - {recall['RecallDate']}")
                                elif days_until <= 7:
                                    st.warning(f"⚠️ Due soon: {recall['RecallReason']} - {recall['RecallDate']} (in {days_until} days)")
                                else:
                                    st.info(f"📅 {recall['RecallReason']} - {recall['RecallDate']} (in {days_until} days)")
                            except:
                                st.write(f"📅 {recall['RecallReason']} - {recall['RecallDate']}")
                        
                        if recall['Notes']:
                            st.caption(recall['Notes'])
                        
                        # Toggle completion
                        if not recall['Completed']:
                            if st.button(f"Mark Complete", key=f"complete_{recall['RecallID']}"):
                                execute_query("UPDATE tblRecall SET Completed = 1 WHERE RecallID = ?", 
                                            (recall['RecallID'],), fetch=False)
                                st.success("Recall marked complete!")
                                st.rerun()
                    
                    with col2:
                        if confirm_delete("recall", recall['RecallID']):
                            execute_query("DELETE FROM tblRecall WHERE RecallID = ?", 
                                        (recall['RecallID'],), fetch=False)
                            st.success("Recall deleted!")
                            st.rerun()
            else:
                st.info("No recalls scheduled")

elif st.session_state.current_tab == "Dashboard":
    # Dashboard view
    st.header("📈 Clinical Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_patients = execute_query("SELECT COUNT(*) as count FROM tblPatients")
        count = total_patients.iloc[0]['count'] if not total_patients.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>{count}</h3>
            <p>Total Patients</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        barrett_patients = execute_query("SELECT COUNT(DISTINCT PatientID) as count FROM tblPathology WHERE Barretts = 1")
        count = barrett_patients.iloc[0]['count'] if not barrett_patients.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>{count}</h3>
            <p>Barrett's Patients</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        overdue_recalls = execute_query("SELECT COUNT(*) as count FROM tblRecall WHERE Completed = 0 AND RecallDate < date('now')")
        count = overdue_recalls.iloc[0]['count'] if not overdue_recalls.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3 class="status-urgent">{count}</h3>
            <p>Overdue Recalls</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        high_grade = execute_query("SELECT COUNT(DISTINCT PatientID) as count FROM tblPathology WHERE Barretts = 1 AND DysplasiaGrade LIKE '%High Grade%'")
        count = high_grade.iloc[0]['count'] if not high_grade.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3 class="status-urgent">{count}</h3>
            <p>High-Grade Dysplasia</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Activity")
        
        # Recent procedures
        recent_surgeries = execute_query("""
            SELECT DATE(SurgeryDate) as date, COUNT(*) as count
            FROM tblSurgicalHistory
            WHERE SurgeryDate >= date('now', '-12 months')
            GROUP BY DATE(SurgeryDate)
            ORDER BY date
        """)
        
        if not recent_surgeries.empty:
            fig = px.line(recent_surgeries, x='date', y='count', 
                         title="Surgical Procedures (Last 12 Months)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent surgical data available")
    
    with col2:
        st.subheader("Barrett's Surveillance Status")
        
        surveillance_status = execute_query("""
            SELECT 
                CASE 
                    WHEN Undecided = 1 THEN 'Undecided'
                    WHEN NextBarrettsEGD < date('now') THEN 'Overdue'
                    WHEN NextBarrettsEGD <= date('now', '+90 days') THEN 'Due Soon'
                    ELSE 'Future'
                END as status,
                COUNT(*) as count
            FROM tblSurveillance
            GROUP BY status
        """)
        
        if not surveillance_status.empty:
            fig = px.pie(surveillance_status, values='count', names='status',
                        title="Surveillance Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No surveillance data available")
    
    # Export functionality
    st.divider()
    st.subheader("📊 Data Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export All Patients"):
            all_patients = execute_query("SELECT * FROM tblPatients ORDER BY LastName, FirstName")
            if not all_patients.empty:
                csv_data = export_to_csv(all_patients, "all_patients.csv")
                st.download_button(
                    "⬇️ Download Patient List CSV",
                    csv_data,
                    "all_patients.csv",
                    "text/csv"
                )
    
    with col2:
        if st.button("🔬 Export Barrett's Data"):
            barrett_data = execute_query("""
                SELECT P.LastName, P.FirstName, P.MRN, Path.PathologyDate, Path.DysplasiaGrade,
                       S.NextBarrettsEGD, S.Undecided
                FROM tblPatients P
                JOIN tblPathology Path ON P.PatientID = Path.PatientID
                LEFT JOIN tblSurveillance S ON P.PatientID = S.PatientID
                WHERE Path.Barretts = 1
                ORDER BY P.LastName, P.FirstName
            """)
            if not barrett_data.empty:
                csv_data = export_to_csv(barrett_data, "barrett_surveillance.csv")
                st.download_button(
                    "⬇️ Download Barrett's Data CSV",
                    csv_data,
                    "barrett_surveillance.csv",
                    "text/csv"
                )
    
    with col3:
        if st.button("📞 Export Recalls"):
            recalls_data = execute_query("""
                SELECT P.LastName, P.FirstName, P.MRN, R.RecallDate, R.RecallReason, 
                       R.Notes, R.Completed
                FROM tblRecall R
                JOIN tblPatients P ON R.PatientID = P.PatientID
                ORDER BY R.RecallDate
            """)
            if not recalls_data.empty:
                csv_data = export_to_csv(recalls_data, "recalls.csv")
                st.download_button(
                    "⬇️ Download Recalls CSV",
                    csv_data,
                    "recalls.csv",
                    "text/csv"
                )

elif st.session_state.current_tab == "Recalls":
    # Recall management
    st.header("📞 Recall Management")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        recall_filter = st.selectbox("Filter by status:", ["All", "Overdue", "Due Today", "Due This Week", "Completed"])
    with col2:
        reason_filter = st.selectbox("Filter by reason:", ["All", "Office Visit", "Endoscopy", "Barrett's Surveillance"])
    with col3:
        priority_filter = st.selectbox("Priority:", ["All", "Critical", "High", "Medium", "Low"])
    with col4:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Build query based on filters
    where_clauses = []
    params = []
    
    if recall_filter == "Overdue":
        where_clauses.append("R.Completed = 0 AND R.RecallDate < date('now')")
    elif recall_filter == "Due Today":
        where_clauses.append("R.Completed = 0 AND R.RecallDate = date('now')")
    elif recall_filter == "Due This Week":
        where_clauses.append("R.Completed = 0 AND R.RecallDate BETWEEN date('now') AND date('now', '+7 days')")
    elif recall_filter == "Completed":
        where_clauses.append("R.Completed = 1")
    
    if reason_filter != "All":
        where_clauses.append("R.RecallReason = ?")
        params.append(reason_filter)
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    recalls_query = f"""
        SELECT R.RecallID, R.RecallDate, R.RecallReason, R.Notes, R.Completed,
               P.FirstName, P.LastName, P.MRN, P.PatientID
        FROM tblRecall R
        JOIN tblPatients P ON R.PatientID = P.PatientID
        WHERE {where_clause}
        ORDER BY R.RecallDate ASC
    """
    
    recalls_df = execute_query(recalls_query, params)
    
    # Bulk actions
    if not recalls_df.empty:
        st.subheader("🔧 Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_recalls = st.multiselect(
                "Select recalls for bulk actions:",
                options=recalls_df['RecallID'].tolist(),
                format_func=lambda x: f"{recalls_df[recalls_df['RecallID']==x].iloc[0]['LastName']}, {recalls_df[recalls_df['RecallID']==x].iloc[0]['FirstName']} - {recalls_df[recalls_df['RecallID']==x].iloc[0]['RecallReason']}"
            )
        
        with col2:
            if selected_recalls and st.button("✅ Mark Selected Complete"):
                for recall_id in selected_recalls:
                    execute_query("UPDATE tblRecall SET Completed = 1 WHERE RecallID = ?", 
                                (recall_id,), fetch=False)
                st.success(f"Marked {len(selected_recalls)} recalls as complete!")
                st.rerun()
        
        with col3:
            if selected_recalls and st.button("📅 Bulk Reschedule"):
                new_date = st.date_input("New date:", value=date.today() + timedelta(days=7))
                if st.button("Confirm Reschedule"):
                    for recall_id in selected_recalls:
                        execute_query("UPDATE tblRecall SET RecallDate = ? WHERE RecallID = ?", 
                                    (new_date.strftime("%Y-%m-%d"), recall_id), fetch=False)
                    st.success(f"Rescheduled {len(selected_recalls)} recalls!")
                    st.rerun()
    
    if not recalls_df.empty:
        st.subheader(f"Recalls ({len(recalls_df)} found)")
        
        # Export current results
        if st.button("📊 Export Current Results"):
            csv_data = export_to_csv(recalls_df, "filtered_recalls.csv")
            st.download_button(
                "⬇️ Download CSV",
                csv_data,
                "filtered_recalls.csv",
                "text/csv"
            )
        
        for _, recall in recalls_df.iterrows():
            patient_name = f"{recall['LastName']}, {recall['FirstName']} ({recall['MRN']})"
            
            # Determine status color and priority
            status_class = ""
            priority = "Low"
            
            if not recall['Completed']:
                try:
                    recall_date = datetime.strptime(recall['RecallDate'], "%Y-%m-%d").date()
                    today = date.today()
                    days_until = (recall_date - today).days
                    
                    # Check if patient has Barrett's for priority
                    barrett_check = execute_query("""
                        SELECT COUNT(*) as count FROM tblPathology 
                        WHERE PatientID = ? AND Barretts = 1
                    """, (recall['PatientID'],))
                    has_barretts = not barrett_check.empty and barrett_check.iloc[0]['count'] > 0
                    
                    if days_until < 0:
                        status_class = "status-urgent"
                        status_text = f"OVERDUE ({abs(days_until)} days)"
                        priority = "Critical" if has_barretts else "High"
                    elif days_until == 0:
                        status_class = "status-warning"
                        status_text = "DUE TODAY"
                        priority = "High"
                    elif days_until <= 7:
                        status_class = "status-warning"
                        status_text = f"Due in {days_until} days"
                        priority = "Medium"
                    else:
                        status_class = "status-info"
                        status_text = f"Due in {days_until} days"
                        priority = "Low"
                except:
                    status_text = "Invalid date"
                    priority = "Medium"
            else:
                status_class = "status-success"
                status_text = "COMPLETED"
                priority = "Completed"
            
            # Filter by priority if selected
            if priority_filter != "All" and priority != priority_filter:
                continue
            
            with st.expander(f"{patient_name} - {recall['RecallReason']} ({recall['RecallDate']}) - {priority}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"**Status:** <span class='{status_class}'>{status_text}</span>", unsafe_allow_html=True)
                    st.write(f"**Reason:** {recall['RecallReason']}")
                    st.write(f"**Priority:** {priority}")
                    if recall['Notes']:
                        st.write(f"**Notes:** {recall['Notes']}")
                
                with col2:
                    if not recall['Completed']:
                        if st.button(f"✅ Mark Complete", key=f"complete_recall_{recall['RecallID']}"):
                            execute_query("UPDATE tblRecall SET Completed = 1 WHERE RecallID = ?", 
                                        (recall['RecallID'],), fetch=False)
                            st.success("Recall marked complete!")
                            st.rerun()
                        
                        new_date = st.date_input(f"Reschedule to:", 
                                               value=date.today() + timedelta(days=7),
                                               key=f"reschedule_{recall['RecallID']}")
                        if st.button(f"📅 Reschedule", key=f"reschedule_btn_{recall['RecallID']}"):
                            execute_query("UPDATE tblRecall SET RecallDate = ? WHERE RecallID = ?", 
                                        (new_date.strftime("%Y-%m-%d"), recall['RecallID']), fetch=False)
                            st.success("Recall rescheduled!")
                            st.rerun()
                
                with col3:
                    if st.button(f"👤 Open Patient", key=f"open_patient_{recall['RecallID']}"):
                        st.session_state.selected_patient = recall['PatientID']
                        st.session_state.current_tab = "Demographics"
                        st.rerun()
                    
                    if confirm_delete("recall", recall['RecallID']):
                        execute_query("DELETE FROM tblRecall WHERE RecallID = ?", 
                                    (recall['RecallID'],), fetch=False)
                        st.success("Recall deleted!")
                        st.rerun()
    else:
        st.info("No recalls found matching the selected criteria")

elif st.session_state.current_tab == "Barrett's":
    # Barrett's surveillance
    st.header("🔬 Barrett's Surveillance Management")
    
    # Get Barrett's patients with surveillance status
    barrett_query = """
        SELECT DISTINCT
            P.PatientID, P.FirstName, P.LastName, P.MRN,
            Path.PathologyDate, Path.DysplasiaGrade,
            S.NextBarrettsEGD, S.Undecided
        FROM tblPatients P
        JOIN tblPathology Path ON P.PatientID = Path.PatientID
        LEFT JOIN (
            SELECT PatientID, NextBarrettsEGD, Undecided,
                   ROW_NUMBER() OVER (PARTITION BY PatientID ORDER BY LastModified DESC) as rn
            FROM tblSurveillance
        ) S ON P.PatientID = S.PatientID AND S.rn = 1
        WHERE Path.Barretts = 1
        ORDER BY P.LastName, P.FirstName
    """
    
    barrett_df = execute_query(barrett_query)
    
    if not barrett_df.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_barrett = len(barrett_df)
            st.metric("Total Barrett's Patients", total_barrett)
        
        with col2:
            high_grade_count = len(barrett_df[barrett_df['DysplasiaGrade'].str.contains('High Grade', na=False)])
            st.metric("High-Grade Dysplasia", high_grade_count)
        
        with col3:
            overdue_count = 0
            for _, row in barrett_df.iterrows():
                if not row['Undecided'] and row['NextBarrettsEGD']:
                    try:
                        egd_date = datetime.strptime(row['NextBarrettsEGD'], "%Y-%m-%d").date()
                        if egd_date < date.today():
                            overdue_count += 1
                    except:
                        pass
            st.metric("Overdue Surveillance", overdue_count)
        
        with col4:
            no_plan_count = len(barrett_df[barrett_df['NextBarrettsEGD'].isna() | barrett_df['Undecided']])
            st.metric("No Surveillance Plan", no_plan_count)
        
        # Export Barrett's data
        if st.button("📊 Export Barrett's Surveillance Data"):
            csv_data = export_to_csv(barrett_df, "barrett_surveillance.csv")
            st.download_button(
                "⬇️ Download Barrett's CSV",
                csv_data,
                "barrett_surveillance.csv",
                "text/csv"
            )
        
        st.divider()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            grade_filter = st.selectbox("Filter by dysplasia grade:", 
                                      ["All"] + barrett_df['DysplasiaGrade'].dropna().unique().tolist())
        with col2:
            status_filter = st.selectbox("Surveillance status:", 
                                       ["All", "Overdue", "Due Soon (90 days)", "No Plan", "Future"])
        with col3:
            priority_filter = st.selectbox("Priority level:", 
                                         ["All", "Critical", "High", "Medium"])
        
        # Patient list
        st.subheader("Barrett's Patients")
        
        for _, patient in barrett_df.iterrows():
            # Apply filters
            if grade_filter != "All" and patient['DysplasiaGrade'] != grade_filter:
                continue
            
            patient_name = f"{patient['LastName']}, {patient['FirstName']} ({patient['MRN']})"
            grade = patient['DysplasiaGrade'] or "No grade specified"
            
            # Determine surveillance status and priority
            surveillance_status = ""
            status_class = ""
            priority = "Medium"
            
            if patient['Undecided']:
                surveillance_status = "⚠️ Plan undecided"
                status_class = "status-warning"
                priority = "High"
            elif patient['NextBarrettsEGD']:
                try:
                    egd_date = datetime.strptime(patient['NextBarrettsEGD'], "%Y-%m-%d").date()
                    today = date.today()
                    days_until = (egd_date - today).days
                    
                    if days_until < 0:
                        surveillance_status = f"🚨 OVERDUE by {abs(days_until)} days"
                        status_class = "status-urgent"
                        priority = "Critical" if "high grade" in grade.lower() else "High"
                    elif days_until <= 90:
                        surveillance_status = f"⚠️ Due in {days_until} days"
                        status_class = "status-warning"
                        priority = "High" if "high grade" in grade.lower() else "Medium"
                    else:
                        surveillance_status = f"📅 Due in {days_until} days"
                        status_class = "status-info"
                        priority = "Medium"
                except:
                    surveillance_status = "❓ Invalid date"
                    status_class = "status-warning"
                    priority = "High"
            else:
                surveillance_status = "❌ No plan on file"
                status_class = "status-urgent"
                priority = "Critical" if "high grade" in grade.lower() else "High"
            
            # Apply status filter
            if status_filter != "All":
                if status_filter == "Overdue" and "OVERDUE" not in surveillance_status:
                    continue
                elif status_filter == "Due Soon (90 days)" and "Due in" not in surveillance_status:
                    continue
                elif status_filter == "No Plan" and "No plan" not in surveillance_status and "undecided" not in surveillance_status:
                    continue
                elif status_filter == "Future" and ("OVERDUE" in surveillance_status or "Due in" in surveillance_status):
                    continue
            
            # Apply priority filter
            if priority_filter != "All" and priority != priority_filter:
                continue
            
            with st.expander(f"{patient_name} - {grade} - {priority} Priority"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Latest Pathology:** {patient['PathologyDate']} - {grade}")
                    st.markdown(f"**Surveillance Status:** <span class='{status_class}'>{surveillance_status}</span>", unsafe_allow_html=True)
                    st.write(f"**Priority Level:** {priority}")
                    
                    # Clinical recommendations
                    if "high grade" in grade.lower():
                        st.error("🚨 High-grade dysplasia requires 3-month surveillance intervals")
                    elif "low grade" in grade.lower():
                        st.warning("⚠️ Low-grade dysplasia requires 6-month surveillance intervals")
                    elif "no dysplasia" in grade.lower():
                        st.info("ℹ️ No dysplasia - 3-year surveillance intervals recommended")
                
                with col2:
                    if st.button(f"👤 Open Patient", key=f"barrett_{patient['PatientID']}"):
                        st.session_state.selected_patient = patient['PatientID']
                        st.session_state.current_tab = "Demographics"
                        st.rerun()
    else:
        st.info("No Barrett's patients found in the database")

else:
    # Default view - Search/Welcome
    st.header("🔍 Search for a Patient")
    st.write("Use the sidebar to search for patients by name or MRN, or access clinical reports.")
    
    # Quick stats on main page
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Quick Statistics")
        
        # Recent activity
        recent_patients = execute_query("""
            SELECT COUNT(*) as count
            FROM tblPatients
            WHERE InitialConsultDate >= date('now', '-30 days')
        """)
        
        recent_surgeries = execute_query("""
            SELECT COUNT(*) as count
            FROM tblSurgicalHistory
            WHERE SurgeryDate >= date('now', '-30 days')
        """)
        
        recent_pathology = execute_query("""
            SELECT COUNT(*) as count
            FROM tblPathology
            WHERE PathologyDate >= date('now', '-30 days')
        """)
        
        if not recent_patients.empty:
            st.metric("New Patients (30 days)", recent_patients.iloc[0]['count'])
        if not recent_surgeries.empty:
            st.metric("Recent Surgeries (30 days)", recent_surgeries.iloc[0]['count'])
        if not recent_pathology.empty:
            st.metric("Recent Pathology (30 days)", recent_pathology.iloc[0]['count'])
    
    with col2:
        st.subheader("🚨 Urgent Items")
        
        # High-priority alerts
        high_grade_overdue = execute_query("""
            SELECT COUNT(DISTINCT P.PatientID) as count
            FROM tblPatients P
            JOIN tblPathology Path ON P.PatientID = Path.PatientID
            LEFT JOIN tblSurveillance S ON P.PatientID = S.PatientID
            WHERE Path.Barretts = 1 
            AND Path.DysplasiaGrade LIKE '%High Grade%'
            AND (S.NextBarrettsEGD IS NULL OR S.NextBarrettsEGD < date('now'))
        """)
        
        overdue_recalls_today = execute_query("""
            SELECT COUNT(*) as count
            FROM tblRecall
            WHERE Completed = 0 AND RecallDate <= date('now')
        """)
        
        if not high_grade_overdue.empty:
            count = high_grade_overdue.iloc[0]['count']
            if count > 0:
                st.error(f"🚨 {count} High-Grade Dysplasia patients need surveillance")
        
        if not overdue_recalls_today.empty:
            count = overdue_recalls_today.iloc[0]['count']
            if count > 0:
                st.warning(f"⚠️ {count} Overdue recalls")
    
    st.divider()
    
    # Recent patients for quick access
    st.subheader("📋 Recently Modified Patients")
    recent_modified = execute_query("""
        SELECT DISTINCT P.PatientID, P.FirstName, P.LastName, P.MRN,
               MAX(COALESCE(D.TestDate, S.SurgeryDate, Path.PathologyDate, P.InitialConsultDate)) as LastActivity
        FROM tblPatients P
        LEFT JOIN tblDiagnostics D ON P.PatientID = D.PatientID
        LEFT JOIN tblSurgicalHistory S ON P.PatientID = S.PatientID
        LEFT JOIN tblPathology Path ON P.PatientID = Path.PatientID
        GROUP BY P.PatientID, P.FirstName, P.LastName, P.MRN
        ORDER BY LastActivity DESC
        LIMIT 10
    """)
    
    if not recent_modified.empty:
        for _, patient in recent_modified.iterrows():
            patient_display = f"{patient['LastName']}, {patient['FirstName']} ({patient['MRN']}) - Last activity: {patient['LastActivity']}"
            if st.button(patient_display, key=f"recent_{patient['PatientID']}", use_container_width=True):
                st.session_state.selected_patient = patient['PatientID']
                st.session_state.current_tab = "Demographics"
                st.rerun()

# Footer
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption("Minnesota Reflux & Heartburn Center - Clinical Management System")
    st.caption(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col2:
    # Database info
    try:
        db_stats = execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM tblPatients) as patients,
                (SELECT COUNT(*) FROM tblDiagnostics) as diagnostics,
                (SELECT COUNT(*) FROM tblSurgicalHistory) as surgeries,
                (SELECT COUNT(*) FROM tblPathology) as pathology
        """)
        if not db_stats.empty:
            stats = db_stats.iloc[0]
            st.caption(f"Database: {stats['patients']} patients, {stats['diagnostics']} diagnostics, {stats['surgeries']} surgeries, {stats['pathology']} pathology")
    except:
        st.caption("Database connection active")