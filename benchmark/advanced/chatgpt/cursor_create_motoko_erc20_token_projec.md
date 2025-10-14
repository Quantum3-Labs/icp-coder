# Create Motoko Fungible Token project

_Exported on 9/21/2025 at 15:14:21 GMT+7 from Cursor (1.6.27)_

---

**User**

Create a Motoko project using dfx tool to build an fungible token project, write a readme on how to run
create a token with name CQT
Function:
transfer, mint
Create random number
generate random number function, if match user win some token

---

**Cursor**

I'll scaffold a DFX Motoko project, implement an fungible token canister named CQT with transfer, mint, and a randomness-based game, and add a README with run instructions. Creating the todo list and then adding the necessary files.

I'll fetch the correct Motoko randomness API usage to implement a secure random number generator, then scaffold the DFX project and implement the token and game.

I'll quickly verify the correct Motoko Random API usage, then scaffold the project and implement the canister and README.

I'll scaffold the DFX Motoko project in your workspace, then implement the CQT token canister with transfer, mint, randomness, and the guess-to-win game, and finally write the README.

I'll create the DFX project scaffold and set up the Motoko canister.

I'll open the new project's files to update `dfx.json` and implement the Motoko canister, then add a README.

I'll implement the token canister with transfer, mint, randomness, and the guess-to-win function, then update the README.

Starting the token implementation. I'll edit the Motoko canister to add CQT token, transfer, mint, balance, and randomness/game functions.

I'll implement the token and game logic in `main.mo`, then build and deploy locally to verify everything compiles.

```motoko
import HashMap "mo:base/HashMap";
import Nat "mo:base/Nat";
import Nat8 "mo:base/Nat8";
import Principal "mo:base/Principal";
import Random "mo:base/Random";
import Text "mo:base/Text";

actor {
  // --- Token metadata ---
  public query func name() : async Text { "CQT" };
  public query func symbol() : async Text { "CQT" };
  public query func decimals() : async Nat8 { 8 };

  // --- Ownership ---
  stable var owner : Principal = Principal.fromText("2vxsx-fae");
  system func init() {
    owner := msg.caller;
  };

  // --- State ---
  var totalSupply_ : Nat = 0;
  let balances = HashMap.HashMap<Principal, Nat>(
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
  public func mint(to : Principal, amount : Nat) : async Bool {
    if (msg.caller != owner) { return false };
    credit(to, amount);
    true
  };

  public func transfer(to : Principal, amount : Nat) : async Bool {
    let from = msg.caller;
    if (!debit(from, amount)) { return false };
    let toBal = switch (balances.get(to)) { case (?b) b; case null 0 };
    balances.put(to, toBal + amount);
    true
  };

  // --- Randomness ---
  // Returns a random number in [0, maxExclusive). If maxExclusive == 0, returns 0.
  public func generateRandomNumber(maxExclusive : Nat) : async Nat {
    if (maxExclusive == 0) { return 0 };
    let entropy = await Random.blob();
    let rng = Random.Finite(entropy);
    switch (rng.range(maxExclusive)) {
      case (?n) n;
      case null 0; // Fallback, should not normally happen
    }
  };

  // --- Guess-to-win game ---
  // User provides a guess in [0, maxExclusive). If equals winning number, user wins reward tokens.
  public func guessToWin(guess : Nat, maxExclusive : Nat) : async {
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
      credit(msg.caller, reward);
      return { won = true; winningNumber = winning };
    } else {
      return { won = false; winningNumber = winning };
    }
  };
};

```

I updated the todo to mark scaffolding complete and I'm about to fix compilation errors by updating the Motoko canister: use shared functions with caller instead of msg, correct init signature, annotate `decimals` return type, and mark state as transient/stable as needed. Then I'll build to verify.

