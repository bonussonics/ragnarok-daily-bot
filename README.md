# Ragnarok daily bot — first detector

สถานะ: ตรวจจับกิจกรรมและทดสอบคลิกหนึ่งครั้ง ยังไม่ทำเควสอัตโนมัติ

ภาพที่รับจริงมีขนาด 2048x1280 แม้ตั้งค่าเกมแจ้งว่า 1920x1080
รองรับภาพ 16:10 เช่น 2048x1280 และ 2560x1600 โดยตรวจบนภาพอ้างอิง 2048x1280 แล้วแปลงพิกัดกลับเป็นขนาดจริง
ต้องรักษา UI scale ที่สัมพันธ์กับขนาดจอเดิม หาก UI ไม่ได้ขยายตามจอ อาจตรวจไม่พบและต้องเก็บ template ใหม่
ไม่ยืดภาพต่างสัดส่วน เช่น 1920x1080

## Run on Windows / PowerShell

เปิด Terminal ในโฟลเดอร์นี้:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe detect_activity.py
```

สลับเข้าเกมภายใน 5 วินาที เปิดเมนูด้านบนให้เห็นกิจกรรม
ดู captures/activity_debug.png: กรอบเขียวต้องครอบปุ่มกิจกรรมจริง
ส่งภาพนี้กลับมาตรวจสอบก่อนเพิ่มระบบคลิก
ถ้าเกมอยู่จออื่น ใช้ --monitor 2
ทดสอบไฟล์เก่า: python detect_activity.py --image PATH
คะแนน 0.85 เป็นเกณฑ์ตั้งต้น ไม่ใช่ความน่าจะเป็น ต้องทดสอบหลายฉาก/แสง/เอฟเฟกต์
สคริปต์ไม่มีคำสั่งเมาส์หรือคีย์บอร์ด

## Git

มี Git bundle แนบใน zip เพื่อเก็บประวัติ commit แรก
หากต้องการเปิดเป็น repo ใหม่ (อย่าใช้ทับ repo เดิม):

```powershell
git clone .\ragnarok-daily-bot.bundle ragnarok-daily-bot-git
cd ragnarok-daily-bot-git
git remote remove origin
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

ยังไม่มี remote และยังไม่ได้ push ไป GitHub
รายละเอียดงานทั้งหมดอยู่ docs/workflows.md

## v0.3 ทดสอบเปิดกิจกรรม

คัดลอก open_activity.py, detect_activity.py และ requirements.txt มาด้วยกัน
ติดตั้ง: python -m pip install -r requirements.txt
ทดสอบคลิก: python open_activity.py --click
หากไม่ใส่ --click จะตรวจจับเท่านั้น
สลับเข้าเกมภายใน 5 วินาที เกมต้องอยู่จอหลัก
ตรวจสองภาพต่อเนื่อง คะแนนอย่างน้อย 0.90 และตำแหน่งคงที่ก่อนคลิก
กด Esc ค้างหรือเลื่อนเมาส์ไปมุมจอหลักเพื่อยกเลิกก่อนคลิก
บันทึก captures/activity_before_click.png และ activity_after_click.png
สคริปต์ไม่วนคลิกและไม่ถือว่าส่งคลิกแล้วเท่ากับเปิดเมนูสำเร็จ
ต้องตรวจภาพหลังคลิกจริงบน Windows; ยังไม่ได้ทดสอบ input กับเกมจากเครื่องนี้

## v0.4 Guild Go test

เริ่มจากหน้า กิจกรรมรายวัน ที่เปิดแล้ว
รัน python guild_daily.py --click แล้วสลับเข้าเกมใน 5 วินาที
ตรวจชื่อประจำวัน Guild พร้อม 0/1 และปุ่มไปในใบเดียวกัน ก่อนคลิกหนึ่งครั้ง
ถ้าหาไม่พบหรือเป็นสถานะเสร็จแล้ว สคริปต์หยุดโดยไม่คลิก
เก็บ guild_after_click.png หลัง 2 วินาที และ guild_after_travel.png หลังรอเพิ่ม 20 วินาที
การรอ 20 วินาทีใช้เก็บภาพเท่านั้น ไม่ถือเป็นหลักฐานว่าเดินทางเสร็จ
ยังไม่กดยืนยันรับและไม่ตรวจเควสจบ
ไฟล์ใหม่: guild_daily.py, assets/templates/guild_title.png, guild_zero.png, guild_go.png
ไฟล์แก้ไข: open_activity.py
ทดสอบกับภาพจริงที่ให้มา ภาพจำลอง 2560x1600 การย้ายการ์ดอีกคอลัมน์ และการไม่มีตัวเลข 0/1
การส่งคลิก Guild ต้องทดสอบจริงบน Windows ของผู้ใช้

