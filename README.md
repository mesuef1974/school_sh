# 🦅 SULTAN HAGRY | سلطان هجري
>
> **AI-Powered Data Management & Analysis Platform**
> **منصة متكاملة لإدارة وتحليل البيانات مدعومة بالذكاء الاصطناعي**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-AI-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.0-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

---

## 📖 Overview | نظرة عامة

**SULTAN HAGRY** is a sophisticated data management system designed to streamline complex workflows through intelligent automation. Leveraging a powerful combination of Django for its core engine and PyTorch for advanced analytics, it provides a high-performance environment for data-driven decision-making.

**سلطان هجري** هو نظام متطور لإدارة البيانات مصمم لتبسيط سير العمل المعقد من خلال الأتمتة الذكية. يعتمد النظام على مزيج قوي بين Django كمحرك أساسي وPyTorch للتحليلات المتقدمة، مما يوفر بيئة عالية الأداء لاتخاذ القرارات المبنية على البيانات.

---

## ✨ Key Features | المميزات الرئيسية

### 🤖 AI-Driven Insights | رؤى مدعومة بالذكاء الاصطناعي

- Automated analysis and pattern recognition using **PyTorch**.
- Intelligent reporting and predictive modeling.

### 📊 Comprehensive Data Management | إدارة شاملة للبيانات

- Seamless data processing with **Pandas** and **NumPy**.
- Robust CSV/Excel import/export capabilities.

### 🎨 Modern & Responsive UI | واجهة مستخدم حديثة وتفاعلية

- Built with **Tailwind CSS** for a premium, mobile-responsive experience.
- Dark mode support and smooth micro-interactions.

### 🧠 Event & Memory System | نظام الأحداث والذاكرة

- Advanced tracking of system activities and data versions.
- Context-aware data archiving and retrieval.

---

## 🛠️ Technology Stack | التقنيات المستخدمة

- **Backend:** Python 3.10+, Django 4.2+
- **AI/ML:** PyTorch, NumPy, SciPy
- **Data:** Pandas, PostgreSQL (or SQLite for local dev)
- **Frontend:** HTML5, Vanilla JS, Tailwind CSS
- **Containerization:** Docker & Docker Compose

---

## 🚀 Getting Started | بدأت العمل

### Prerequisites | المتطلبات الأساسية

- Python 3.10+
- Virtualenv
- Git

### Installation | خطوات التثبيت

1. **Clone the repository | استنساخ المستودع**

   ```bash
   git clone https://github.com/mesuef1974/SULTAN_HAGRY.git
   cd SULTAN_HAGRY
   ```

2. **Setup Virtual Environment | إعداد البيئة الافتراضية**

   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On Linux/Mac
   ```

3. **Install Dependencies | تثبيت المكتبات**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations | تنفيذ التهجير**

   ```bash
   python manage.py migrate
   ```

5. **Start Dev Server | تشغيل الخادم**

   ```bash
   python manage.py runserver
   ```

---

## 🛡️ License | الترخيص

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🧑‍💻 Author | المطور

**Mesuef** - [GitHub Profile](https://github.com/mesuef1974)

---
*Made with ❤️ for high-performance data systems.*

# منصة الشحانية — Django + HTMX (Bootstrap)

هذه حزمة انطلاق سريعة لنسخة **Django + HTMX** مشتقة من وضعك الحالي.

## تشغيل سريع (تطوير)

```bash
yes | cp docker/docker-compose.yml ./docker-compose.yml
docker compose up -d --build
# افتح: http://localhost:8000 — الخطة التشغيلية (HTMX)
# Flower: http://localhost:5555
# Adminer: http://localhost:8080
```

## ملاحظات

- نموذج **OperationalPlanItem** مُستمد من مخطط بياناتك (03_Database_Schema). الحقول قابلة للزيادة وفق الحاجة.
- أولوية الواجهات: **الخطة التشغيلية + الصلاحيات + إدارة المستخدمين**.
- مصدر المهاجرات: **Django** من الآن — ابدأ بـ `makemigrations` ثم `migrate --fake-initial` إن لزم.
- سياسة **RLS** ينبغي تفعيلها في PostgreSQL وتمرير `app.allowed_classes` عبر
  `coredata.middleware.RlsContext`.

*تاريخ التوليد:* 2026-02-01T16:38:00