```motoko
import HashMap "mo:base/HashMap";
import Nat "mo:base/Nat";
import Nat8 "mo:base/Nat8";
import Principal "mo:base/Principal";
import Random "mo:base/Random";
import Text "mo:base/Text";

actor {
  // --- Token metadata ---
  public query func name() : async Text { "CQT" };
  public query func symbol() : async Text { "CQT" };
  public query func decimals() : async Nat8 { 8 : Nat8 };

  // --- Ownership ---
  stable var owner : Principal = Principal.fromText("2vxsx-fae");
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
    if (caller != owner) { return false };
    credit(to, amount);
    true
  };

  public shared ({ caller }) func transfer(to : Principal, amount : Nat) : async Bool {
    let from = caller;
    if (!debit(from, amount)) { return false };
    let toBal = switch (balances.get(to)) { case (?b) b; case null 0 };
    balances.put(to, toBal + amount);
    true
  };

  // --- Randomness ---
  // Returns a random number in [0, maxExclusive). If maxExclusive == 0, returns 0.
  public func generateRandomNumber(maxExclusive : Nat) : async Nat {
    if (maxExclusive == 0) { return 0 };
    let entropy = await Random.blob();
    let rng = Random.Finite(entropy);
    switch (rng.range(maxExclusive)) {
      case (?n) n;
      case null 0; // Fallback, should not normally happen
    }
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

```

```motoko
import HashMap "mo:base/HashMap";
import Nat "mo:base/Nat";
import Nat8 "mo:base/Nat8";
import Principal "mo:base/Principal";
import Random "mo:base/Random";
import Text "mo:base/Text";

actor persistent {
  // --- Token metadata ---
  public query func name() : async Text { "CQT" };
  public query func symbol() : async Text { "CQT" };
  public query func decimals() : async Nat8 { 8 : Nat8 };

  // --- Ownership ---
  stable var owner : Principal = Principal.fromText("2vxsx-fae");
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
    if (caller != owner) { return false };
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
    let rng = Random.Finite(entropy);
    switch (rng.range(maxExclusive)) {
      case (?n) n;
      case null 0; // Fallback, should not normally happen
    }
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

```

```motoko
import HashMap "mo:base/HashMap";
import Nat "mo:base/Nat";
import Nat8 "mo:base/Nat8";
import Principal "mo:base/Principal";
import Random "mo:base/Random";
import Text "mo:base/Text";

actor {
  // --- Token metadata ---
  public query func name() : async Text { "CQT" };
  public query func symbol() : async Text { "CQT" };
  public query func decimals() : async Nat8 { 8 : Nat8 };

  // --- Ownership ---
  var owner : Principal = Principal.fromText("2vxsx-fae");
  public shared ({ caller }) func init() : async () {
    owner := caller;
  };

  // --- State ---
  var totalSupply_ : Nat = 0;
  let balances = HashMap.HashMap<Principal, Nat>(
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
    if (caller != owner) { return false };
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
    let rng = Random.Finite(entropy);
    switch (rng.range(maxExclusive)) {
      case (?n) n;
      case null 0; // Fallback, should not normally happen
    }
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

```

```motoko
import HashMap "mo:base/HashMap";
import Nat "mo:base/Nat";
import Nat8 "mo:base/Nat8";
import Principal "mo:base/Principal";
import Random "mo:base/Random";
import Text "mo:base/Text";

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
    if (caller != owner) { return false };
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
    let rng = Random.Finite(entropy);
    switch (rng.range(maxExclusive)) {
      case (?n) n;
      case null 0; // Fallback, should not normally happen
    }
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

```

```motoko
import HashMap "mo:base/HashMap";
import Nat "mo:base/Nat";
import Nat8 "mo:base/Nat8";
import Principal "mo:base/Principal";
import Random "mo:base/Random";
import Text "mo:base/Text";

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
    if (caller != owner) { return false };
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
    let rng = Random.Finite(entropy);
    switch (rng.range(Nat8.fromNat(maxExclusive))) {
      case (?n) n;
      case null 0; // Fallback, should not normally happen
    }
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

```

I'll build and deploy locally to validate the Motoko canister compiles and runs. If it compiles, I'll write a concise README with commands to mint, transfer, generate random number, and play the guess-to-win game.

```motoko
import HashMap "mo:base/HashMap";
import Nat "mo:base/Nat";
import Nat8 "mo:base/Nat8";
import Principal "mo:base/Principal";
import Random "mo:base/Random";
import Text "mo:base/Text";

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
    let rng = Random.Finite(entropy);
    switch (rng.range(Nat8.fromNat(maxExclusive))) {
      case (?n) n;
      case null 0; // Fallback, should not normally happen
    }
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

```

Deploying updated canister code to apply recent changes, then testing mint/transfer and the game functions.