## v0.5 รับเควสกิลด์

เพิ่ม guild_accept.py และ assets/templates/guild_accept.png, guild_dialog_npc.png,
guild_talk.png, guild_nearby_npc.png ลงโฟลเดอร์เดิม
รัน python guild_accept.py --click จากหน้าสนทนากิลด์หรือหน้ารอยืนยันรับ
ตรวจชื่อ NPC ร่วมกับปุ่มสองภาพติดกัน ก่อนกด F อย่างมากหนึ่งครั้งและยืนยันอย่างมากหนึ่งครั้ง
รอไม่เกิน 60 วินาที หากไม่มั่นใจจะหยุด ไม่มีการคลิกซ้ำ
ส่ง captures/guild_after_accept.png หลังคลิก 5 วินาที เพื่อตรวจว่าเริ่มเควสจริง
ไม่ถือว่าปุ่มหายไปคือเควสสำเร็จ ยังไม่ได้ทำตัวตรวจจบ 1/1
ทดสอบรูปสนทนา/ยืนยันและภาพอื่นที่ไม่ควรผ่าน พร้อมขนาดจำลอง 2560x1600 แล้ว
ยังต้องทดสอบการส่ง input จริงกับเกมบน Windows

## v0.6 เชื่อมขั้นตอนกิลด์และตรวจจบ

เพิ่ม run_guild.py, guild_status.py และรวม assets/templates กับโฟลเดอร์เดิม
ใช้ .venv เดิม ไม่ต้องติดตั้งเพิ่ม
ตรวจสถานะอย่างเดียว: python run_guild.py
เปิดหน้ากิจกรรมที่เห็นการ์ดกิลด์ แล้วสลับเข้าเกมภายใน 5 วินาที
ผลถูกบันทึกใน captures/guild_run_result.json และ guild_workflow_last.png
รันครบขั้นตอน: python run_guild.py --run
เริ่มจากหน้าตัวละคร/หน้ากิจกรรม/หน้า NPC/หน้ารอยืนยัน/ระหว่าง Auto ที่มองเห็นชื่อเควส
ถ้าพบ 1/1 พร้อมเครื่องหมายถูกในใบกิลด์เดียวกันสองภาพติดกัน จะจบทันที ไม่รับซ้ำ
หากการ์ดไม่อยู่ในหน้าจอ จะเลื่อนขึ้นแล้วลงแบบจำกัดจำนวนในพื้นที่รายการที่ตรวจยืนยันแล้ว
รอ NPC และเควสเริ่มไม่เกิน 120 วินาทีในแต่ละช่วง; เวลารวมเริ่มต้น 1800 วินาที
หลังเคยเห็น Guild รายวันกำลังทำ รอชื่อเควสหายบน HUD ปกติ 3 รอบตรวจ (ทุก 5 วินาที)
จากนั้นเปิดกิจกรรมและตรวจ 1/1 + เครื่องหมายถูก ไม่ถือว่าภารกิจหายหรือฉากโหลดคือเสร็จ
หากยังเป็น 0/1 หลังตรวจ จะหยุดเป็น stopped_unverified โดยไม่รับซ้ำ
หาก Esc ค้าง เปลี่ยนหน้าต่าง หรือใช้ mouse fail-safe จะหยุด
ไม่เชื่อถือสถานะบันทึกจากรอบเก่าเพื่อข้ามงาน ทุกครั้งตรวจหน้าจอใหม่
ยังไม่มีระบบรีเซ็ตรายวันหรือตรวจงานบอร์ด/Home/MVP
ชุดทดสอบภาพ: สำเร็จ/ไม่สำเร็จที่ 2048x1280 และจำลอง 2560x1600,
ย้ายการ์ดไปอีกคอลัมน์, ลบเลข 1/1, ลบเครื่องหมายถูก, บังการ์ด,
ภาพโหลดฉากและภาพเควสกำลังทำ ผ่านทั้งหมด
การเลื่อนและการรันครบวงจรจริงยังต้องทดสอบบน Windows ของผู้ใช้

