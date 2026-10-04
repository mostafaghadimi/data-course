<div dir="rtl">

# اضافه‌کردن اسم خودت

اسم منتورها از `data/mentors.json` و اسم شرکت‌کننده‌ها از `data/participants.json` خونده می‌شه. برای اضافه‌شدن:

**۱.** فایل `data/participants.json` (یا برای منتورها `data/mentors.json`) رو ویرایش کن و یک آبجکت به آخر لیست اضافه کن:

```json
{
  "name": "اسم تو",
  "linkedin": "https://www.linkedin.com/in/username/",
  "avatar": "https://example.com/your-photo.jpg",
  "education": [
    "کارشناسی مهندسی کامپیوتر، دانشگاه ..."
  ],
  "experience": [
    "مهندس داده در شرکت ..."
  ]
}
```

- فقط `name` لازمه؛ بقیه اختیاری‌ان.
- برای `avatar` یک **لینکِ مستقیمِ عکس** بذار (مثلاً آواتار گیت‌هابت: `https://github.com/USERNAME.png`). اگه نذاری، حروف اول اسمت نشون داده می‌شه.
- `education` (سوابق تحصیلی) و `experience` (سوابق کاری) هرکدوم یک **لیست از خط‌ها**ن. اگه یکی‌شون رو بذاری، روی کارتت یک دکمهٔ سوابق ظاهر می‌شه که با کلیک، یک پنجره با همون دو بخش باز می‌کنه.

**۲.** یک Pull Request بزن. همین.

</div>
