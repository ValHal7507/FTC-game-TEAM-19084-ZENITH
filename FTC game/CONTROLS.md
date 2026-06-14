# Ghid de Control — FTC DECODE Match Simulator

## Controlere acceptate

Jocul accepta orice controler/gamepad compatibil **SDL**, detectat automat prin Pygame:

- **Xbox 360 / Xbox One / Xbox Series X|S** (cu fir sau wireless)
- **PlayStation 3 / 4 / 5** (DualShock 3/4, DualSense)
- **Nintendo Switch Pro Controller**
- **Controlere generice USB sau Bluetooth** cu scheme de butoane Xbox-compatible

> **Nota:** In modul Solo, toate controlerele conectate functioneaza simultan. In modul 1v1, fiecare jucator isi alege cate un controler.

La pornire, numele controlerului detectat apare in consola (ex: `Gamepad 0: Xbox Controller`).

---

## Moduri de deplasare

Jocul dispune de **doua moduri de deplasare**, comutabile cu tasta `R` (tastatura) sau `LB` (controler):

| Mod | Comportament |
|---|---|
| **Field** (implicit) | W/S/A/D sau stick-ul stanga se deplaseaza pe axe lumii: W = sus, S = jos, A = stanga, D = dreapta, indiferent de directia robotului |
| **Robot** | W = inainte (directia robotului), S = inapoi, A = stranga perpendicular pe directie, D = dreapta perpendicular pe directie |

Modul curent este afisat intr-un badge in coltul stanga sus al terenului.

---

## Control cu tastatura

### Deplasare si rotatie — P1

| Tasta | Actiune |
|---|---|
| `W` | Inainte (directia robotului in mod Robot / sus in mod Field) |
| `S` | Inapoi (directia robotului in mod Robot / jos in mod Field) |
| `A` | Strafe stanga (mod Robot) / Stanga pe lume (mod Field) |
| `D` | Strafe dreapta (mod Robot) / Dreapta pe lume (mod Field) |
| `←` (sagata stanga) | Roteste robotul in sens antiorar |
| `→` (sagata dreapta) | Roteste robotul in sens orar |

### Actiuni — P1

| Tasta | Actiune |
|---|---|
| `E` | Tine apasat pentru intake (ridicare continua cat timp e tinut; blocat cand e supraincalzit) |
| `Q` | Lanseaza TOATE artefactele detinute spre gol (oricate ar avea) |
| `R` | Comuteaza modul de deplasare (Robot / Field) |
| `T` | Deschide / inchide poarta ( trebuie sa fii in raza de actiune a portii ) |

### Controle meci

| Tasta | Actiune |
|---|---|
| `F5` | Reseteaza jocul (opreste totul, repune artefactele) |
| `F6` | Porneste cronometrul (doar cand e oprit) |
| `ESC` | Pauza / Resume (sau inchide ecranul Options daca e deschis) |
| `F10` | Iesire din joc |

> **Sageti Numpad:** Tastele `KP8`/`KP2`/`KP4`/`KP6` functioneaza ca sagetile obisnuite in toate meniurile (selectie mod, asignare controler, pauza, sfarsit de meci, Options).

### P2 — Control cu tastatura (1v1)

In modul 1v1, P2 foloseste urmatoarele taste (implicate, nu pot fi personalizate):

| Tasta | Actiune |
|---|---|
| `I` | Inainte |
| `K` | Inapoi |
| `J` | Strafe stanga |
| `L` | Strafe dreapta |
| `U` | Roteste robotul in sens antiorar |
| `O` | Roteste robotul in sens orar |
| `P` | Tine apasat pentru intake (blocat cand e supraincalzit) |
| `;` | Lanseaza TOATE artefactele detinute spre gol |
| `.` | Deschide / inchide poarta |
| `M` | Comuteaza modul de deplasare (Robot / Field) |

---

## Control cu gamepad (controler)

### Stick-uri

| Stick | Actiune |
|---|---|
| **Stick stanga** | Deplasare (directie dependa de modul curent: Field sau Robot) |
| **Stick dreapta (X)** | Roteste robotul (stanga/dreapta) |

> Are zona moarta (deadzone) de 15% pentru precizie.

### Triggere

| Trigger | Actiune |
|---|---|
| **Trigger stanga (LT)** | Lanseaza TOATE artefactele detinute spre gol (oricate ar avea) |
| **Trigger dreapta (RT)** | Tine apasat pentru intake (ridicare continua cat timp e tinut; blocat cand e supraincalzit) |

> La trigger-ul stanga se foloseste edge detection: lansarea se declanseaza doar la apasare, nu si la mentinere.

### Butoane

| Buton | Actiune |
|---|---|
| `X` (butonul 2) | Deschide / inchide poarta ( trebuie sa fii in raza de actiune ) |
| `Y` (butonul 3) | Pauza / Resume |
| `LB` (butonul 4) | Comuteaza modul de deplasare (Robot / Field) |
| `Back / Select` (butonul 6) | Reseteaza jocul |

---

