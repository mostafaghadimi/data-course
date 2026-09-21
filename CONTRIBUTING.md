# اضافه‌کردن اسم خودت

اسم شرکت‌کننده‌ها و منتورها از `data/people.json` خونده می‌شه. برای اضافه‌شدن:

۱. `data/people.json` رو ویرایش کن و یک آبجکت به `participants` (یا `mentors`) اضافه کن:

```json
{
  "name": "اسم تو",
  "linkedin": "https://www.linkedin.com/in/username/",
  "avatar": "https://example.com/your-photo.jpg"
}
```

- فقط `name` لازمه؛ `linkedin` و `avatar` اختیاری‌ان.
- برای `avatar` یک **لینکِ مستقیمِ عکس** بذار (مثلاً آواتار گیت‌هابت: `https://github.com/USERNAME.png`).
- اگه `avatar` نذاری، حروف اول اسمت نشون داده می‌شه.

۲. یک Pull Request بزن. همین.
