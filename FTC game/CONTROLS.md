# Ghid de Control — FTC DECODE Match Simulator

## Controlere acceptate

Jocul accepta orice controler/gamepad compatibil **SDL**, detectat automat prin Pygame:

- **Xbox 360 / Xbox One / Xbox Series X|S** (cu fir sau wireless)
- **PlayStation 3 / 4 / 5** (DualShock 3/4, DualSense)
- **Nintendo Switch Pro Controller**
- **Controlere generice USB sau Bluetooth** cu scheme de butoane Xbox-compatible

> **Nota:** Doar primul controler conectat este utilizat. Daca ai mai multe, deconecteaza-le pe celelalte inainte de a porni jocul.

La pornire, numele controlerului detectat apare in consola (ex: `Gamepad 0: Xbox Controller`).

---

## Moduri de deplasare

Jocul dispune de **doua moduri de deplasare**, comutabile cu tasta `R` (tastatura):

| Mod | Comportament |
|---|---|
| **Field** (implicit) | W/S/A/D sau stick-ul stanga se deplaseaza pe axe lumii: W = sus, S = jos, A = stanga, D = dreapta, indiferent de directia robotului |
| **Robot** | W = inainte (directia robotului), S = inapoi, A = stranga perpendicular pe directie, D = dreapta perpendicular pe directie |

Modul curent este afisat intr-un badge in coltul stanga sus al terenului.

---

## Control cu tastatura

### Deplasare si rotatie

| Tasta | Actiune |
|---|---|
| `W` | Inainte (directia robotului in mod Robot / sus in mod Field) |
| `S` | Inapoi (directia robotului in mod Robot / jos in mod Field) |
| `A` | Strafe stanga (mod Robot) / Stanga pe lume (mod Field) |
| `D` | Strafe dreapta (mod Robot) / Dreapta pe lume (mod Field) |
| `←` (sagata stanga) | Roteste robotul in sens antiorar |
| `→` (sagata dreapta) | Roteste robotul in sens orar |

### Actiuni

| Tasta | Actiune |
|---|---|
| `E` | Porneste / opreste intakes-ul (ridicare continua). Cand e pornit, robotul ridica automat artefactele din fata lui |
| `Q` | Lanseaza TOATE artefactele detinute spre gol (oricate ar avea) |
| `R` | Comuteaza modul de deplasare (Robot / Field) |
| `T` | Deschide / inchide poarta ( trebuie sa fii in raza de actiune a portii ) |

### Controle meci

| Tasta | Actiune |
|---|---|
| `F5` | Reseteaza jocul (opreste totul, repune artefactele) |
| `F6` | Porneste cronometrul (doar cand e oprit) |
| `ESC` | Pauza / Resume |
| `F10` | Iesire din joc |

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
| `B` (butonul 1) | Comuteaza modul de deplasare (Robot / Field) |
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

- La sfarsitul meciului, parca robotul in **zona de baza** (patratul din coltul stanga-jos al terenului, la 100px de margini)
- Robotul complet inauntru → +10 puncte
- Robotul partial in zona → +5 puncte
- Robotul in afara → 0 puncte

### Faza Endgame

- In ultimele **20 de secunde**, faza trece la **ENDGAME** (text portocaliu clipitor)
- La 0 secunde, meciul se termina si apare ecranul cu scorul final

### Pauza si reset

- `ESC` (tastatura) / `Y` (controler) — pune pe pauza / reia cronometrul
- Cand cronometrul e oprit, robotul **nu se misca** si nu poate interactiona
- `F5` (tastatura) / `Back` (controler) — reseteaza intregul joc (teren, artefacte, scor)
- `F10` — iesire din joc

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
