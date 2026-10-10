# Ders Görevleri

Ders Görevleri, YKS hazırlığı için derslere göre görev, tarih, öncelik ve
Windows hatırlatıcıları sunan yerel bir masaüstü uygulamasıdır.

İndirme ve güncel yayın bilgileri: <https://yks-dostu.pages.dev/>.

## Gizlilik

Uygulama hesap ve görev verilerini Windows kullanıcısının yerel uygulama verileri
klasöründe saklar. Bu sürüm çevrimiçi hesap eşitlemesi, ödeme, analiz veya
telemetri içermez. Görev veritabanları şifrelenmez; gizlilik ayrıntıları için
[gizlilik sayfasına](site/privacy.html) bakın.

## Geliştirme

Windows 10/11 x64, Python 3.14 ve `requirements.txt` içindeki paketler gerekir.

```powershell
py -3.14 -m pip install -r requirements.txt
py -3.14 app.py
```

Kurulum dosyasını kaynak koddan üretmek için Python bağımlılıklarına ek olarak
PyInstaller ve Inno Setup 6 kurun:

```powershell
py -3.14 -m pip install -r requirements-build.txt
.\build_setup.ps1
```

Kurulum dosyası `site\downloads\Ders-Gorevleri-Setup.exe` konumuna üretilir.
Üretilen dosya imzalanmamıştır. Kod imzalama ancak SignPath Foundation
başvurusunun kabul edilmesi ve her sürümün ayrıca onaylanması halinde mümkün
olabilir; kabul veya SmartScreen itibarının anında oluşacağı garanti edilmez.

## Yayınlama ve imzalama

Proje MIT lisansı altında yayımlanır. SignPath Foundation’ın açık kaynak
imzalama koşulları için başvurudan önce projenin güncel politika ve
uygunluk koşullarını inceleyin. Başvuru kabul edilmeden ve imza politikası
oluşturulmadan imzalı sürüm yayımlanmış sayılmaz.

## Lisans

Bu depodaki proje kaynak kodu MIT lisansı altındadır. Bağımlılıklar kendi
lisanslarına tabidir.
