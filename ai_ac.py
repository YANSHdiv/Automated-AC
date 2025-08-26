import tkinter as tk
from tkinter import ttk, messagebox
import random
import json
import requests
import os
from ic.client import Client;
from ic.identity import Identity;
from ic.candid import Types, encode, decode

client = Client()
identity = Identity()

CANISTER_ID = "uxrrr-q7777-77774-qaaaq-cai"   # deployed ID
IC_GATEWAY = "http://127.0.0.1:4943"     # mainnet; uses "http://127.0.0.1:4943" for local dfx
InputType = Types.Record({
    "room_temp": Types.Float64,
    "humidity": Types.Float64,
    "num_people": Types.Nat,
    "movement": Types.Text,
    "timing": Types.Text,
})

OutputType = Types.Record({
    "Room_Temp": Types.Float64,
    "Humidity": Types.Float64,
    "Suggested_AC_Temp": Types.Float64,
    "Mode": Types.Text,
    "Fan_Speed": Types.Text,
    "Flap_Direction": Types.Text,
    "Estimated_Units_per_day": Types.Float64,
})

MemoryEntryType = Types.Record({
    "input": InputType,
    "output": OutputType,
})


class ACReflexAgent:
    def __init__(self, user_data):
        self.data = user_data
        self.memory = []  # to store past experiences

    def save_memory(self, new_entry):
        try:
            print("Saving to canister:", new_entry)
            encoded = encode([MemoryEntryType], [new_entry])
            client.call(CANISTER_ID, "saveMemory", encoded, identity)

        except Exception as e:
            print("Error saving memory to Motoko canister:", e)


    def load_memory(self):
        try:
            raw = client.query(CANISTER_ID, "loadMemory", [])
            decoded = decode([Types.Vec(MemoryEntryType)], raw)
            return decoded[0] if decoded else []
        except Exception as e:
            print("Error loading memory from Motoko canister:", e)
            return []


    def decide(self):
        # generate random room temp & humidity
        room_temp = round(random.uniform(22, 45), 1)
        humidity = round(random.uniform(30, 70), 1)


        # for motoko canister
        current_input = {
            'room_temp': room_temp,
            'humidity': humidity,
            'num_people': int(self.data['num_people']),
            'movement': self.data['movement'],
            'timing': self.data['timing']
        }

        similar = self.find_similar(current_input)
        if similar:
            print("Using past experience")
            return similar['output']

        # AC temp decision
        if room_temp >= 38:
            ac_temp = 18
        elif room_temp >= 32:
            ac_temp = 20
        elif room_temp >= 28:
            ac_temp = 22
        else:
            ac_temp = 24

        # Humidity check
        if humidity > 60:
            mode = "Dry Mode"
        else:
            mode = "Cool Mode"

        # Eco Mode if zero people
        if int(self.data['num_people']) == 0:
            mode = "Eco Mode"
            fan_speed = "Low"

        # Sleep Mode logic
        if self.data['movement'] == "No":
            hour = int(self.data['timing'].split(":")[0])
            if (hour >= 21 or hour < 6):
                mode = "Sleep Mode"
                ac_temp += 2

        # Fan speed
        num_people = int(self.data['num_people'])
        if num_people >= 4 or room_temp > 35:
            fan_speed = "High"
        elif num_people >= 2:
            fan_speed = "Medium"
        else:
            fan_speed = "Low"

        # get positions
        positions = [p.strip() for p in self.data['position'].split(',')]

        # flap direction
        if len(positions) > 1:
            flap_direction = "Rotate"
        else:
            pos = positions[0]
            hour = int(pos.replace('o', ''))

            if hour == 12:
                flap_direction = "Middle"
            elif 10 <= hour <= 11:
                flap_direction = "Left"
            elif 1 <= hour <= 2:
                flap_direction = "Right"
            else:
                # for other angles
                flap_direction = "Middle"


        # combo(AC type & Compressor type) power consumption
        combo_base_units = {
            ("Split AC", "Inverter Rotary Compressor"): 10,
            ("Cassette AC", "Inverter Rotary Compressor"): 11,
            ("Split AC", "Scroll Compressor"): 11,
            ("Cassette AC", "Scroll Compressor"): 12,
            ("Window AC", "Scroll Compressor"): 13,
            ("Window AC", "Reciprocating Compressor"): 14,
            ("Portable AC", "Fixed Speed Rotary Compressor"): 15
        }

        combo_key = (self.data['ac_type'], self.data['compressor_options'])
        base_combo_units = combo_base_units.get(combo_key, 12)  # fallback if combo missing, 12kwh as reasonable average


        # inputs
        tonnage = float(self.data['tonnage'])
        iseer = float(self.data['iseer'])
        external_heat = float(self.data['external_heat'])
        room_area = float(self.data['room_size'])
        affordable_units = float(self.data['affordable_units'])

        # calculation of cooling load
        area_cooling_kw = room_area * 0.04  # simple estimate: 0.04 kW per sq ft

        cooling_load_kw = tonnage * 3.5 + external_heat / 1000 + area_cooling_kw
        hourly_consumption = cooling_load_kw / iseer
        estimated_units = hourly_consumption * 8  # assume 8 hr/day

        # Add combo in cooling load unit
        total_daily_units = estimated_units + base_combo_units
        total_hourly_consumption = total_daily_units / 8

        print(f"Standard daily estimate: {estimated_units:.2f} kWh")
        print(f"Combo base addition: {base_combo_units} kWh")
        print(f"Final total daily units: {total_daily_units:.2f} kWh")
        print(f"Final hourly consumption: {total_hourly_consumption:.2f} kWh")

        # adjustment if over budget
        adjustments = 0
        while estimated_units > affordable_units and adjustments < 2:
            ac_temp += 1  # raise temp to reduce load
            mode = "Eco Mode" 
            fan_speed = "Low"
            # reduce tonnage effect to simulate less cooling demand
            cooling_load_kw = tonnage * 3.2 + external_heat / 1000 + area_cooling_kw
            hourly_consumption = cooling_load_kw / iseer
            estimated_units = hourly_consumption * 8
            adjustments += 1

        if estimated_units > float(self.data['affordable_units']):
            ac_temp += 1
            mode = "Eco Mode" 
            fan_speed = "Low"

        # for motoko canister
        entry = {
            "input": current_input,
            "output": {
                "Room_Temp": room_temp,
                "Humidity": humidity,
                "Suggested_AC_Temp": round(ac_temp, 1),
                "Mode": mode,
                "Fan_Speed": fan_speed,
                "Flap_Direction": flap_direction,
                "Estimated_Units_per_day": round(estimated_units, 2)
            }
        }

        self.save_to_canister(entry)   


        return {
            "Room Temp": room_temp,
            "Humidity": humidity,
            "Suggested AC Temp": round(ac_temp, 1),
            "Mode": mode,
            "Fan Speed": fan_speed,
            "Flap Direction": flap_direction,
            "Estimated Units/day": round(estimated_units, 2)
        }
    
    def find_similar(self, current_input):
        # Ask Motoko canister directly
        return self.query_canister(current_input)
    
    def save_to_canister(self, entry):
        url = f"{IC_GATEWAY}/api/v2/canister/{CANISTER_ID}/call/saveMemory"
        try:
            requests.post(url, json={"entry": entry})
        except Exception as e:
            print("Error saving to Motoko canister:", e)

    def query_canister(self, current_input):
        url = f"{IC_GATEWAY}/api/v2/canister/{CANISTER_ID}/query/findSimilar"
        try:
            resp = requests.post(url, json={"current": current_input})
            try:
                data = resp.json()
            except ValueError:
                print("Received invalid or empty response from canister.")
                return None
            return data
        except Exception as e:
            print("Error querying Motoko canister:", e)
            return None

    # ------------for Goal based---------------
    def plan_to_goal(self, current_input):
        """
        Simple Goal-based plan.
        Goal: Keep temp comfy & efficient.
        """
        room_temp = current_input['room_temp']
        humidity = current_input['humidity']

        # Goal to keep AC temp between 22–26
        if room_temp > 30:
            ac_temp = 22
        else:
            ac_temp = 24

        if humidity > 60:
            mode = "Dry Mode"
        else:
            mode = "Cool Mode"

        plan = {
            "Room Temp": room_temp,
            "Humidity": humidity,
            "Planned AC Temp": ac_temp,
            "Mode": mode,
            "Goal": "Keep comfort and efficiency"
        }

        return plan

