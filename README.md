# 🌬️ Automated AC

An intelligent **Tkinter GUI** app that works on different **agents** to suggest optimal AC settings based on your room conditions, preferences, and energy limits. It remembers similar situations, estimates energy use, and even plans for comfort & efficiency!

---

## 📌 Features

✅ User-friendly GUI with **Tkinter**  
✅ Random simulation of **room temperature & humidity**  
✅ Memory-based reuse of past scenarios (reflex agent)  
✅ Goal-based planning for comfort & energy savings  
✅ Estimates **hourly & daily energy consumption**  
✅ Handles AC type, tonnage, compressor, ISEER, room size, people, heat, movement, timing, position  
✅ Shows **previous vs. new output** side-by-side  
✅ Stores all data in motoko canister.

---

## 🧠 How it Works

1. **Inputs:** You enter AC specs, room details, people count, heat sources, energy limit, and more.
2. **Simulation:** Generates random room temp & humidity.
3. **Decision Logic:**  
   - Suggests AC temp based on thresholds.
   - Adjusts mode (Cool, Dry, Eco, Sleep).
   - Sets fan speed & flap direction.
   - Compares with past scenarios for reuse.
   - Adjusts if estimated energy exceeds your budget.
4. **Output:** Displays suggestions & energy use estimate.

---

## 🔑 Conditions & Information Used

- **AC Type:** Window, Split, Cassette, Portable
- **Tonnage:** 0.8 to 4.0 tons
- **ISEER:** User input
- **Compressor Type:** Reciprocating, Inverter Rotary, Fixed Speed Rotary, Scroll
- **Room Size, Number of People, External Heat**
- **Affordable Units:** Units/day limit
- **Person Movement:** Yes/No
- **Timing:** 24-hour format
- **Position:** Clock angle (e.g., 11o)

**Decision Rules Include:**
- Room temp ≥ 38°C → AC temp = 18°C  
- Humidity > 60% → Dry Mode  
- Zero people → Eco Mode  
- No movement at night → Sleep Mode  
- People count & temp decide fan speed  
- Clock position decides flap direction  
- Base combo units adjust total energy estimate  
- If units > budget, adjust AC temp & mode to save energy

**⚙️ 6. Base Unit Consumption Logic (AC Type + Compressor Type)**

This logic adds a base energy consumption value depending on the AC + compressor combo:

-Split AC + Inverter Rotary Compressor → 10 kWh/day

-Cassette AC + Inverter Rotary Compressor → 11 kWh/day

-Split AC + Scroll Compressor → 11 kWh/day

-Cassette AC + Scroll Compressor → 12 kWh/day

-Window AC + Scroll Compressor → 13 kWh/day

-Window AC + Reciprocating Compressor → 14 kWh/day

-Portable AC + Fixed Speed Rotary Compressor → 15 kWh/day

-Explanation: Different hardware combinations consume different base power.
 


*Many of the logics are used instead of a hardware sensor.

---

## Setup

Use Linux for ease (due to Motoko) or in Window run by WSL.

### Create Virtual Environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```
### Install Dependencies
```bash
pip install -r requirements.txt
tkinter
requests
```
⚠️ tkinter usually comes pre-installed with Python. If not, install via system package manager (e.g., sudo apt-get install python3-tk).
### Running the Project
```bash
python gui.py
```
Once launched, enter room & AC details, then get recommended AC settings instantly.
