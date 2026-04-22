# Test & Tag System (MVP)
A lightweight, technician‑friendly web application for managing electrical appliance testing under:

- **AS/NZS 3760** — In‑service safety inspection & testing  
- **AS/NZS 5761** — Second‑hand appliance safety testing  
- **AS/NZS 5762** — Repaired appliance safety testing  

This MVP provides a clean workflow for recording tests, generating certificates, tracking retest intervals, and managing appliances.

---

## 🚀 Features

### ✔ Appliance Management
- Add and view appliances  
- Track class type, supply type, location, owner  
- View complete test history  
- Photo gallery aggregated from all tests  

### ✔ Test Entry (Multi‑Standard)
Supports three standards:

| Standard | Purpose |
|---------|---------|
| **AS/NZS 3760** | In‑service testing (default) |
| **AS/NZS 5761** | Second‑hand appliance testing |
| **AS/NZS 5762** | Repaired appliance testing |

Each standard automatically reveals the correct additional fields.

### ✔ Retest Interval Rules (Database‑Driven)
- Retest intervals stored in a **retest_rules** table  
- Auto‑suggested interval based on **appliance class + supply type**  
- Fully editable without code changes  

### ✔ Fuzzy Search
Search appliances and test tags with typo‑tolerant matching.

Examples:
- `ketle` → *kettle*  
- `A12` → *A12345*  
- `tg24` → *TAG‑2024‑001*  

### ✔ Upcoming Test Reminders
A dedicated page showing appliances due for testing in the next 30 days.

### ✔ PDF Export (with QR Codes)
Generates standard‑specific certificates:

- **AS/NZS 3760 Test Report**
- **AS/NZS 5761 Second‑Hand Appliance Certificate**
- **AS/NZS 5762 Repair Certificate**

Each PDF includes:
- Appliance details  
- Test results  
- Standard‑specific fields  
- A **QR code** linking back to the test record  

### ✔ Photo Uploads
Technicians can attach multiple photos to each test.

---

## 📁 Project Structure

