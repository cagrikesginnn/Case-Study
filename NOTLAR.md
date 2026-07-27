# Notlar

Bu dosyada case boyunca ne bulduğumu, neye karar verdiğimi kendi kelimelerimle yazıyorum.

---

## Task 1 — Veri biraz bozuktu
Not: CSV'yi performans pazarlamacı bir tanıdığımdan aldım. Bu sebeple excell formatından kaynaklı çok sorun yaşadım.

Dosyayı ilk yaptığımda “normal csv” sandım. Yani virgülle ayrılmış satırlar. Ama satırlara bakınca her şey noktalı virgülle ayrılmıştı.. Muhtemelen Excel’den kaydederken Avrupa ayarıyla `;` kaydeddilmiş. Python’ın normal csv okuyucusu virgül bekliyor, o yüzden ilk denemede bütün satır tek kolon gibi geldi, hiçbir şey düzgün parse olmadı. 

**Nasıl düzelttim:** Dosyayı okurken delimiter=";" verdim. Bir de dosyanın en başında görünmeyen bir karakter vardı (BOM diye geçiyor), kolon adı garip görünüyordu. Onu da encoding="utf-8-sig" ile açınca düzeldi(chatgpt yardım aldım burada). Bunlar ingest_csv.py içerisinde.

Tarihler de 2026-07-01 gibi değil, 1.07.2026 gibi. İlk başta tarih parse patladı. parse_date diye küçük bir fonksiyon yazdım(chatgpt yardımıyla), önce gün.ay.yıl deniyor, olmazsa normal formatı deniyor. 

Brief’te kolon adı channel diyordu, dosyada channel_name yazıyor. Kanallar da google_ads değil, Google Ads, Meta Ads, Tiktok Ads diye geliyor. Ben bunları içeride google_ads, meta, tiktok diye kısalttım ki API’de hep aynı isim olsun. CHANNEL_MAP diye bir sözlük var utils.py içinde.

En kritik şey: aynı campaign_id (örneğin 1) hem Google’da hem Meta’da hem TikTok’ta var. İlk başta id 1 tek kampanyadır sandım. Sonra aynı güne bakınca 3 farklı satır, 3 farklı harcama gördüm. Yani id tek başına yetmiyor. O yüzden kampanyayı (kanal + id) ile unique yaptım. Yoksa veriler birbirinin üstüne binerdi.

İsimlerde başta/sonda boşluk olabilir diye .strip() koydum. Excele güvenmediğim için bunu yaptım.


Veriyi iki tabloya ayırdım:
- Campaign → kampanya kimliği, adı, kanalı
- DailyMetric → o kampanyanın günlük sayıları

Aynı günü iki kere yüklememek için (kampanya, tarih) unique. update_or_create kullanıyorum; komutu iki kez çalıştırınca satır artmıyor, varsa güncelliyor.

---

## Task 2 — API’yi nasıl koydum

Brief’teki isimleri kullandım:
- `/api/campaigns/` = kampanya listesi
- `/api/metrics/` = günlük satırlar (kanal, kampanya, tarih filtresi var)
- `/api/metrics/summary/` = özet

Summary’de group_by ile channel / campaign / date seçiliyor. Toplama işini DB’de `Sum` ile yaptım, sonra CTR, CVR, CPC, CPA, ROAS’ı hesapladım.

---

## Task 3 — “Haziran sayıları tutmuyor”

**Not / varsayım:** Brief’te örnek soru Haziran üzerinden. Ama bana gelen `ad_performance.csv` Temmuz 2026 verisi. Yani arkadaşım Haziran toplamı isteyince API doğal olarak boş dönüyor. Bu bir bug değil — dosyada o ay yok. Task 3’ü buna göre doğruladım.

Ne yaptım adım adım:

1. Testte bilinen küçük bir veri koydum (2 gün). Elle topladım: mesela impressions 2000, clicks 200, spend 100, revenue 400 : ROAS = 400/100 = 4 API de aynı sayıyı verdiyse aggregator doğru demektir.
2. Sıfıra bölme: gerçek CSV’de 0’lı satır yok. Ama Haziran gibi hiç satır olmayan bir filtrede tüm toplamlar 0 oluyor. O zaman CTR/CPC/ROAS için null dönüyorum. 
3. Aynı CSV’yi ikinci kez yükledim. Satır sayısı aynı kaldı. Yani çift kayıt yok.