## v0.7 การ์ดกิลด์ถูกแถบรางวัลบังเมื่อเลื่อนสุด

รองรับการ์ดที่เลข 1/1 ถูกบัง โดยตรวจหัวการ์ดกิลด์แบบสีจางและภาพส่วนบน
50 พิกเซลของเครื่องหมายถูกในใบเดียวกัน คะแนนทั้งสองต้อง >= 0.95
ผล JSON ระบุ evidence เพื่อแยกวิธีนี้จากการเห็น title + 1/1 + check ครบ
หากเห็นหัวการ์ดแต่หลักฐานไม่พอ จะคืน guild_card_obscured และไม่ถือว่าเสร็จ
โหมด --run ยังคงยืนยันสองภาพติดกันก่อนจบ

อัปเดต guild_status.py และ run_guild.py ในโฟลเดอร์เดิม เก็บ .venv เดิมไว้
เปิดหน้ากิจกรรมตามภาพเดิม แล้วรันอ่านอย่างเดียว:

```powershell
.\.venv\Scripts\python.exe run_guild.py
```

ทดสอบออฟไลน์ผ่านภาพที่ส่งมา: การ์ดถูกบังและการ์ดเต็มเป็น completed,
การ์ดที่ยังไม่รับเป็น pending, ฉากโหลดเป็น unknown ที่ 2048x1280 และ
2560x1600 (ภาพปรับขนาดจำลอง); ลบเครื่องหมายถูกแล้วไม่รายงาน completed
ยังต้องทดสอบหน้าจอจริงบน Windows โดยผู้ใช้

## v0.8 บอร์ดเควส (แยกจากกิลด์)

เพิ่ม run_board.py, board_status.py และ assets/templates/board_*.png
ใช้โมดูลเดิมประกอบ จึงคัดลอกทั้งโฟลเดอร์ assets/templates และไฟล์ Python ใหม่
ลงโฟลเดอร์โปรเจกต์เดิม เก็บ .venv เดิมไว้ ไม่ต้องติดตั้ง dependency เพิ่ม

1. เปิดหน้าบอร์ดที่มีปุ่มส้ม “เริ่มงานมอบหมาย”
2. ทดสอบอ่านอย่างเดียว ควรได้ state: start:

```powershell
.\.venv\Scripts\python.exe run_board.py
```

3. เริ่มทำจริงจากหน้าบอร์ดเดิม หรือหน้าตัวละครปกติ/หน้ากิจกรรม:

```powershell
.\.venv\Scripts\python.exe run_board.py --run
```

สลับเข้าเกมภายใน 5 วินาที กด Esc หรือเลื่อนเมาส์เข้ามุมเพื่อหยุด
ปุ่ม Go/เริ่ม/ยืนยันต้องตรวจได้สองภาพตำแหน่งนิ่งก่อนคลิกครั้งเดียว
ไม่รีเฟรชภารกิจและไม่ซื้อรอบเพิ่ม หลังยืนยันให้เกมทำอัตโนมัติ
เมื่อเห็นหน้าตัวละครจะเปิดกิจกรรมตรวจชื่อบอร์ด + 1/1 + เครื่องหมายถูก
หากยัง pending จะปิดกิจกรรมด้วย Esc แล้วรอ 30 วินาทีก่อนตรวจอีกครั้ง
ไม่รับงานซ้ำ ไม่ถือว่าปุ่มหาย/ฉากโหลดคือเสร็จ จำกัดรวม 30 นาที
หาก UI ไม่ตรงหรือเปิดหน้ากิจกรรมไม่ได้ จะหยุดพร้อมภาพและ JSON:

