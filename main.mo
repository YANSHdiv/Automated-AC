import Nat "mo:base/Nat";
import Text "mo:base/Text";
import Array "mo:base/Array";
import Float "mo:base/Float";

actor ACReflexAgent {

  public type Input = {
    room_temp : Float;
    humidity : Float;
    num_people : Nat;
    movement : Text;
    timing : Text;
  };

  public type Output = {
    Room_Temp : Float;
    Humidity : Float;
    Suggested_AC_Temp : Float;
    Mode : Text;
    Fan_Speed : Text;
    Flap_Direction : Text;
    Estimated_Units_per_day : Float;
  };

  public type MemoryEntry = {
    input : Input;
    output : Output;
  };

  stable var memory : [MemoryEntry] = [];

  public func saveMemory(entry : MemoryEntry) : async () {
    memory := Array.append(memory, [entry]);
  };

  public query func loadMemory() : async [MemoryEntry] {
    return memory;
  };

  public query func findSimilar(current : Input) : async ?MemoryEntry {
    for (entry in memory.vals()) {
      if (
        Float.abs(entry.input.room_temp - current.room_temp) <= 1.0
        and Float.abs(entry.input.humidity - current.humidity) <= 5.0
        and entry.input.num_people == current.num_people
        and entry.input.movement == current.movement
        and Text.split(entry.input.timing, ":")[0] == Text.split(current.timing, ":")[0]
      ) {
        return ?entry;
      };
    };
    return null;
  };
};
