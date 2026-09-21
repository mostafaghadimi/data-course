# data-course-page

صفحهٔ فرود (landing page) برای **دورهٔ رایگان مهندسی داده و هوش مصنوعی**.

یک صفحهٔ کاملاً مستقل و تک‌فایل (`index.html`) — بدون وابستگی و بدون مرحلهٔ build.
فرم ثبت‌نام به‌صورت native ساخته شده و مستقیم به یک Google Form ارسال می‌شود
(بدون iframe). راست‌به‌چپ، با فونت Vazirmatn، و پشتیبانی از حالت تیره.

A standalone, single-file landing page for a free Data Engineering / AI course.
No dependencies, no build step. The enrollment form is native HTML and posts
straight to a Google Form (no iframe). RTL, Vazirmatn, dark-mode aware.

## اجرا

کافی است `index.html` را در مرورگر باز کنید، یا با یک سرور استاتیک سرو کنید:

```bash
python3 -m http.server
```

## استقرار

روی GitHub Pages (شاخهٔ `main`، ریشهٔ مخزن) سرو می‌شود؛ فایل `.nojekyll`
جلوی پردازش Jekyll را می‌گیرد.