## Gameplay — Cum se joaca

### Obiectivul

Scopul este sa colectezi artefacte de pe teren, sa le clasifici pe rampa si sa le lansezi spre gol pentru a puncta. La finalul meciului, robotul trebuie parcat in zona de baza pentru puncte bonus.

### Pregatirea meciului

1. Jocul porneste in faza **TELEOP** cu 120 de secunde pe cronometru, cronometrul **OPRIT**
2. Apasa **F6** (tastatura) pentru a porni cronometrul si a incepe meciul

### Colectarea artefactelor

- Apropie robotul de un artefact (cercurile de pe teren: violet sau verde)
- Artefactul trebuie sa fie in **fata** robotului (un con de 120 grade)
- Daca intakes-ul e **pornit** (`E` / `RT`), robotul ridica automat artefactele din fata
- Daca intakes-ul e **oprit**, robotul nu ridica nimic automat
- Robotul poate tine maxim **3 artefacte** simultan

### Lansarea spre gol

- Apropie robotul de **zona de lansare** (triunghiul de sus din teren, zona de shooting din centru-jos, sau zona de baza)
- Apasa `Q` (tastatura) sau `LT` (controler) pentru a lansa toate artefactele detinute
- Artefactele zboara spre gol si intra in rampa vizual
- **Puncte:** artefactele lansate din zona de lansare primesc puncte; cele lansate din alta zona nu primesc nimic (doar umplu rampa vizual)

### Rampa si clasificarea

- Cand un artefact este lansat din zona de lansare, acesta este plasat pe rampa in sloturi:
  - Daca robotul avea 3 artefacte → artefactele se clasifica direct (+3 puncte fiecare)
  - Daca robotul avea mai putin de 3 → artefactele merg in depot/overflow (+1 punct fiecare)
- Rampa are 9 sloturi (3 culori x 3)
- La sfarsitul meciului, sloturile care corespund motivului (motif) primesc +2 puncte fiecare

### Poarta (Gate)

- Apropie robotul de poarta (linia de pe teren)
- Apasa `T` (tastatura) sau `X` (controler) pentru a deschide
- Cand poarta se deschide, toate artefactele de pe rampa sunt **teleportate** pe teren (la pozitii aleatoare)
- Poarta se inchide automat dupa 2 secunde
- Util pentru a recicla artefacte cand rampa e plina

### Parcare

- La sfarsitul meciului, parca robotul in **zona de baza** (patratul din coltul stanga-jos al terenului)
- Robotul complet inauntru → +10 puncte
- Robotul partial in zona → +5 puncte
- Robotul in afara → 0 puncte

### Faza Endgame

- In ultimele **20 de secunde**, faza trece la **ENDGAME** (text portocaliu clipitor)
- La 0 secunde, meciul se termina si apare ecranul cu scorul final

### Pauza si reset

- `ESC` (tastatura) — pune pe pauza / reia cronometrul (si porneste cronometrul cand e oprit)
- In 1v1, **ambii jucatori** pot pune pauza prin `ESC`
- Cand cronometrul e oprit, robotul **nu se misca** si nu poate interactiona
- Starea intakes-ului (pornit/oprit, caldura, cooldown) se reseteaza la fiecare pauza, sfarsit de meci sau reset
- Navigare meniu pauza: `↑`/`↓` sau `KP8`/`KP2` (numpad)
- Selectie: `Enter`/`Space`
- Butoanele meniului de pauza:
  - **Resume** — reia meciul
  - **Restart Game** — reseteaza terenul si incepe un nou meci
  - **Detect Gamepads** — rescaneaza controlerele conectate
  - **Options** — personalizeaza tastele si butoanele (ascuns in modul 1v1)
  - **Mode Select** — revenire la ecranul de selectie a modului
  - **Quit** — iesire din joc
- `F5` (tastatura) — reseteaza intregul joc (teren, artefacte, scor)
- `F10` — iesire din joc

### Ecranul de sfarsit de meci

- Dupa terminarea meciului, apar butoanele **Restart** si **Exit**
- Navigare intre butoane: `←`/`→` (sageti) sau `KP4`/`KP6` (numpad)
- Selectie: `Enter`/`Space` (tastatura)
- `F5` (tastatura) — reseteaza meciul (scurtatura)
- `F10` (tastatura) — iesire din joc (scurtatura)

### Ecranul Options (Personalizare taste)

Din meniul de pauza, selecteaza **Options** pentru a personaliza tastele si butoanele:

- Doua tab-uri: **KEYBOARD** si **GAMEPAD**, comutabile cu sagetile Left/Right (`KP4`/`KP6` pe numpad)
- Navigheaza cu sagetile Up/Down (`KP8`/`KP2` pe numpad)
- Apasa **Enter** pe un rand pentru a incepe rebinding-ul
- In timpul rebinding-ului: apasa orice tasta/but nou pentru a atribui, sau **Backspace** pentru a sterge
- **Escape** iesi din ecranul Options
- Randul **Reset to Default** din partea de jos restaureaza toate tastele la valorile implicite
- Legaturi duplicat sunt marcate cu `!`
- Legaturi blocate (Reset pe controler) sunt marcate ca `(Fixed)`

