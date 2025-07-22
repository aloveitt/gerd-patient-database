from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import sqlite3
import os
import tempfile
import webbrowser
from datetime import datetime, date
import re

def generate_surgeon_optimized_summary(patient_id):
    """Generate a surgeon-optimized patient summary for clinical use"""
    
    # Get patient data
    conn = sqlite3.connect("gerd_center.db")
    cur = conn.cursor()

    # Get patient demographics
    cur.execute("SELECT FirstName, LastName, MRN, DOB, Gender, BMI FROM tblPatients WHERE PatientID = ?", (patient_id,))
    patient_row = cur.fetchone()
    if not patient_row:
        conn.close()
        return None

    first, last, mrn, dob, gender, bmi = patient_row
    
    # Calculate age
    try:
        birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        age = "Unknown"

    # Create filename and document
    filename = f"{last}_{first}_Clinical_Summary.pdf"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    styles = getSampleStyleSheet()
    elements = []

    # Custom styles for medical documentation
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        spaceAfter=20,
        alignment=1,  # Center
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.darkgreen,
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )
    
    clinical_style = ParagraphStyle(
        'Clinical',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        fontName='Helvetica'
    )
    
    alert_style = ParagraphStyle(
        'Alert',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.red,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    # Document title and patient header
    title = Paragraph("GERD PATIENT CLINICAL SUMMARY", title_style)
    elements.append(title)
    
    # Patient demographics box
    demo_data = [
        ["Patient:", f"{last}, {first}", "MRN:", mrn],
        ["DOB:", dob, "Age:", str(age)],
        ["Gender:", gender or "Not specified", "BMI:", bmi or "Not recorded"]
    ]
    
    demo_table = Table(demo_data, colWidths=[1*inch, 2*inch, 1*inch, 1.5*inch])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(demo_table)
    elements.append(Spacer(1, 20))

    # Clinical alerts section - Most important for surgeons
    clinical_alerts = get_clinical_alerts(cur, patient_id)
    if clinical_alerts:
        elements.append(Paragraph("🚨 CLINICAL ALERTS", header_style))
        for alert in clinical_alerts:
            elements.append(Paragraph(f"• {alert}", alert_style))
        elements.append(Spacer(1, 15))

    # Barrett's surveillance status - Critical for GERD practice
    barretts_status = get_barretts_surveillance_status(cur, patient_id)
    if barretts_status:
        elements.append(Paragraph("🔬 BARRETT'S SURVEILLANCE STATUS", header_style))
        elements.append(Paragraph(barretts_status, clinical_style))
        elements.append(Spacer(1, 15))

    # Recent pathology - Last 2 most important
    elements.append(Paragraph("🧪 RECENT PATHOLOGY", header_style))
    pathology_summary = get_recent_pathology_summary(cur, patient_id, limit=2)
    if pathology_summary:
        elements.append(Paragraph(pathology_summary, clinical_style))
    else:
        elements.append(Paragraph("No recent pathology on file", clinical_style))
    elements.append(Spacer(1, 15))

    # Recent diagnostics - Last 2 most important  
    elements.append(Paragraph("🔍 RECENT DIAGNOSTIC STUDIES", header_style))
    diagnostic_summary = get_recent_diagnostics_summary(cur, patient_id, limit=2)
    if diagnostic_summary:
        elements.append(Paragraph(diagnostic_summary, clinical_style))
    else:
        elements.append(Paragraph("No recent diagnostic studies on file", clinical_style))
    elements.append(Spacer(1, 15))

    # Surgical history - All procedures
    elements.append(Paragraph("🏥 SURGICAL HISTORY", header_style))
    surgical_summary = get_surgical_history_summary(cur, patient_id)
    if surgical_summary:
        elements.append(Paragraph(surgical_summary, clinical_style))
    else:
        elements.append(Paragraph("No prior GERD-related surgeries on file", clinical_style))
    elements.append(Spacer(1, 15))

    # Current recalls and follow-up
    elements.append(Paragraph("📅 FOLLOW-UP & RECALLS", header_style))
    recall_summary = get_recall_summary(cur, patient_id)
    if recall_summary:
        elements.append(Paragraph(recall_summary, clinical_style))
    else:
        elements.append(Paragraph("No pending recalls", clinical_style))

    # Footer with generation info
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1  # Center
    )
    footer_text = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Minnesota Reflux & Heartburn Center"
    elements.append(Paragraph(footer_text, footer_style))

    conn.close()

    # Build PDF
    try:
        doc.build(elements)
        
        # Open the PDF
        webbrowser.open_new(filepath)
        return filepath
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

