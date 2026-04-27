# PAT Recorder — Portable Appliance Testing System

A lightweight, technician‑friendly web application for recording, managing, and exporting Portable Appliance Testing (PAT) results in compliance with **AS/NZS 3760**, **AS/NZS 5761**, and **AS/NZS 5762**.

Built with **Flask**, **Bootstrap 5**, **WeasyPrint**, and **DataTables**, the system provides a clean workflow for technicians performing electrical safety testing on appliances.

---

## Features

### 🔌 Modern, Branded Interface
- Streamlined navigation:
  - Dashboard  
  - Appliances  
  - Add Appliance  

---

## 🧰 Appliance Management
- Add, edit, and view appliances
- Appliance fields:
  - Asset Number  
  - Description  
  - **Make / Model**  
  - Location  
  - Owner  
  - Class Type / Supply Type  
- Appliance detail page includes:
  - Full test history  
  - Full repair history  
  - Quick actions (Add Test, Add Repair, View PDFs)
- Soft-delete (dispose/restore) and hard-delete support
- Disposed appliances and their records are hidden from normal views

---

## 🧪 Test Recording
Supports all major Australian/New Zealand PAT standards:

- **AS/NZS 3760** — In‑service safety inspection & testing  
- **AS/NZS 5761** — Repaired electrical equipment  
- **AS/NZS 5762** — Re‑testing of repaired equipment  

Includes:
- Visual inspection checklist  
- Electrical test results  
- PASS / FAIL logic  
- Technician dropdown (from database)  
- Auto‑calculated next test due date  
- QR code linking back to the test record

---

## 🔧 Repair Logging
Log ad‑hoc repair events against any appliance, independently of formal test records.

Repair records include:
- Repair date  
- Repaired by (free text — supports external contractors)  
- Description of work performed  
- Extended comments (multi‑line)  
- Photo attachments  

### Locking behaviour
When a new test is recorded for an appliance, all preceding open repair records are automatically **locked** with the test date. Locked records are read‑only and cannot be edited or deleted, preserving a tamper‑evident maintenance history.

### Dashboard integration
The dashboard flags appliances as **"Repaired – test required"** whenever a repair has been logged more recently than the appliance's last test, prompting a post‑repair compliance test.

---

## 📄 PDF Generation
Each test record can be exported as a **professional PDF**, including:

- Appliance details  
- Test results  
- PASS/FAIL summary  
- Technician details  
- Timestamp  
- **Embedded QR code** linking to the online record  
- Clean layout optimised for A4 printing  

A separate **Repair History PDF** is available per appliance, listing all repair records chronologically with lock status.

Powered by **WeasyPrint**.

---

## 📱 QR Code Integration
Every PDF includes a QR code that links directly to the test record.

QR codes are generated using:
- `qrcode` Python library  
- Base64‑embedded PNG images  
- No temporary files required  

---

## 📊 Appliance List Enhancements
The appliance list now includes:

### ✔ DataTables Sorting
Sort by:
- Asset  
- Description  
- Make/Model  
- Location  
- Owner  

### ✔ Global Search
Instant search across all columns.

### ✔ Column Filters
- Text filters for:
  - Asset  
  - Description  
  - Make/Model  
- Dropdown filters for:
  - Location  
  - Owner  

### ✔ Responsive Layout
Action buttons remain aligned and consistent:
- **View**
- **Add Test**
- **Add Repair**

---

## Technology Stack

### Backend
- Python 3.x  
- Flask  
- SQLAlchemy  
- WeasyPrint  
- qrcode  

### Frontend
- Bootstrap 5  
- jQuery  
- DataTables 1.13.x  
- Material Design Icons  

---

## 📁 Project Structure
`test_and_tag/
├── app.py
├── config.py
├── models.py
├── utils.py
├── views.py
├── requirements.txt
│
├── sql/
│   ├── create_database.sql
│   ├── create_tables.sql
│   └── insert_default_retest_rules.sql
│
├── static/
│   ├── css/custom.css
│   ├── uploads/tests/
│   └── uploads/repairs/
│
└── templates/
├── base.html
├── dashboard.html
├── appliance_list.html
├── appliance_detail.html
├── appliance_due.html
├── search_results.html
├── test_form.html
├── test_detail.html
├── repair_form.html
├── repair_detail.html
│
└── pdf/
├── test_3760.html
├── test_5761.html
├── test_5762.html
└── repair_history.html`

---

## 🛠 Installation

See **INSTALL.txt** for full installation instructions.

---

## 🔧 Note

AI (Claude) used in the generation of this code

