import HashMap "mo:base/HashMap";
import Nat "mo:base/Nat";
import Nat8 "mo:base/Nat8";
import Principal "mo:base/Principal";
import Random "mo:base/Random";
import Text "mo:base/Text";
import Blob "mo:base/Blob";
import Nat64 "mo:base/Nat64";

actor {
  // --- Token metadata ---
  public query func name() : async Text { "CQT" };
  public query func symbol() : async Text { "CQT" };
  public query func decimals() : async Nat8 { 8 : Nat8 };

  // --- Ownership ---
  transient var owner : Principal = Principal.fromText("2vxsx-fae");
  public shared ({ caller }) func init() : async () {
    owner := caller;
  };

  // --- State ---
  transient var totalSupply_ : Nat = 0;
  transient let balances = HashMap.HashMap<Principal, Nat>(
    0,
    Principal.equal,
    Principal.hash,
  );

  // --- Views ---
  public query func totalSupply() : async Nat { totalSupply_ };

  public query func balanceOf(account : Principal) : async Nat {
    switch (balances.get(account)) {
      case (?b) b;
      case null 0;
    }
  };

  // --- Internal helpers ---
  func credit(to : Principal, amount : Nat) {
    let current = switch (balances.get(to)) { case (?b) b; case null 0 };
    balances.put(to, current + amount);
    totalSupply_ += amount;
  };

  func debit(from : Principal, amount : Nat) : Bool {
    let current = switch (balances.get(from)) { case (?b) b; case null 0 };
    if (current < amount) { return false };
    balances.put(from, current - amount);
    return true;
  };

  // --- Token actions ---
  public shared ({ caller }) func mint(to : Principal, amount : Nat) : async Bool {
    // For this demo token, allow anyone to mint.
    credit(to, amount);
    true
  };

  public shared ({ caller }) func transfer(to : Principal, amount : Nat) : async Bool {
    let from = caller;
    if (not debit(from, amount)) { return false };
    let toBal = switch (balances.get(to)) { case (?b) b; case null 0 };
    balances.put(to, toBal + amount);
    true
  };

  // --- Randomness ---
  // Returns a random number in [0, maxExclusive). If maxExclusive == 0, returns 0.
  public func generateRandomNumber(maxExclusive : Nat) : async Nat {
    if (maxExclusive == 0) { return 0 };
    let entropy = await Random.blob();
    let bytes = Blob.toArray(entropy);
    var acc : Nat64 = 0;
    let take : Nat = if (bytes.size() < 8) { bytes.size() } else { 8 };
    var i : Nat = 0;
    while (i < take) {
      acc := (acc << 8) | Nat64.fromNat(Nat8.toNat(bytes[i]));
      i += 1;
    };
    let n = Nat64.toNat(acc);
    n % maxExclusive
  };

  // --- Guess-to-win game ---
  // User provides a guess in [0, maxExclusive). If equals winning number, user wins reward tokens.
  public shared ({ caller }) func guessToWin(guess : Nat, maxExclusive : Nat) : async {
    won : Bool;
    winningNumber : Nat;
  } {
    if (maxExclusive == 0) {
      return { won = false; winningNumber = 0 };
    };
    if (guess >= maxExclusive) {
      return { won = false; winningNumber = 0 };
    };
    let winning = await generateRandomNumber(maxExclusive);
    if (guess == winning) {
      let reward : Nat = 10; // prize amount
      credit(caller, reward);
      return { won = true; winningNumber = winning };
    } else {
      return { won = false; winningNumber = winning };
    }
  };
};