- captures/board_workflow_last.png
- captures/board_run_result.json
- captures/board_after_start.png และ board_after_confirm.png เมื่อมีการคลิก

ข้อจำกัด: ทดสอบจากภาพเท่านั้น ยังไม่ได้ทดสอบบน Windows จริง
ภาพก่อนเริ่มและยืนยันที่ผู้ใช้ส่งมาตรวจผ่านทั้งขนาดอ้างอิง 2048x1280
และขนาดจำลอง 2560x1600; การตรวจจบใช้การ์ดสำเร็จจากภาพเก่าที่ปรับขนาด
วางบนหน้ากิจกรรมอ้างอิง จึงยังต้องยืนยันกับภาพสำเร็จจริงใน UI ปัจจุบัน
ถ้าการ์ดจบถูกบังจนไม่เห็น 1/1 และเครื่องหมายถูก จะไม่ยืนยันผลสำเร็จ
รองรับเฉพาะอัตราส่วน 16:10 ตามภาพจับหน้าจอที่ใช้งานผ่านแล้ว

## Home entry v0.9 — ทดสอบเข้า Home

เปิดเมนูขวาล่างให้เห็นปุ่ม Home ก่อน แล้วรัน:

```powershell
.\.venv\Scripts\python.exe run_home.py
```

ผลที่คาดหวังคือ `home_menu` หรือ `return_home` ถ้าเปิดหน้าหลัก Home อยู่แล้ว
เมื่อผลถูกต้องจึงทดสอบคลิก:

```powershell
.\.venv\Scripts\python.exe run_home.py --run
```

สลับกลับเกมภายใน 5 วินาที สคริปต์คลิก Home แล้วกลับบ้านอย่างละไม่เกินหนึ่งครั้ง
รอ 20 วินาทีและบันทึก `captures/home_workflow_last.png` กับ `home_run_result.json`.
`return_sent_unverified` หมายถึงส่งคำสั่งแล้ว ยังไม่ยืนยันว่าถึงบ้านหรือทำงานสำเร็จ
Esc, ย้ายเมาส์เข้ามุมจอ หรือเปลี่ยนหน้าต่างจะหยุดการทำงาน
ถ้าไม่พบปุ่ม ให้ส่งภาพผลลัพธ์เพื่อปรับ detector ก่อน ไม่ลด threshold เอง

ยังไม่มีเดินหาเชฟ รับอาหาร ตักน้ำ เก็บเกี่ยว ซื้อเมล็ด หรือปลูกอัตโนมัติใน v0.9
ข้อกำหนดขั้นต่อไป: ฟักทอง 3 แปลง × 6 แถว; ตักน้ำหนึ่งครั้งต่อแปลง;
กดรดน้ำครั้งแรกเท่านั้น ไม่รดน้ำซ้ำหลังปลูกแต่ละแถว; เดินได้ด้วยคลิกพื้นหรือ WASD.
ภาพอ้างอิง Home เดิมเป็น 16:9 จึงตรวจแบบรักษาสัดส่วนและลองหลายขนาดไอคอน
ยังต้องทดสอบตำแหน่ง UI จริงบนจอ 2560×1600.

Validation v0.9: Home menu/Return detected on supplied reference images and uniform
2560-wide resizes (scores ~0.97); world/activity negatives rejected; existing six tests pass.
No live Windows Home test performed by the author.

## Sequential Guild → Board v0.10

เริ่มจากหน้าตัวละครปกติที่เห็นปุ่มกิจกรรม แล้วรัน:

```powershell
.\.venv\Scripts\python.exe run_daily.py --run
```

สลับกลับเกมภายใน 5 วินาที ตัวรันจะเปิดกิจกรรม → ทำ Guild → ตรวจ completed
→ ปิดหน้าเช็กผล Guild → เปิดกิจกรรมใหม่ → ทำ Board → ตรวจ completed → หยุด
ไม่ต้องสลับกลับ Terminal ระหว่างสองงาน หน้าต่างเกมต้องอยู่ด้านหน้าตลอด
กด Esc ค้างหรือย้ายเมาส์เข้ามุมจอเพื่อหยุด