def get_clinical_alerts(cur, patient_id):
    """Generate clinical alerts that surgeons need to know immediately"""
    alerts = []
    
    # Check for high-grade dysplasia
    cur.execute("""
        SELECT PathologyDate, DysplasiaGrade 
        FROM tblPathology 
        WHERE PatientID = ? AND Barretts = 1 AND DysplasiaGrade LIKE '%High Grade%'
        ORDER BY PathologyDate DESC LIMIT 1
    """, (patient_id,))
    hgd_result = cur.fetchone()
    if hgd_result:
        alerts.append(f"HIGH-GRADE DYSPLASIA: Last documented {hgd_result[0]} - Requires 3-month surveillance")
    
    # Check for overdue Barrett's surveillance
    cur.execute("""
        SELECT NextBarrettsEGD FROM tblSurveillance 
        WHERE PatientID = ? AND NextBarrettsEGD IS NOT NULL AND NextBarrettsEGD != ''
        AND NextBarrettsEGD < date('now', '-30 days')
        ORDER BY LastModified DESC LIMIT 1
    """, (patient_id,))
    overdue_result = cur.fetchone()
    if overdue_result:
        alerts.append(f"OVERDUE SURVEILLANCE: Barrett's EGD was due {overdue_result[0]}")
    
    # Check for recent concerning pathology
    cur.execute("""
        SELECT PathologyDate, DysplasiaGrade, Notes 
        FROM tblPathology 
        WHERE PatientID = ? AND PathologyDate > date('now', '-12 months')
        AND (DysplasiaGrade LIKE '%Low Grade%' OR DysplasiaGrade LIKE '%Indeterminate%')
        ORDER BY PathologyDate DESC LIMIT 1
    """, (patient_id,))
    concerning_path = cur.fetchone()
    if concerning_path:
        alerts.append(f"DYSPLASIA DETECTED: {concerning_path[1]} on {concerning_path[0]} - Monitor closely")
    
    # Check for recent failed anti-reflux surgery
    cur.execute("""
        SELECT SurgeryDate, Notes FROM tblSurgicalHistory 
        WHERE PatientID = ? AND Revision = 1 
        ORDER BY SurgeryDate DESC LIMIT 1
    """, (patient_id,))
    revision_surgery = cur.fetchone()
    if revision_surgery:
        alerts.append(f"REVISION SURGERY: Previous anti-reflux surgery revised on {revision_surgery[0]}")
    
    return alerts