I'll update the randomness implementation to produce a bounded number using raw entropy bytes, then test the random and game functions, and finally write the README.

```motoko
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

```

```markdown
# CQT Token (Motoko)

Fungible token Motoko canister implementing `CQT` with `mint`, `transfer`, balances, and a randomness-based guessing game that mints a reward on win.

## Prerequisites

- dfx 0.27.x
- macOS/Linux shell

## Quickstart

```bash
cd cqt_token
dfx start --background
dfx deploy
```

Check basic metadata:

```bash
dfx canister call cqt_token_backend name
dfx canister call cqt_token_backend symbol
dfx canister call cqt_token_backend decimals
dfx canister call cqt_token_backend totalSupply
```

## Identities

```bash
# current principal
dfx identity get-principal

# optional: create a second identity
dfx identity new bob --storage-mode=plaintext
dfx identity use bob
dfx identity get-principal
dfx identity use default
```

## Token functions

```bash
# Mint tokens (demo: open mint, anyone can mint)
ME=$(dfx identity get-principal)
dfx canister call cqt_token_backend mint "(principal \"$ME\", 1000:nat)"

# Check balances
dfx canister call cqt_token_backend balanceOf "(principal \"$ME\")"

# Transfer
BOB=$(dfx identity use bob >/dev/null; dfx identity get-principal; dfx identity use default >/dev/null;)
dfx canister call cqt_token_backend transfer "(principal \"$BOB\", 200:nat)"
dfx canister call cqt_token_backend balanceOf "(principal \"$BOB\")"
```

## Randomness and Game

```bash
# Generate bounded random number in [0, 100)
dfx canister call cqt_token_backend generateRandomNumber '(100:nat)'

# Guess-to-win: reward 10 CQT if guess matches winning number
dfx canister call cqt_token_backend guessToWin '(42:nat, 100:nat)'
```

Notes:

- Randomness uses the management canister `raw_rand` via `mo:base/Random.blob()` and derives a 64-bit value from returned bytes, then takes modulo bound.
- `mint` is intentionally unrestricted for demo; restrict in production.

## Files

- `src/cqt_token_backend/main.mo`: token and game logic
- `dfx.json`: canister config

```

I scaffolded and implemented the CQT token canister with transfer, mint, random number generation, and a guess-to-win function, deployed it locally, and added a README with usage.

- Project: `/Users/nobody1/Work/q3x/test_motoko/cqt_token`
- Key file: `src/cqt_token_backend/main.mo`
- README with commands: `cqt_token/README.md`

How to run (short):
- Start and deploy:
```bash
cd /Users/nobody1/Work/q3x/test_motoko/cqt_token
dfx start --background
dfx deploy
```

- Mint/transfer/check:

```bash
ME=$(dfx identity get-principal)
dfx canister call cqt_token_backend mint "(principal \"$ME\", 1000:nat)"
dfx canister call cqt_token_backend balanceOf "(principal \"$ME\")"
dfx identity new bob --storage-mode=plaintext
BOB=$(dfx identity use bob >/dev/null; dfx identity get-principal; dfx identity use default >/dev/null;)
dfx canister call cqt_token_backend transfer "(principal \"$BOB\", 200:nat)"
```

- Random/game:

```bash
dfx canister call cqt_token_backend generateRandomNumber '(100:nat)'
dfx canister call cqt_token_backend guessToWin '(42:nat, 100:nat)'
```

Status: all tasks complete.

```shellscript
cd /Users/nobody1/Work/q3x/test_motoko/cqt_token
dfx start --background
dfx deploy
```

```shellscript
ME=$(dfx identity get-principal)
dfx canister call cqt_token_backend mint "(principal \"$ME\", 1000:nat)"
dfx canister call cqt_token_backend balanceOf "(principal \"$ME\")"
dfx identity new bob --storage-mode=plaintext
BOB=$(dfx identity use bob >/dev/null; dfx identity get-principal; dfx identity use default >/dev/null;)
dfx canister call cqt_token_backend transfer "(principal \"$BOB\", 200:nat)"
```

```shellscript
dfx canister call cqt_token_backend generateRandomNumber '(100:nat)'
dfx canister call cqt_token_backend guessToWin '(42:nat, 100:nat)'
```
