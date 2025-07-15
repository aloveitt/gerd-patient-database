from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
import sqlite3
import os

def generate_pdf(patient_id):
    conn = sqlite3.connect("gerd_center.db")
    cur = conn.cursor()

    cur.execute("SELECT FirstName, LastName, MRN, DOB FROM tblPatients WHERE PatientID = ?", (patient_id,))
    row = cur.fetchone()
    if not row:
        return

    first, last, mrn, dob = row
    filename = f"{last}_{first}_summary.pdf"
    c = canvas.Canvas(filename, pagesize=landscape(letter))
    width, height = landscape(letter)
    y = height - 40

    def header(text, size=14):
        nonlocal y
        c.setFont("Helvetica-Bold", size)
        c.drawString(40, y, text)
        y -= 16

    def body(text):
        nonlocal y
        c.setFont("Helvetica", 9)
        c.drawString(50, y, text)
        y -= 10
        if y < 60:
            c.showPage()
            y = height - 40

    def separator():
        nonlocal y
        y -= 4
        c.line(40, y, width - 40, y)
        y -= 10

    header(f"Patient Summary: {last}, {first}")
    body(f"MRN: {mrn}    DOB: {dob}")
    separator()

    # Diagnostics
    header("Diagnostics")
    cur.execute("""
        SELECT TestDate, Surgeon, Endoscopy, EsophagitisGrade, HiatalHerniaSize, EndoscopyFindings,
               Bravo, pHImpedance, DeMeesterScore, pHFindings,
               EndoFLIP, EndoFLIPFindings,
               Manometry, ManometryFindings,
               GastricEmptying, PercentRetained4h, GastricEmptyingFindings,
               Imaging, ImagingFindings,
               UpperGI, UpperGIFindings, DiagnosticNotes
        FROM tblDiagnostics
        WHERE PatientID = ?
        ORDER BY TestDate DESC
    """, (patient_id,))
    for row in cur.fetchall():
        if any(row[2:]):
            body(f"Date: {row[0]}")
            if row[1]: body(f"  Surgeon: {row[1]}")
            if row[2]: body("  - Endoscopy")
            if row[3]: body(f"    Esophagitis Grade: {row[3]}")
            if row[4]: body(f"    Hiatal Hernia Size: {row[4]}")
            if row[5]: body(f"    Endoscopy Findings: {row[5]}")
            if row[6]: body("  - Bravo")
            if row[7]: body("  - pH Impedance")
            if row[8]: body(f"    DeMeester Score: {row[8]}")
            if row[9]: body(f"    pH Findings: {row[9]}")
            if row[10]: body("  - EndoFLIP")
            if row[11]: body(f"    EndoFLIP Findings: {row[11]}")
            if row[12]: body("  - Manometry")
            if row[13]: body(f"    Manometry Findings: {row[13]}")
            if row[14]: body("  - Gastric Emptying")
            if row[15]: body(f"    % Retained @ 4h: {row[15]}")
            if row[16]: body(f"    Gastric Emptying Findings: {row[16]}")
            if row[17]: body("  - Imaging")
            if row[18]: body(f"    Imaging Findings: {row[18]}")
            if row[19]: body("  - Upper GI")
            if row[20]: body(f"    Upper GI Findings: {row[20]}")
            if row[21]: body(f"    Notes: {row[21]}")
            separator()

    # Surgery
    header("Surgical History")
    cur.execute("""
        SELECT SurgeryDate, SurgerySurgeon, Notes,
               HiatalHernia, Toupet, LINX, ParaesophagealHernia, MeshUsed,
               GastricBypass, SleeveGastrectomy, TIF, Nissen, Dor, HellerMyotomy,
               Stretta, Ablation, GPOEM, EPOEM, ZPOEM, Pyloroplasty,
               Revision, GastricStimulator, Dilation, Other
        FROM tblSurgicalHistory
        WHERE PatientID = ?
        ORDER BY SurgeryDate DESC
    """, (patient_id,))
    labels = [
        "Hiatal Hernia", "Toupet", "LINX", "Paraesophageal Hernia", "Mesh Used",
        "Gastric Bypass", "Sleeve Gastrectomy", "TIF", "Nissen", "Dor", "Heller Myotomy",
        "Stretta", "Ablation", "G-POEM", "E-POEM", "Z-POEM", "Pyloroplasty",
        "Revision", "Gastric Stimulator", "Dilation", "Other"
    ]
    for row in cur.fetchall():
        body(f"Date: {row[0]}")
        if row[1]: body(f"  Surgeon: {row[1]}")
        active = [labels[i] for i, val in enumerate(row[3:]) if val]
        if active: body("  Procedures: " + ", ".join(active))
        if row[2]: body(f"  Notes: {row[2]}")
        separator()

    # Pathology
    header("Pathology")
    cur.execute("""
        SELECT PathologyDate, Biopsy, WATS3D, EsoPredict, TissueCypher,
               Hpylori, Barretts, DysplasiaGrade, AtrophicGastritis,
               EoE, EosinophilCount, OtherFinding, EsoPredictRisk, TissueCypherRisk, Notes
        FROM tblPathology
        WHERE PatientID = ?
        ORDER BY PathologyDate DESC
    """, (patient_id,))
    for row in cur.fetchall():
        body(f"Date: {row[0]}")
        tests = []
        if row[1]: tests.append("Biopsy")
        if row[2]: tests.append("WATS3D")
        if row[3]: tests.append("EsoPredict")
        if row[4]: tests.append("TissueCypher")
        if tests: body("  Tests: " + ", ".join(tests))
        if row[5]: body("  - H. pylori")
        if row[6]: body("  - Barrett's")
        if row[7]: body(f"    Dysplasia: {row[7]}")
        if row[8]: body("  - Atrophic Gastritis")
        if row[9]: body("  - EoE")
        if row[10]: body(f"    Eosinophil Count: {row[10]}")
        if row[11]: body(f"    Other Findings: {row[11]}")
        if row[12]: body(f"    EsoPredict Risk: {row[12]}")
        if row[13]: body(f"    TissueCypher Risk: {row[13]}")
        if row[14]: body(f"    Notes: {row[14]}")
        separator()

    # Recalls
    header("Recalls")
    cur.execute("SELECT RecallDate, RecallReason, Notes, Completed FROM tblRecall WHERE PatientID = ? ORDER BY RecallDate DESC", (patient_id,))
    for row in cur.fetchall():
        body(f"Date: {row[0]}")
        if row[1]: body(f"  Reason: {row[1]}")
        if row[2]: body(f"  Notes: {row[2]}")
        if row[3]: body("  Completed")
        separator()

    c.save()
    os.startfile(filename)
