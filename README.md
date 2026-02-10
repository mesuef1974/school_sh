
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