# memeory review for Goal based 
def find_similar(self, current_input):
        memory = self.load_memory()
        for entry in memory:
            past_input = entry['input']   # <- This pulls the saved input
            if abs(past_input['room_temp'] - current_input['room_temp']) <= 1.0 \
            and abs(past_input['humidity'] - current_input['humidity']) <= 5 \
            and past_input['num_people'] == current_input['num_people'] \
            and past_input['movement'] == current_input['movement'] \
            and past_input['timing'].split(":")[0] == current_input['timing'].split(":")[0]:
                return entry['output']
        return None
    
class SmartACInputTab:
    def __init__(self, master):
        self.master = master
        master.title("Smart AC")

        # AC type Radiobuttons
        tk.Label(master, text="Type of AC:").grid(row=0, column=0, sticky="w")
        self.ac_type_var = tk.StringVar(value="0")  
        ac_types = ["Window AC", "Split AC", "Cassette AC", "Portable AC"]
        for idx, ac_type in enumerate(ac_types):
            tk.Radiobutton(master, text=ac_type, variable=self.ac_type_var, value=ac_type).grid(row=0, column=idx+1)

        # Tonnage Combobox
        tk.Label(master, text="AC Tonnage:").grid(row=1, column=0, sticky="w")
        self.tonnage_var = tk.StringVar()
        tonnage_options = ["0.8", "1.0", "1.4", "1.5", "1.6", "1.7", "1.8",
                           "2.0", "2.1", "2.2", "2.5", "3.0", "3.2", "3.4", "3.5", "4.0"]
        self.tonnage_cb = ttk.Combobox(master, textvariable=self.tonnage_var, values=tonnage_options, state="readonly", width=25)
        self.tonnage_cb.grid(row=1, column=1, padx=10)

        # ISEER Rating entry
        tk.Label(master, text="ISEER Rating (e.g., 3.9):").grid(row=2, column=0, sticky="w")
        self.iseer_entry = tk.Entry(master, width=28)
        self.iseer_entry.grid(row=2, column=1)

        # cooling capacity entry
        tk.Label(master, text="Cooling Capacity (100%):").grid(row=3, column=0, sticky="w")
        self.cooling_entry = tk.Entry(master, width=28)
        self.cooling_entry.grid(row=3, column=1)

        # last service Radiobuttons
        tk.Label(master, text="Last Service:").grid(row=4, column=0, sticky="w")
        self.service_var = tk.StringVar(value="0") 
        service_options = ["6 months", "12 months", "More"]
        for idx, option in enumerate(service_options):
            tk.Radiobutton(master, text=option, variable=self.service_var, value=option).grid(row=4, column=idx+1)

        # Compressor type Combobox
        tk.Label(master, text="Compressor Type:").grid(row=5, column=0, sticky="w")
        self.compressor_var = tk.StringVar()
        compressor_options = [
            "Reciprocating compressor",
            "Inverter rotary compressor",
            "Fixed speed rotary compressor",
            "Scroll compressor"
        ]
        self.compressor_cb = ttk.Combobox(master, textvariable=self.compressor_var, values=compressor_options, state="readonly", width=25)
        self.compressor_cb.grid(row=5, column=1)

        # next button
        tk.Button(master, text="Next", command=self.next).grid(row=6, column=1, pady=10)

    # Error handling 
    def next(self):
        try:
            iseer = float(self.iseer_entry.get())
            cooling_capacity = float(self.cooling_entry.get())

            if not self.ac_type_var.get():
                raise ValueError("Select AC type.")
            if not self.tonnage_var.get():
                raise ValueError("Select AC tonnage.")
            if not self.service_var.get():
                raise ValueError("Select last service.")
            if not self.compressor_var.get():
                raise ValueError("Select compressor type.")

            # open next page
            self.open_next_page()

        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except:
            messagebox.showerror("Input Error", "ISEER and Cooling Capacity must be numbers.")

    # ------------Next page inputs---------------

    def open_next_page(self):
        next_window = tk.Toplevel(self.master)
        next_window.title("Room & Energy Details")

        tk.Label(next_window, text="Room Size (sq ft):").grid(row=3, column=0, sticky="w")
        self.roomsize_entry = tk.Entry(next_window, width=28)
        self.roomsize_entry.grid(row=3, column=1)

        tk.Label(next_window, text="Number of People:").grid(row=0, column=0, sticky="w")
        self.people_entry = tk.Entry(next_window, width=28)
        self.people_entry.grid(row=0, column=1)

        tk.Label(next_window, text="Other Source of Heat (Watt):").grid(row=1, column=0, sticky="w")
        self.heat_entry = tk.Entry(next_window, width=28)
        self.heat_entry.grid(row=1, column=1)

        tk.Label(next_window, text="Energy limitation(units/kWh):").grid(row=2, column=0, sticky="w")
        self.energy_entry = tk.Entry(next_window, width=28)
        self.energy_entry.grid(row=2, column=1,padx=10)

        tk.Label(next_window, text="Person Movement:").grid(row=4, column=0, sticky="w")
        self.movement_var = tk.StringVar(value="0")  # empty so none selected by default
        tk.Radiobutton(next_window, text="Yes", variable=self.movement_var, value="Yes").grid(row=4, column=1, sticky="w")
        tk.Radiobutton(next_window, text="No", variable=self.movement_var, value="No").grid(row=4, column=2, sticky="w")

        tk.Label(next_window, text="Timing (24hr format):").grid(row=5, column=0, sticky="w")
        self.timing_entry = tk.Entry(next_window, width=28)
        self.timing_entry.grid(row=5, column=1)

        tk.Label(next_window, text="Position of Person (in clock e.g., 11o, 12o):").grid(row=6, column=0, sticky="w")
        self.position_entry = tk.Entry(next_window, width=28)
        self.position_entry.grid(row=6, column=1)


        tk.Button(next_window, text="Submit", command=self.submit_next_page).grid(row=7, column=1, pady=10)

    # Error handling
    def submit_next_page(self):
        try:
            num_people = int(self.people_entry.get())
            other_heat = float(self.heat_entry.get())
            total_energy = float(self.energy_entry.get())
            room_size = float(self.roomsize_entry.get())

            movement = self.movement_var.get()
            if not movement:
                raise ValueError("Please select Yes or No for Person Movement.")

            timing = self.timing_entry.get().strip()
            position = self.position_entry.get().strip()

            # Basic format checks
            if ":" not in timing or len(timing.split(":")) != 2:
                raise ValueError("Timing must be in 24hr format, e.g., 13:30")

            if not position.endswith("o"):
                raise ValueError("Position should be in clock format like '11o'.")

            # Store for your agent
            print(f"Number of People: {num_people}")
            print(f"Other Heat Source: {other_heat} W")
            print(f"Total Energy You Can Afford: {total_energy} units")
            print(f"Room Size: {room_size} sq ft")
            print(f"Person Movement: {movement}")
            print(f"Timing: {timing}")
            print(f"Position: {position}")

            self.num_people = num_people
            self.other_heat = other_heat
            self.total_energy = total_energy
            self.room_size = room_size
            self.movement = movement
            self.timing = timing
            self.position = position


        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except:
            messagebox.showerror("Input Error", "Please enter valid data in all fields.")
       
    # Build user_data dictionary for the agent
        self.user_data = {
            "ac_type": self.ac_type_var.get(),
            "tonnage": self.tonnage_var.get(),
            "iseer": float(self.iseer_entry.get()),
            "cooling_capacity": float(self.cooling_entry.get()),
            "service": self.service_var.get(),
            "compressor": self.compressor_var.get(),
            "room_size": float(self.roomsize_entry.get()),
            "num_people": num_people,
            "external_heat": other_heat,
            "affordable_units": total_energy,
            "movement": movement,
            "timing": timing,
            "position": position,
            "compressor_options":self.compressor_var.get()
        }

        # Run the agent
        agent = ACReflexAgent(self.user_data)
        result = agent.decide()
        previous_data = agent.load_memory()[:-1]  # Exclude the just-added result if needed

        # shows results in popup 
        result_text = f"""
        Room Temp: {result['Room Temp']} °C
        Humidity: {result['Humidity']}%
        Suggested AC Temp: {result['Suggested AC Temp']} °C
        Mode: {result['Mode']}
        Fan Speed: {result['Fan Speed']}
        Flap Direction: {result['Flap Direction']}
        Estimated Units/day: {result['Estimated Units/day']} kWh
        """
        messagebox.showinfo("AC Reflex Agent Result", result_text)

        # prepare previous data text
        prev_text = ""
        for entry in previous_data:
            prev_text += f"INPUT: {entry['input']}\nOUTPUT: {entry['output']}\n\n"

        # New popup output/result
        new_text = f"""
        Room Temp: {result['Room Temp']} °C
        Humidity: {result['Humidity']}%
        Suggested AC Temp: {result['Suggested AC Temp']} °C
        Mode: {result['Mode']}
        Fan Speed: {result['Fan Speed']}
        Flap Direction: {result['Flap Direction']}
        Estimated Units/day: {result['Estimated Units/day']} kWh
        """

        # Creates a new window with 2 text areas side by side
        split_window = tk.Toplevel(self.master)
        split_window.title("Goal-Based Agent Comparison")

        left = tk.Text(split_window, width=60, height=30)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left.insert(tk.END, f"--- PREVIOUS DATA ---\n\n{prev_text}")

        right = tk.Text(split_window, width=60, height=30)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        right.insert(tk.END, f"--- NEW OUTPUT ---\n\n{new_text}")



if __name__ == "__main__":
    root = tk.Tk()
    app = SmartACInputTab(root)
    root.mainloop()
