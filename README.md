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
5. **Stores:** Saves input-output to JSON for future reuse.

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

---

## 🗃️ Project Structure