def get_barretts_surveillance_status(cur, patient_id):
    """Get comprehensive Barrett's surveillance status"""
    # Check if patient has Barrett's
    cur.execute("""
        SELECT PathologyDate, DysplasiaGrade, Notes 
        FROM tblPathology 
        WHERE PatientID = ? AND Barretts = 1 
        ORDER BY PathologyDate DESC LIMIT 1
    """, (patient_id,))
    barretts_result = cur.fetchone()
    
    if not barretts_result:
        return "No Barrett's esophagus documented"
    
    path_date, dysplasia_grade, notes = barretts_result
    
    # Get current surveillance plan
    cur.execute("""
        SELECT NextBarrettsEGD, Undecided FROM tblSurveillance 
        WHERE PatientID = ? 
        ORDER BY LastModified DESC LIMIT 1
    """, (patient_id,))
    surveillance_result = cur.fetchone()
    
    status = f"<b>Barrett's Confirmed:</b> {path_date}<br/>"
    status += f"<b>Latest Dysplasia Grade:</b> {dysplasia_grade or 'Not specified'}<br/>"
    
    if surveillance_result:
        next_egd, undecided = surveillance_result
        if undecided:
            status += f"<b>Surveillance Plan:</b> <font color='red'>UNDECIDED - Needs planning</font><br/>"
        elif next_egd:
            # Calculate days until next EGD
            try:
                next_date = datetime.strptime(next_egd, "%Y-%m-%d").date()
                today = date.today()
                days_diff = (next_date - today).days
                
                if days_diff < 0:
                    status += f"<b>Next Surveillance:</b> <font color='red'>OVERDUE by {abs(days_diff)} days ({next_egd})</font><br/>"
                elif days_diff <= 90:
                    status += f"<b>Next Surveillance:</b> <font color='orange'>Due {next_egd} (in {days_diff} days)</font><br/>"
                else:
                    status += f"<b>Next Surveillance:</b> {next_egd} (in {days_diff} days)<br/>"
            except:
                status += f"<b>Next Surveillance:</b> {next_egd}<br/>"
        else:
            status += f"<b>Surveillance Plan:</b> <font color='red'>No plan documented</font><br/>"
    else:
        status += f"<b>Surveillance Plan:</b> <font color='red'>No surveillance plan on file</font><br/>"
    
    # Add guideline recommendation
    if dysplasia_grade:
        if "high grade" in dysplasia_grade.lower():
            status += f"<b>Guideline Recommendation:</b> 3-month intervals"
        elif "low grade" in dysplasia_grade.lower():
            status += f"<b>Guideline Recommendation:</b> 6-month intervals"
        elif "no dysplasia" in dysplasia_grade.lower() or "ngim" in dysplasia_grade.lower():
            status += f"<b>Guideline Recommendation:</b> 3-year intervals"
        else:
            status += f"<b>Guideline Recommendation:</b> Individualize based on risk factors"
    
    return status

def get_recent_pathology_summary(cur, patient_id, limit=2):
    """Get summary of recent pathology results"""
    cur.execute("""
        SELECT PathologyDate, Biopsy, WATS3D, EsoPredict, TissueCypher,
               Hpylori, Barretts, DysplasiaGrade, AtrophicGastritis,
               EoE, EosinophilCount, OtherFinding, EsoPredictRisk, TissueCypherRisk, Notes
        FROM tblPathology
        WHERE PatientID = ?
        ORDER BY PathologyDate DESC
        LIMIT ?
    """, (patient_id, limit))
    
    results = cur.fetchall()
    if not results:
        return None
    
    summary = ""
    for i, row in enumerate(results):
        (path_date, biopsy, wats3d, esopredict, tissuecypher, hpylori, barretts, 
         dysplasia_grade, gastritis, eoe, eos_count, other_finding, eso_risk, tc_risk, notes) = row
        
        if i > 0:
            summary += "<br/><br/>"
        
        summary += f"<b>{path_date}:</b><br/>"
        
        # Test types
        tests = []
        if biopsy: tests.append("Biopsy")
        if wats3d: tests.append("WATS3D")
        if esopredict: tests.append("EsoPredict")
        if tissuecypher: tests.append("TissueCypher")
        
        if tests:
            summary += f"&nbsp;&nbsp;Tests: {', '.join(tests)}<br/>"
        
        # Key findings
        findings = []
        if barretts:
            if dysplasia_grade:
                findings.append(f"<b>Barrett's with {dysplasia_grade}</b>")
            else:
                findings.append("<b>Barrett's esophagus</b>")
        
        if hpylori:
            findings.append("H. pylori positive")
        
        if eoe:
            if eos_count:
                findings.append(f"EoE ({eos_count} eos/hpf)")
            else:
                findings.append("EoE")
        
        if gastritis:
            findings.append("Atrophic gastritis")
        
        if other_finding:
            findings.append(other_finding)
        
        if findings:
            summary += f"&nbsp;&nbsp;Findings: {', '.join(findings)}<br/>"
        
        # Risk scores
        risk_scores = []
        if eso_risk:
            risk_scores.append(f"EsoPredict: {eso_risk}")
        if tc_risk:
            risk_scores.append(f"TissueCypher: {tc_risk}")
        
        if risk_scores:
            summary += f"&nbsp;&nbsp;Risk Assessment: {', '.join(risk_scores)}<br/>"
        
        if notes:
            summary += f"&nbsp;&nbsp;Notes: {notes}<br/>"
    
    return summary