---

## AI & Decision Log

**Ne kullandım:** Cursor (Composer) ve Chatgpt. Özellikle dosyayı anlamak, Django iskeleti kurmak ve test yazarken yardım aldım. Projedeki metrikler ne anlama geliyor diye Chatgpt ve Gemini'den faydalandım. Çünkü metriklerin ne anlama geldiğini anlamam gerekiyordu. 

**Kullandığım 3 prompt (aynısı):**
1. ad_performance.csv dosyasını incele: delimiter, tarih formatı, kanal isimleri, duplicate key var mı?
2. Django ile Campaign ve DailyMetric modelleri yaz, CSV'yi update_or_create ile yükle
3. summary endpoint'inde Sum sonrası CTR (clicks/impressions), ROAS(revenue / spend) hesapla, bölen 0 ise null dön, buna test yaz
4. 1.000.000 satır olsaydı api cevap dönerken zorlanabilirdi? pagination burada uygulanabilir miydi? DB'deki x tarih öncesindeki data güncellenmez. X tarih öncesindeki datayı cache alabilir miyiz?
5. Ekstra olarak şunu yapar mısın bende mistral api key var.
bir tane sayfa yap. ben o sayfaya en fazla para harcanan gün dediğimde, en fazla spend kampanya dediğimde en fazla conversion hangi gün dediğim de gibi bir çok soru yazdığımda mistral bana sql üretsin ve bunu otomatik db'ye sorgu atıp sonuç dönsün. Bunu bir sayfa olarak yapar mısın? 
Özetle önce yazdığım soruyu alacak. Benim database'me göre sql üretecek bu sql'i gidip db'ye atacak ve sonuç dönecek. (Kesinlikle mistral'e bizim sonuçlarımızı gönderme, mistral sadece db yapımı bilerek sql üretsin bana.)

**NOT**: 5. promt için son kullanıcı api vs anlamakta zorluk çekebilir. Bunu nasıl gösterebilirim son kullanıcıya düşünürken aklıma chatbot tarzı bir şey geldi. Mistral adında bir ai buldum. Ciddi bir ücretsiz kullanım hakkı vardı onun üzerinden bir chat sayfası oluşturdum. burada dikkat etmeye çalıştığım datanın kesinlike mistral'e gitmemesi. Mistral sadece db şemamı bilip buna göre sorgu üretmesi yönündeydi.

**AI’nın yanıldığı yer:** Kampanya id’sini tek başına unique yazdı. Ben dosyaya bakınca aynı id’nin 3 kanalda da olduğunu gördüm, onu düzelttim. || AI mistral api kısmında da ciddi sorun yaşadı.

**AI’ya bırakmadığım şey:** Sıfıra bölünce null dönsün kararı. Bunu kendim seçtim; “0 mı null mı” AI’ya bırakılacak bir şey değil bence, sonra karışır.

**Ne kadar sürdü:** Yaklaşık 1–1.5 gün.

---

## Stretch (Module I)

Ekstra olarak ;
/api/insights/top-campaigns/ ekledim. ROAS’a göre sıralıyor.
chatbot oluşturdum. /api/ask-page/ soru sorarak cevap dönebiliyor.

Temmuz’a bakınca:
- En iyi duran: Google Ads / campaign_1 (ROAS ~12.7)
- Meta'da en iyi: campaign_3 (~9.8)
- En zayıf gibi duran: TikTok / campaign_2 (~6.7) hem de en çok para harcananlardan

ROAS’lar baya yüksek. Önce sorarım: revenue ile spend aynı yerden / aynı para biriminden mi geliyor? Belki revenue yüksek raporlanıyordur. Spend dolar, revenue tl olabilir. Bu durumda cost currency ve revenue currency gerekiyor. Böyle bir durumla karşılaşsaydım o günün güncel kurunu bir yerden crawl edip iki değeri de aynı currency'e getirirdim.
