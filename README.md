# Nik yasovchi Telegram bot

800 xil shrift, qisqa (1–40) va uzun (1–2000) nik, admin panel, premium emoji, rangli tugmalar.
Bot GitHub Actions'da 24/7 ishlaydi (har 30 daqiqada cron tekshiradi).

## Ishga tushirish
1. @BotFather'da bot yarating, tokenni oling. O'z ID ingizni @userinfobot dan oling.
2. Yangi GitHub repo oching va shu fayllarni yuklang (`.github/workflows/bot.yml` ham).
3. Repo → Settings → Secrets and variables → Actions → New repository secret:
   - `BOT_TOKEN` — bot tokeni
   - `ADMIN_ID` — sizning Telegram ID ingiz
   - `DATA_KEY` — (ixtiyoriy) ma'lumotlarni shifrlash kaliti; bo'lmasa BOT_TOKEN ishlatiladi
4. Actions bo'limida workflow'ni yoqing → **Nik Bot 24/7** → Run workflow.
5. Botga /start yuboring. Admin panel: /admin yoki menyudagi tugma.

## Premium emoji
Dastlab hamma uyaga bitta vaqtincha emoji qo'yilgan. Admin panel → **Emoji sozlash** → uyani tanlang →
o'zingiz xohlagan premium emojini yuboring. Tugma emojilari faqat bot egasida Premium bo'lsa ishlaydi.
Tugma rangi va emojisini admin panel → **Tugmalar** dan ham o'zgartirasiz.

## Muhim
- Actions'da 24/7 ishlash uchun repo **public** bo'lishi kerak (private repoda oyiga 2000 daqiqa limit).
  Ma'lumotlar bazasi `data` branchda **shifrlangan** holda saqlanadi.
- Har ~6 soatda bot qayta ishga tushadi (job limiti); navbatdagi run uzilishsiz davom ettiradi.
- Muammo bo'lsa Actions → run logini ko'ring.