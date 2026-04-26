# PAT Recorder — Portable Appliance Testing System

A lightweight, technician‑friendly web application for recording, managing, and exporting Portable Appliance Testing (PAT) results in compliance with **AS/NZS 3760**, **AS/NZS 5761**, and **AS/NZS 5762**.

Built with **Flask**, **Bootstrap 5**, **WeasyPrint**, and **DataTables**, the system provides a clean workflow for technicians performing electrical safety testing on appliances.

---

## Features

### 🔌 Modern, Branded Interface
- Application renamed to **PAT Recorder**
- MDI **power‑plug icon** added to the navbar
- Streamlined navigation:
  - Dashboard  
  - Appliances  
  - Add Appliance  
- *Testers* menu removed (tester selection now handled internally)

---

## 🧰 Appliance Management
- Add, edit, and view appliances
- Appliance fields:
  - Asset Number  
  - Description  
  - **Make / Model**  
  - Location  
  - Owner  
  - Notes  
- Appliance detail page includes:
  - Full test history  
  - Quick actions (Add Test, View PDF)

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

## 📄 PDF Generation
Each test record can be exported as a **professional PDF**, including:

- Appliance details  
- Test results  
- PASS/FAIL summary  
- Technician details  
- Timestamp  
- **Embedded QR code** linking to the online record  
- Clean layout optimised for A4 printing  

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
test_and_tag/
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
│   └── uploads/tests/
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
│
└── pdf/
├── test_3760.html
├── test_5761.html
└── test_5762.html

---

## 🛠 Installation

See **INSTALL.md** for full installation instructions.

---

## 🔧 Note

AI (Copilot) used in the generation of this code