> **Modul 1v1:** Ecranul Options este complet ascuns — butonul nu apare in meniul de pauza. Tastele sunt fixe (valorile implicite) si nu pot fi personalizate.

> Setarile de taste sunt salvate automat intr-un fisier `keybinds.json` in folderul jocului si persista intre sesiuni (doar in Solo). La prima pornire se folosesc valorile implicite. In modul 1v1, tastele sunt intotdeauna cele implicite (fisierul JSON nu este citit).

---

## Sistemul de punctaj

| Eveniment | Puncte | Observatii |
|---|---|---|
| Artefact clasificat pe rampa | +3 | Doar daca robotul era in zona de lansare |
| Overflow / Depot | +1 | Doar daca robotul era in zona de lansare |
| Slot de rampa care corespunde motivului | +2 | Evaluat la sfarsitul meciului |
| Parcare completa in baza | +10 | Robotul complet in interiorul zonei de baza |
| Parcare partiala in baza | +5 | Robotul suprapus partial cu zona de baza |

**Zona de lansare** include: triunghiul de sus, zona de baza (coltul stanga-jos), si triunghiul de shooting (centru-jos).

**Motivul** (culorile care trebuie aliniate pe rampa) este generat aleator la fiecare reset: una dintre variantele `GPP`, `PGP` sau `PPG`.

---

## Moduri de joc

### Solo Practice

- Un singur jucator, control complet asupra robotului
- **Mod dual-input**: Atat tastatura cat si controlerele conectate functioneaza simultan, indiferent ce dispozitiv ai ales la meniu — poti conduce cu WASD si sa pui pauza cu Y pe controler, sau sa conduci cu controlerul si sa lansezi cu Q
- Poti exersa colectarea, clasificarea, lansarea si parcare fara presiunea unui adversar

### 1v1 Local

- Doi jucatori pe aceeasi tastatura/gamepad
- Fiecare jucator are propriul robot, rampa, intake si scor
- Artefactele sunt dublate: 18 de baza + 18 mirror pe jumatatea lui P2 (36 total)
- **Robotii se ciocnesc intre ei** — daca cei doi roboti se suprapun, sunt impinsi automat la jumatatea distantei de separare pe cea mai mica axa (nu pot trece unul prin altul)
- **Ambii jucatori pot pune pauza** prin `ESC`
- La sfarsitul meciului, castigatorul este anuntat (P1 WINS / P2 WINS / TIE)
- La selectarea modului 1v1, ambii jucator isi aleg dispozitivul de control (Gamepad 1 sau Gamepad 2)
- **Asignarea implicita a controlerelor** (la intrarea in ecranul de asignare):
  - 2+ controlere detectate → P1 = Gamepad 1, P2 = Gamepad 2
  - 1 controler detectat → P1 = Gamepad 1, P2 = AI
  - 0 controlere detectate → P1 = Gamepad 1 (neidentificat), P2 = AI
  - Utilizatorul poate schimba selectiile folosind sagetile
- **Tastele nu pot fi personalizate in 1v1** — meniul Options este ascuns si tastele raman la valorile implicite pe toata durata meciului

### vs AI (prin modul 1v1)

- Un jucator (P1) contra unui robot controlat de calculator (P2)
- La selectarea modului 1v1, daca este detectat un singur controler, P2 este setat automat pe **AI** (asignare implicita). P2 poate alege, de asemenea, AI manual in ecranul de asignare a controlerelor
- **Robotii se ciocnesc intre ei** — daca cei doi roboti se suprapun, sunt impinsi automat (la fel ca in 1v1)
- AI-ul foloseste o strategie bazata pe reguli cu 5 stari:
  1. **Colectare** — cauta cel mai apropiat artefact si se indreapta spre el mereu (il "impinge"/"loveste"). Intakes-ul se activeaza doar cand robotul se afla la sub 85 pixeli de artefact
  2. **Navigare** — daca detine suficiente artefacte, se indreapta spre cea mai apropiata zona de lansare
  3. **Lansare** — daca se afla in zona de lansare, lanseaza toate artefactele detinute
  4. **Parcare** — in ultimele 5 secunde, se indreapta spre zona de baza pentru puncte bonus
  5. **Poarta** — daca rampa are artefacte si poarta e inchisa, se apropie de poarta si o deschide pentru a recicla artefactele
- AI-ul are **protectie supraincalzire** — opreste intake-ul cand e supraincalzit
- AI-ul **evita obstacolele** — ruta inconjoara automat zona gol+depot
- AI-ul se **deblocheaza singur** — daca robotul ramane blocat, incearca directii alternative pentru a iesi

> **Nota:** Modul vs AI este activ. Codul AI exista in `ai_controller.py` si este conectat in `mode_1v1.py`. Cand P2 este setat pe AI, robotul P2 este controlat de inteligenta artificiala.
