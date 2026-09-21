# Eval: MacBook Pro 14-inch M3 2024

Product ID: `macbook_pro_m3_2024`  
Source: `sample_data/macbook_pro_m3_2024.json` (50 reviews)

Questions are for chat prompt testing. **Expected** = scoring points grounded in those reviews (cite themes / review ids), not a required verbatim answer.

---

## Q1
How is the battery life day to day?

**Expected**
- Many say it lasts a full workday or more (r001, r024, r038, r050)
- Counterpoint: not as advertised — about 12–15h vs claimed 22 (r005); max brightness drains faster (r012)
- Flights / teaching day at ~60% brightness called strong (r035, r024)

## Q2
Is the M3 fast enough for video editing?

**Expected**
- 4K / Final Cut / multicam called smooth; exports much faster than Intel (r001, r036)
- Silent or quiet while rendering for some (r006, r018)
- Storage fills fast with video projects — 512GB complained about (r007, r029)

## Q3
What do reviewers say about the display?

**Expected**
- Gorgeous / XDR / color accuracy for photo & grading (r001, r004, r011, r036, r024)
- Reflective near windows; some bought matte protector (r005, r027)
- Notch: fine for many (r004, r026); awkward in some fullscreen apps (r047)
- QC: one unit had backlight bleed / light leak, exchanged (r017)

## Q4
Is 8GB unified memory enough?

**Expected**
- Frequent complaint: limiting for VMs / Docker / Chrome; wish 16GB base (r003, r007, r021, r023, r034)
- Performance great until memory pressure / swap stutter (r007, r023)
- Some workflows (dev with multiple VMs) still say it keeps up (r008) — minority vs RAM complaints
- Non-upgradeable RAM called limiting (r013, r015)

## Q5
How are MagSafe and the ports?

**Expected**
- MagSafe praised; saved drops / cable swap easy (r002, r020, r022); faulty cable replaced once (r032)
- HDMI + SDXC valued (no dongle for presentations / photo) (r014, r020)
- Still miss USB-A / still carry a hub (r003, r025); one cable for charge+display “not fully met” (r035)
- Better port set than Air (r011, r025); three Thunderbolt enough for some (r008)

## Q6
Is it good for software development?

**Expected**
- Xcode, simulators, IDEs, fast compiles vs Intel (r002, r004, r008, r021, r026, r048)
- Docker + multiple IDEs mentioned positively (r002) but RAM is the bottleneck for Docker/VMs (r023, r034)
- Team deploy: fewer build-speed complaints (r048)

## Q7
What about speakers, mic, and webcam?

**Expected**
- Speakers repeatedly “phenomenal” / Spatial Audio / movie nights (r002, r009, r022, r030)
- Mic clear on calls (r030)
- Webcam improved but still 1080p — want better at this price (r009, r030)

## Q8
Does it get hot or loud under load?

**Expected**
- Often silent / fans barely spin for coding or normal use (r006, r021, r026)
- Warm under heavy Blender / load but usually not badly throttled (r005, r018, r031)
- Sustained renders / no throttling vs Air called a upgrade point (r011)
- Fan noise under load “modest” for Logic (r041)

## Q9
Is the price / value fair?

**Expected**
- Split: “worth every penny” for pros (r011, r036) vs steep / Apple tax / ripoff base config (r003, r007, r015, r022)
- RAM/storage upgrade pricing called nickel-and-diming (r007, r015, r029)
- Student discount recommended (r038); refurbished positive (r028)
- M2 Pro owners: incremental, maybe wait (r040)

## Q10
How is the keyboard and trackpad?

**Expected**
- Trackpad often best-in-class / gestures / haptics (r004, r016, r024); one mushy-click unit variance (r033)
- Keyboard comfortable, good travel, quiet for offices (r002, r008, r022, r044)
- Function keys liked (r008); backlight could be brighter (r014)
- Sharp chassis edges dig into wrists (r012, r025)

## Q11
Any issues coming from Windows or Intel?

**Expected**
- Windows → Mac: smooth for some (r002); others miss touchscreen, prefer Win window mgmt, weak gaming (r019)
- Intel → M3: huge compile/export speed jump (r004, r021, r036)
- Ecosystem / AirDrop / iPhone-iPad praised for first-Mac users (r006)

## Q12
Storage complaints?

**Expected**
- 512GB fills with large/video projects; wish 1TB; price jump painful (r007, r029)
- Performance fine when space available (r029)

## Q13
Travel and weight?

**Expected**
- Some find it heavy in a backpack all day (r012)
- Others: travel weight fine but dense; battery on flights outstanding (r035, r049)
- Student / all-day no-outlet use praised (r038)

## Q14
External displays / clamshell?

**Expected**
- Clamshell with two external displays works with port caveats; read display limits (r042)
- HDMI to studio monitor works (r025)

## Q15
Software compatibility (audio plugins, Rosetta, gaming)?

**Expected**
- Some pro audio plugins not Apple Silicon native → Rosetta (r010)
- Native gaming hit-or-miss; cloud gaming fine; not bought for gaming (r019, r046); “surprisingly decent” for some (r011)
- Creative apps (Blender/Metal, Logic, Lightroom, Final Cut) strongly positive (r018, r031, r041, r024, r036)

## Q16
Build quality, cosmetics, repairs?

**Expected**
- Premium / solid / lasting build widely praised (r002, r014, r016, r044)
- Micro scratches / dust in ports anxiety (r037)
- Liquid-spill repair quote scary; AppleCare feels mandatory (r045)
- MagSafe cable / support experiences mixed-to-good (r032)

## Q17
Photo / music / 3D creative work?

**Expected**
- Photo: Lightroom / color accuracy (r004, r024, r014 SD slot)
- Music: Logic + sample libraries, low MIDI latency (r001, r041)
- 3D: Blender / Metal strong; warm but capable (r018, r031)

## Q18
What do people say about the notch, Touch ID, and migration?

**Expected**
- Notch mostly ignored or minor (r004, r026, r047)
- Touch ID reliable; some wanted Face ID (r004, r028)
- Migration Assistant seamless (r008, r028)

## Q19
Who should buy vs skip, based on reviews?

**Expected**
- Buy: creators, developers, Apple-ecosystem users, travel+work needing battery/display (r006, r008, r036, r049, r048)
- Caution/skip: need 16GB+ cheaply, hate dongles/hubs, want gaming/touchscreen, already on M2 Pro for light work (r003, r015, r019, r040, r023)
- Plan RAM/storage at purchase — not upgradable (r013, r015, r034)

## Q20
Do reviews conflict on battery and performance — how should an answer sound?

**Expected**
- Must cover both sides: all-day praise vs 12–15h / not-22h (r001 vs r005)
- Performance: beastly CPU/GPU vs stutter under memory pressure (r018 vs r023)
- Should cite concrete opinions, not only “mixed/unclear”
'''