ถ้าเควสเสร็จแล้ววันนี้ จะยืนยันจากการ์ดและข้ามการรับเควสซ้ำ
จึงทดสอบเส้นทางรับเควสครบได้ในวันที่ทั้งสองงานยังไม่เสร็จ
`--timeout 1800` คือเวลาสูงสุดต่อหนึ่งงาน (ค่าเริ่มต้น 30 นาที)
ไม่ใส่ `--run` จะตรวจ Guild แบบอ่านอย่างเดียว ไม่เริ่มลำดับงาน

ดู `captures/daily_run_result.json`: `completed` ยืนยันครบทั้งสองงาน;
`stopped_unverified` หมายถึงหยุดก่อนยืนยันครบ ดู error และรายงานย่อย Guild/Board.
ตัวรันใช้ผลคืนจากการทำงานปัจจุบันเท่านั้น ไม่อ่านไฟล์ผลสำเร็จเก่ามาเริ่มงานถัดไป
Home/MVP ไม่อยู่ในลำดับนี้ สคริปต์แยกเดิมยังใช้ได้

Validation: detector tests and sequence tests (success, failed/unverified Guild,
failed Board) passed. Live chained Windows/game test is pending user testing.

## v0.11 Guild NPC fix

เพิ่ม template ชื่อผู้มอบเควสจากภาพที่ค้างหน้า NPC: เดิมปุ่มสนทนาคะแนน .963
แต่ชื่อ NPC .495 ทำให้ไม่กด F ตอนนี้ภาพดังกล่าวตรวจได้ `talk` .963
ยังต้องตรวจทั้งชื่อ NPC และปุ่มสนทนา ไม่ลด threshold รวม

Guild จะพัก input ระหว่างเสียโฟกัสไม่เกิน 2 วินาที แล้วทำต่อเฉพาะเมื่อ HWND เดิม
กลับมาเท่านั้น ไม่ดึงโฟกัสเอง หากไม่กลับจะหยุดและรายงาน handle/PID/class/title
ของหน้าต่างเดิมและหน้าต่างปัจจุบันใน error พร้อม npc_detection ใน guild_run_result.json
Board ยังใช้การหยุดทันทีเมื่อโฟกัสเปลี่ยนตามเดิม

รันทดสอบต่อจากหน้า NPC เดิมได้ด้วย `run_daily.py --run`.
ดูข้อความ `Guild NPC verified; sending F.` หากหยุดอีก ส่ง guild_run_result.json
พร้อมภาพ guild_workflow_last.png. ทดสอบ offline และ unit tests ผ่าน 12 ข้อ;
ยังไม่ได้ทดสอบ live Windows รอบนี้

## v0.12 NPC background-independent fallback

แก้กรณีภาพล่าสุด talk=.960 แต่ชื่อ NPC แบบ grayscale=.817 ทำให้ timeout.
เพิ่มการจับ glyph สีเหลืองของชื่อ NPC (dilate 1px) threshold .85 ร่วมกับ
ปุ่มสนทนา >=.95 และชื่อฉาก Guild >=.90 ทุกเงื่อนไขต้องผ่าน
เส้นทางตรวจแบบเดิมยังคงอยู่ คะแนน target สำหรับ stable_target คือปุ่มสนทนา
ไม่ใช่คะแนนชื่อ NPC. เพิ่ม log NPC detection ทุก 10 วินาทีระหว่างรอ.

Regression tests: ทั้งภาพก่อนหน้า/ล่าสุดและขนาด 2560×1600 ตรวจได้;
เมื่อเอาชื่อ NPC, ปุ่มสนทนา หรือฉาก Guild ออกจาก fixture ล่าสุดต้องไม่กด.
รวม 13 tests ผ่าน; ยังต้องทดสอบ live ในเกม.

## v0.13 Guild camera rotation and routing fix

