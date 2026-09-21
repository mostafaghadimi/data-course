# اضافه‌کردن اسم خودت

اسم شرکت‌کننده‌ها و منتورها از `data/people.json` خونده می‌شه. برای اضافه‌شدن:

۱. `data/people.json` رو ویرایش کن و یک آبجکت به `participants` (یا `mentors`) اضافه کن:

```json
{
  "name": "اسم تو",
  "linkedin": "https://www.linkedin.com/in/username/",
  "avatar": "assets/your-photo.jpg"
}
```

- فقط `name` لازمه؛ `linkedin` و `avatar` اختیاری‌ان.
- اگه `avatar` نذاری، حروف اول اسمت نشون داده می‌شه.
- برای عکس، یا لینک مستقیم بده یا فایل رو توی پوشهٔ `assets/` بذار و مسیرش رو بنویس.

۲. یک Pull Request بزن. همین.
