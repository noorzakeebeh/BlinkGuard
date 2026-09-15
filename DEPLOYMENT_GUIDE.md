# 🚀 دليل تحويل BlinkGuard إلى تطبيق قابل للتنزيل ونشره على GitHub

هاد الدليل بيشرحلك خطوة بخطوة:
1. شو لازم تنزّلي على جهازك.
2. كيف تجربي التطبيق محليًا.
3. كيف تحوّليه لملف تنفيذي (`.exe` لويندوز، `.app` لماك، ملف تنفيذي للينكس) ينزّله أي شخص بدون ما يثبت Python.
4. كيف ترفعي المشروع على GitHub.
5. كيف تخلّي GitHub يبني النسخ الثلاث تلقائيًا وينشرها كـ Release جاهزة للتنزيل.

---

## 1️⃣ الأشياء يلي لازم تنزّليها على جهازك

| الأداة | ليش؟ | رابط التحميل |
|---|---|---|
| **Python 3.10 أو أحدث** | لتشغيل الكود وتجميعه | https://www.python.org/downloads/ |
| **Git** | لرفع المشروع على GitHub | https://git-scm.com/downloads |
| **حساب GitHub** | لاستضافة المشروع | https://github.com/join |
| **محرر أكواد (اختياري)** | زي VS Code | https://code.visualstudio.com/ |

> ⚠️ عند تثبيت Python على ويندوز، لازم تعلّمي على خيار **"Add Python to PATH"** بأول شاشة تثبيت.

تأكدي من التثبيت بفتح الطرفية (Terminal / cmd / PowerShell) وكتابة:
```bash
python --version
git --version
```
إذا ظهرلك رقم إصدار لكل وحدة، تمام، جاهزة تكملي.

---

## 2️⃣ تجهيز المشروع وتجربته محليًا

```bash
# ادخلي لمجلد المشروع (اللي فيه main.py و app/)
cd blinkguard

# أنشئي بيئة افتراضية (مستحسن، مو إجباري)
python -m venv venv

# فعّلي البيئة الافتراضية
# على ويندوز:
venv\Scripts\activate
# على ماك/لينكس:
source venv/bin/activate

# ثبّتي المكتبات
pip install -r requirements.txt

# شغّلي التطبيق
python main.py
```

إذا ظهرت نافذة BlinkGuard وطلعت شاشة الترحيب (Onboarding) — تمام، كل شي شغال. جرّبي تعطي صلاحية الكاميرا وتكملي المعايرة.

---

## 3️⃣ تحويله لتطبيق تنفيذي (Executable) ينزّل مباشرة

هون رح نستخدم مكتبة **PyInstaller** يلي بتحزم بايثون + كل المكتبات + الكود بملف واحد ما بيحتاج المستخدم يثبت شي.

### تثبيت PyInstaller
```bash
pip install pyinstaller
```

### بناء التطبيق
جهّزتلك ملف `packaging/blinkguard.spec` جاهز مسبقًا (موجود بالمشروع). بس نفّذي:

```bash
cd packaging
pyinstaller blinkguard.spec
```

بعد ما يخلص (بياخد كم دقيقة)، رح تلاقي التطبيق الجاهز هون:
- **ويندوز:** `packaging/dist/BlinkGuard/BlinkGuard.exe`
- **لينكس:** `packaging/dist/BlinkGuard/BlinkGuard`
- **ماك:** `packaging/dist/BlinkGuard.app`

> ⚠️ **مهم جدًا:** PyInstaller **ما بيقدر يبني لنظام تشغيل غير اللي شغال عليه**. يعني إذا بنيتي على ويندوز، بيطلعلك `.exe` بس — مش `.app` ولا ملف لينكس. لازم تبنيها من ماك عشان تطلعلك `.app`، ومن لينكس عشان يطلعلك نسخة لينكس.
>
> **الحل الأسهل:** استخدمي GitHub Actions (خطوة 5 تحت) يلي بيبني الثلاث نسخ تلقائيًا بدون ما تحتاجي أجهزة الثلاث أنظمة.

### إضافة أيقونة (اختياري)
حطّي ملفين بمجلد `packaging/`:
- `app_icon.ico` (لويندوز — استخدمي أي موقع تحويل PNG إلى ICO)
- `app_icon.icns` (لماك)

الـ spec file رح يستخدمهم تلقائيًا إذا كانوا موجودين، وإذا مش موجودين رح يبني بدون أيقونة (ما رح يفشل البناء).

### تحويله لملف تثبيت (Installer) حقيقي (اختياري متقدّم)
إذا بدك ملف `.exe` أو `.dmg` بيشتغل زي أي برنامج تنزّليه وتضغطي "Next Next Finish":