def get_recent_diagnostics_summary(cur, patient_id, limit=2):
    """Get summary of recent diagnostic studies"""
    cur.execute("""
        SELECT TestDate, Surgeon, Endoscopy, EsophagitisGrade, HiatalHerniaSize, EndoscopyFindings,
               Bravo, pHImpedance, DeMeesterScore, pHFindings,
               EndoFLIP, EndoFLIPFindings, Manometry, ManometryFindings,
               GastricEmptying, PercentRetained4h, GastricEmptyingFindings,
               Imaging, ImagingFindings, UpperGI, UpperGIFindings, DiagnosticNotes
        FROM tblDiagnostics
        WHERE PatientID = ?
        ORDER BY TestDate DESC
        LIMIT ?
    """, (patient_id, limit))
    
    results = cur.fetchall()
    if not results:
        return None
    
    summary = ""
    for i, row in enumerate(results):
        if i > 0:
            summary += "<br/><br/>"
        
        test_date = row[0]
        surgeon = row[1]
        
        summary += f"<b>{test_date}</b>"
        if surgeon:
            summary += f" (Dr. {surgeon})"
        summary += ":<br/>"
        
        # Tests performed
        tests_done = []
        if row[2]:  # Endoscopy
            endo_details = []
            if row[3]:  # EsophagitisGrade
                endo_details.append(f"Grade {row[3]} esophagitis")
            if row[4]:  # HiatalHerniaSize
                endo_details.append(f"{row[4]} hiatal hernia")
            
            if endo_details:
                tests_done.append(f"EGD ({', '.join(endo_details)})")
            else:
                tests_done.append("EGD")
            
            if row[5]:  # EndoscopyFindings
                summary += f"&nbsp;&nbsp;Endoscopy: {row[5]}<br/>"
        
        if row[6] or row[7]:  # Bravo or pH Impedance
            ph_tests = []
            if row[6]: ph_tests.append("Bravo")
            if row[7]: ph_tests.append("pH Impedance")
            
            ph_details = []
            if row[8]:  # DeMeesterScore
                ph_details.append(f"DeMeester {row[8]}")
            
            if ph_details:
                tests_done.append(f"{'/'.join(ph_tests)} ({', '.join(ph_details)})")
            else:
                tests_done.append('/'.join(ph_tests))
            
            if row[9]:  # pHFindings
                summary += f"&nbsp;&nbsp;pH Study: {row[9]}<br/>"
        
        if row[10]:  # EndoFLIP
            tests_done.append("EndoFLIP")
            if row[11]:  # EndoFLIPFindings
                summary += f"&nbsp;&nbsp;EndoFLIP: {row[11]}<br/>"
        
        if row[12]:  # Manometry
            tests_done.append("Manometry")
            if row[13]:  # ManometryFindings
                summary += f"&nbsp;&nbsp;Manometry: {row[13]}<br/>"
        
        if row[14]:  # GastricEmptying
            ge_details = []
            if row[15]:  # PercentRetained4h
                ge_details.append(f"{row[15]}% retained at 4h")
            
            if ge_details:
                tests_done.append(f"Gastric Emptying ({', '.join(ge_details)})")
            else:
                tests_done.append("Gastric Emptying")
            
            if row[16]:  # GastricEmptyingFindings
                summary += f"&nbsp;&nbsp;Gastric Emptying: {row[16]}<br/>"
        
        if row[17]:  # Imaging
            tests_done.append("Imaging")
            if row[18]:  # ImagingFindings
                summary += f"&nbsp;&nbsp;Imaging: {row[18]}<br/>"
        
        if row[19]:  # UpperGI
            tests_done.append("Upper GI")
            if row[20]:  # UpperGIFindings
                summary += f"&nbsp;&nbsp;Upper GI: {row[20]}<br/>"
        
        if tests_done:
            summary += f"&nbsp;&nbsp;Studies: {', '.join(tests_done)}<br/>"
        
        if row[21]:  # DiagnosticNotes
            summary += f"&nbsp;&nbsp;Notes: {row[21]}<br/>"
    
    return summary