ภาพล่าสุดชื่อ NPC อยู่ประมาณ x1117..1240 ขณะที่กรอบเดิมจบ x1200
จึงถูกตัดและตรวจไม่พบ ขยายบริเวณชื่อเป็น (600,550)-(1500,1000)
และเทียบ glyph สีเหลืองหลายขนาด .85–1.25 รองรับขนาดชื่อที่เปลี่ยนตามมุมกล้อง
fallback ใช้ talk>=.90, yellow glyph>=.80 และ Guild scene>=.90 ร่วมกัน
เพิ่ม npc_scale ใน diagnostics. คะแนนเป็นความคล้าย ไม่ใช่ความน่าจะเป็น

ถ้าเห็นปุ่มสนทนา >=.90 แต่ยังยืนยัน NPC ไม่ได้ จะรอตรวจต่อภายใน timeout
ไม่เปลี่ยนไปเปิดกิจกรรมเองเหมือนก่อน จึงไม่จบด้วย Activity detection error ที่บดบังสาเหตุ

Validation: 14 tests ผ่าน รวมภาพมุมกล้องใหม่ที่ 2048/2560, ลบชื่อ NPC/ฉาก/ปุ่ม
แล้วต้องไม่ยืนยัน talk และการเลือกเส้นทางเมื่อพบปุ่มสนทนา; live test ยังรอทดสอบ.

## v0.14 Fix dialog callback scope

แก้ UnboundLocalError ของ last_npc_log: callback ตรวจ dialog เคยมี log timer
ที่กำหนดตัวแปรใน nested function ผิด scope จึงพังก่อนกด F หลังตรวจ talk ผ่าน
ย้าย dialog_detector เป็น pure callback ระดับ module และเก็บ log timer เฉพาะ main loop
ไม่มีการเปลี่ยน threshold หรือ template ในรุ่นนี้
เพิ่ม regression test เรียก callback เดียวกับ live path สองครั้งผ่าน stable_target
รวม 15 tests ผ่าน และ callback กับภาพล่าสุดผ่าน; ไม่ได้ทดสอบคลิกเกมจริง.

## v0.15 Board confirmation with scrolling text (Board workflow v0.9)

แก้ปุ่มยืนยันเริ่มงานมอบหมายที่ข้อความเลื่อน: ตรวจขอบบน/ล่างของปุ่ม
พร้อมระยะห่างและแนวเดียวกัน โดยต้องยืนยันหัวข้อบอร์ด หัวข้อ dialog และเนื้อหา dialog
ยังใช้ threshold .90 และตรวจสองภาพก่อนคลิก ไม่ลด threshold ของ Activity/Guild
หากสถานะเปลี่ยนชั่วคราวก่อนคลิก จะตรวจซ้ำไม่เกิน 8 รอบ; ไม่คลิกซ้ำอัตโนมัติ
และไม่กลืนข้อผิดพลาด Esc, foreground หรือ input.

ถ้าค้างที่กล่องยืนยันอยู่ ให้รันจากหน้าปัจจุบัน:
```powershell
.\.venv\Scripts\python.exe run_board.py --run
```
ทดสอบลำดับเต็มจากหน้าตัวละครหรือกิจกรรม:
```powershell
.\.venv\Scripts\python.exe run_daily.py --run
```
Validation: 18 tests ผ่าน รวมภาพปุ่มเลื่อนทั้งสองจังหวะที่ 2048×1280/2560×1600,
ลบปุ่ม/หัวข้อ/เนื้อหาแล้วต้องไม่ยืนยัน, การรอตรวจใหม่และส่งคลิกครั้งเดียว,
foreground เปลี่ยนต้องไม่คลิก. ยังไม่ได้ทดสอบคลิกจริงบน Windows.

## v0.16 Board completion verification (Board workflow v0.10)

Live run completed Board, but the old daily 1/1 template scored .8899 below .90.
Added a count template from the real completed Board card; threshold remains .90.
Title, count and check must still belong to the same card. Unverified reports now
include candidate evidence scores. No changes to Guild or input behavior.
19 tests pass, including the new live screenshot at 2048×1280 and 2560×1600,
and rejection when Board title/count/check is removed despite completed neighbors.

Open Activity with the completed Board card visible, then verify without clicks:
```powershell
.\.venv\Scripts\python.exe run_board.py
```
Expected state: completed; completion_verified: true.