- **ويندوز:** استخدمي [Inno Setup](https://jrsoftware.org/isinfo.php) (مجاني) — بتاخدي مجلد `dist/BlinkGuard` وتسوّيلها Setup Wizard.
- **ماك:** استخدمي `create-dmg` أو `hdiutil` لتحويل `.app` لملف `.dmg`.
- **لينكس:** استخدمي [AppImage](https://appimage.org/) أو اعملي حزمة `.deb`.

هاي خطوة اختيارية — الملف التنفيذي العادي من PyInstaller شغّال ومكفي لمعظم الاستخدامات.

---

## 4️⃣ رفع المشروع على GitHub

### أ. إنشاء الـ Repository (إذا مو موجود بعد)
1. روحي لـ https://github.com/noorzakeebeh/BlinkGuard
2. إذا مو موجود، أنشئيه من https://github.com/new باسم `BlinkGuard`
3. **لا** تعلّمي على "Add README" أو "Add .gitignore" — عندك نسخك جاهزة محليًا.

### ب. رفع الملفات من جهازك
من داخل مجلد `blinkguard` (اللي فيه main.py):

```bash
git init
git add .
git commit -m "Initial commit: BlinkGuard desktop app"
git branch -M main
git remote add origin https://github.com/noorzakeebeh/BlinkGuard.git
git push -u origin main
```

> 💡 أول مرة بترفعي، جيت رح يطلب منك تسجيل دخول — استخدمي **Personal Access Token** بدل الباسورد العادي (GitHub وقفوا دعم الباسورد العادي). تقدري تسوّيه من:
> Settings → Developer settings → Personal access tokens → Generate new token (صلاحية `repo` كافية).

### ج. تأكدي إن مجلد `app/` كامل انرفع
افتحي صفحة الـ repo على GitHub وتأكدي إنك شايفة:
```
app/
  core/
  data/
  workers/
  ui/
main.py
requirements.txt
.gitignore
README.md
packaging/blinkguard.spec
.github/workflows/build.yml
```

---

## 5️⃣ البناء التلقائي للثلاث أنظمة + نشر Release (الطريقة الموصى فيها)

جهّزتلك ملف `.github/workflows/build.yml` جاهز بالمشروع. هاد بيخلّي GitHub نفسه يبني نسخة ويندوز وماك ولينكس تلقائيًا كل ما تعملي **tag** جديد، ويرفعهم كـ Release جاهز للتنزيل — بدون ما تحتاجي أجهزة الثلاث أنظمة.

### كيف تفعّليه
بعد ما ترفعي الكود (خطوة 4)، اعملي tag ونزّليه:

```bash
git tag v1.0.0
git push origin v1.0.0
```

### شو بيصير بعدين
1. روحي لتبويب **Actions** بصفحة الـ repo على GitHub، رح تشوفي البناء شغال (بياخد ٥-١٥ دقيقة للثلاث أنظمة).
2. لما يخلص، روحي لتبويب **Releases** (على يمين صفحة الـ repo الرئيسية).
3. رح تلاقي **Draft Release** فيها ثلاث ملفات مضغوطة:
   - `BlinkGuard-Windows.zip`
   - `BlinkGuard-macOS.zip`
   - `BlinkGuard-Linux.zip`
4. افتحيها، عدّلي وصف الإصدار إذا بدك، واضغطي **Publish release**.

### كيف بينزّل الناس التطبيق بعدين
أي حدا يزور صفحة `https://github.com/noorzakeebeh/BlinkGuard/releases` رح يشوف آخر إصدار وينزّل النسخة يلي تناسب جهازه (ويندوز/ماك/لينكس) بدون ما يحتاج يثبت Python أو أي مكتبة — كل شي محزوم جوا.

> 💡 لأي تحديث جديد بالمستقبل: عدّلي الكود → `git commit` و`git push` عادي → لما تكوني جاهزة لإصدار جديد اعملي tag جديد متل `v1.0.1` وادفعيه، وGitHub رح يبني وينشر تلقائيًا.

---

## ✅ ملخص سريع (Checklist)

- [ ] Python 3.10+ و Git متثبتين على جهازك
- [ ] `pip install -r requirements.txt` اشتغل بدون أخطاء
- [ ] `python main.py` بيفتح التطبيق محليًا
- [ ] `pyinstaller packaging/blinkguard.spec` بيبني نسخة تنفيذية محلية للاختبار
- [ ] المشروع كامل (مع مجلد `app/`) مرفوع على GitHub
- [ ] عملتي `git tag vX.X.X` و `git push origin vX.X.X`
- [ ] تبويب Actions خلّص البناء بنجاح (علامة ✅ خضراء)
- [ ] فتحتي الـ Draft Release ونشرتيها من تبويب Releases

بعد هاي الخطوات، أي شخص بيقدر يزور صفحة الـ Releases وينزّل BlinkGuard مباشرة لجهازه.