def get_surgical_history_summary(cur, patient_id):
    """Get comprehensive surgical history"""
    cur.execute("""
        SELECT SurgeryDate, SurgerySurgeon, Notes,
               HiatalHernia, ParaesophagealHernia, MeshUsed, GastricBypass, SleeveGastrectomy,
               Toupet, TIF, Nissen, Dor, HellerMyotomy, Stretta, Ablation, LINX,
               GPOEM, EPOEM, ZPOEM, Pyloroplasty, Revision, GastricStimulator, Dilation, Other
        FROM tblSurgicalHistory
        WHERE PatientID = ?
        ORDER BY SurgeryDate DESC
    """, (patient_id,))
    
    results = cur.fetchall()
    if not results:
        return None
    
    procedure_names = [
        "Hiatal Hernia Repair", "Paraesophageal Hernia Repair", "Mesh Used", "Gastric Bypass", "Sleeve Gastrectomy",
        "Toupet Fundoplication", "TIF", "Nissen Fundoplication", "Dor Fundoplication", "Heller Myotomy", 
        "Stretta", "Ablation", "LINX Device", "G-POEM", "E-POEM", "Z-POEM", "Pyloroplasty", 
        "Revision Surgery", "Gastric Stimulator", "Dilation", "Other Procedure"
    ]
    
    summary = ""
    for i, row in enumerate(results):
        if i > 0:
            summary += "<br/><br/>"
        
        surgery_date = row[0]
        surgeon = row[1]
        notes = row[2]
        procedures = row[3:]  # All the procedure flags
        
        summary += f"<b>{surgery_date}</b>"
        if surgeon:
            summary += f" (Dr. {surgeon})"
        summary += ":<br/>"
        
        # List procedures performed
        performed_procedures = []
        for j, performed in enumerate(procedures):
            if performed:
                performed_procedures.append(procedure_names[j])
        
        if performed_procedures:
            summary += f"&nbsp;&nbsp;Procedures: {', '.join(performed_procedures)}<br/>"
        
        if notes:
            summary += f"&nbsp;&nbsp;Notes: {notes}<br/>"
    
    return summary

def get_recall_summary(cur, patient_id):
    """Get current recall and follow-up status"""
    cur.execute("""
        SELECT RecallDate, RecallReason, Notes, Completed
        FROM tblRecall
        WHERE PatientID = ? AND Completed = 0
        ORDER BY RecallDate ASC
        LIMIT 3
    """, (patient_id,))
    
    results = cur.fetchall()
    if not results:
        return None
    
    summary = ""
    today = date.today()
    
    for i, (recall_date, reason, notes, completed) in enumerate(results):
        if i > 0:
            summary += "<br/>"
        
        try:
            recall_dt = datetime.strptime(recall_date, "%Y-%m-%d").date()
            days_diff = (recall_dt - today).days
            
            if days_diff < 0:
                urgency = f"<font color='red'>OVERDUE by {abs(days_diff)} days</font>"
            elif days_diff == 0:
                urgency = "<font color='red'>DUE TODAY</font>"
            elif days_diff <= 7:
                urgency = f"<font color='orange'>Due in {days_diff} days</font>"
            else:
                urgency = f"Due in {days_diff} days"
        except:
            urgency = "Date unclear"
        
        summary += f"<b>{reason}:</b> {recall_date} ({urgency})"
        if notes:
            summary += f" - {notes}"
    
    return summary


# Integration function for existing print_summary.py
def generate_pdf(patient_id):
    """Main function to generate surgeon-optimized summary"""
    return generate_surgeon_optimized_summary(patient_id)