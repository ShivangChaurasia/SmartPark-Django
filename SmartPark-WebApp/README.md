# SmartPark – Cost-Effective Smart Parking System
## Built with Python & Django (INT253 Curriculum Aligned)

SmartPark is a full-featured, smart mobility management and parking reservation platform built natively in **Python & Django**. It connects vehicle drivers seeking convenient parking with hosts who monetize unused residential or commercial space.

---

### 📚 Syllabus Mapping: INT253 Web Development in Python using Django

| Unit | Syllabus Topics | Implemented Django Components in SmartPark |
| :--- | :--- | :--- |
| **Unit I** | Django installation, project/app structure, `manage.py` commands | Modular app architecture (`accounts`, `parking`, `bookings`, `core`), custom management commands (`seed_demo_data`), unified project configuration in [`smartpark/settings.py`](file:///c:/Users/ACER/Desktop/Repos/SmartPark-Django/smartpark/settings.py) |
| **Unit II** | Views, URL dispatcher, HTTP request/response methods, error handling | Dynamic URL routing (`urls.py`), parameterized endpoints (`<int:pk>`), GET/POST dispatch, JSON REST APIs (`JsonResponse`) |
| **Unit III** | Templates (DTL), inheritance, variables, tags/filters, unit testing | Django templates with `{% extends 'base.html' %}`, `{% block %}`, `{% if %}`, `{% for %}`, `TestCase` in `tests.py` |
| **Unit IV** | Forms, validation, CSRF security, Post/Redirect/Get pattern | Django Forms (`UserRegistrationForm`, `UserLoginForm`, `HostKYCForm`, `ParkingLotForm`, `ProfileUpdateForm`), `{% csrf_token %}` |
| **Unit V** | Models, Migrations, ORM, ForeignKeys, Django Admin | Models with `ForeignKey`, `OneToOneField`, SQLite DB setup, customized `admin.ModelAdmin` with list filters and bulk actions |
| **Unit VI** | Cookies, Sessions, Users, Login/Logout, Authentication | Custom `User` model extending `AbstractUser`, `@login_required` decorators, session authentication, role toggling |

---

### 🚀 Key Functional Modules

1. **User & Driver Module:**
   - Geolocation search using the Haversine spherical distance formula ($\le 10\text{ km}$ radius) or PIN code.
   - Interactive vehicle slot selection grid for Cars, Bikes, and Buses with real-time collision detection.
   - Razorpay payment gateway integration with HMAC SHA256 signature verification & manual walk-in QR fallback.
   - Live dashboard with real-time countdown timers, session extension, and automated cancellation with tiered refunds ($100\%$, $50\%$, or $0\%$).
   - PDF Ticket & Receipt generation (`reportlab` + `qrcode`) with embedded scannable gate passes.

2. **Host / Owner Module:**
   - KYC onboarding with Aadhaar, phone, and property photo verification.
   - Property listing management with automated slot grid generation.
   - Safe closure protection: checks dependent active reservations before allowing facility deactivation.
   - Gate Scanner & Check-in Verification: validates 10-character booking codes and marks attended status.
   - Weekly revenue analytics chart (Chart.js) with daily earnings breakdown.

3. **Admin Module:**
   - Centralized Django Admin (`/admin/`) with custom filters, search fields, and bulk KYC approval actions.

---

### 🛠️ Quick Start & Setup

#### 1. Activate Environment & Install Dependencies
```bash
# Windows
.\venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 3. Seed Demo Dataset (Users, Parking Lots, Sample Bookings)
```bash
python manage.py seed_demo_data
```

#### 4. Run Unit Tests (INT253 Unit III)
```bash
python manage.py test
```

#### 5. Launch Development Server
```bash
python manage.py runserver
```
Visit: **`http://127.0.0.1:8000/`**

---

### 🔑 Demo Accounts

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Superuser / Admin** | `admin` | `admin123` | Django Admin at `/admin/` |
| **Parking Host** | `host_demo` | `host123` | Access `/owner/dashboard/` & facility controls |
| **Vehicle Driver** | `driver_demo` | `driver123` | Access `/dashboard/` & book parking slots |
