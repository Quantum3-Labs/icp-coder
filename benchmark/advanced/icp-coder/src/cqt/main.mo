import HashMap "mo:base/HashMap";
import Principal "mo:base/Principal";
import Time "mo:base/Time";
import Int "mo:base/Int";
import Nat32 "mo:base/Nat32";
import Iter "mo:base/Iter";
import Array "mo:base/Array";
import Nat8 "mo:base/Nat8";
import Blob "mo:base/Blob";

persistent actor class CQT(initOwner : Principal) {
    // State
    transient var balances : HashMap.HashMap<Principal, Nat> = HashMap.HashMap<Principal, Nat>(10, Principal.equal, Principal.hash);
    stable var totalSupplyVar : Nat = 0;
    stable var owner : Principal = initOwner;
    stable var nonce : Nat = 0;

    // Constants
    transient let NAME : Text = "CQT";
    transient let SYMBOL : Text = "CQT";
    transient let DECIMALS : Nat8 = 8;
    transient let PRIZE_AMOUNT : Nat = 100;
    

    public query func name() : async Text { NAME };
    public query func symbol() : async Text { SYMBOL };
    public query func decimals() : async Nat8 { DECIMALS };
    public query func totalSupply() : async Nat { totalSupplyVar };

    public query func balanceOf(who : Principal) : async Nat {
        switch (balances.get(who)) { case (?b) b; case null 0 };
    };

    public shared ({ caller }) func transfer(to : Principal, amount : Nat) : async Bool {
        if (amount == 0) { return true };
        let fromBalance = switch (balances.get(caller)) { case (?b) b; case null 0 };
        if (fromBalance < amount) { return false };
        balances.put(caller, fromBalance - amount);
        let toBal = switch (balances.get(to)) { case (?b) b; case null 0 };
        balances.put(to, toBal + amount);
        true
    };

    public shared ({ caller }) func mint(to : Principal, amount : Nat) : async Bool {
        if (caller != owner) { return false };
        if (amount == 0) { return true };
        totalSupplyVar := totalSupplyVar + amount;
        let toBal = switch (balances.get(to)) { case (?b) b; case null 0 };
        balances.put(to, toBal + amount);
        true
    };

    // Management canister interface for raw_rand
    actor type IC = actor { raw_rand : () -> async blob };
    let ic : IC = actor "aaaaa-aa";

    public shared ({ caller }) func randomNat(maxExclusive : Nat) : async Nat {
        assert(maxExclusive > 0);
        // Try cryptographic randomness first
        try {
            let randomBlob = await ic.raw_rand();
            let bytes = Blob.toArray(randomBlob);
            var acc : Nat = 0;
            for (byte in bytes.vals()) {
                acc := (acc << 8) + Nat8.toNat(byte);
            };
            return acc % maxExclusive;
        } catch (_) {
            // Fallback deterministic PRNG for local/dev
            nonce := nonce + 1;
            let t : Nat = Int.abs(Time.now());
            let callerHash : Nat = Nat32.toNat(Principal.hash(caller));
            let seed : Nat = t + nonce + callerHash;
            return seed % maxExclusive;
        };
    };

    public shared ({ caller }) func guessAndWin(guess : Nat, maxExclusive : Nat) : async { roll : Nat; won : Bool; prize : Nat } {
        assert(maxExclusive > 0);
        assert(guess < maxExclusive);
        let roll = await randomNat(maxExclusive);
        if (roll == guess) {
            ignore await mint(caller, PRIZE_AMOUNT);
            { roll = roll; won = true; prize = PRIZE_AMOUNT }
        } else {
            { roll = roll; won = false; prize = 0 }
        }
    };

    // Stable upgrade hooks
    stable var _savedBalances : [(Principal, Nat)] = [];
    stable var _savedTotal : Nat = 0;
    stable var _savedOwner : Principal = owner;
    stable var _savedNonce : Nat = 0;

    system func preupgrade() {
        _savedBalances := Iter.toArray(balances.entries());
        _savedTotal := totalSupplyVar;
        _savedOwner := owner;
        _savedNonce := nonce;
    };

    system func postupgrade() {
        balances := HashMap.HashMap<Principal, Nat>(10, Principal.equal, Principal.hash);
        for (entry in Array.vals(_savedBalances)) {
            let (p, b) = entry;
            balances.put(p, b);
        };
        totalSupplyVar := _savedTotal;
        owner := _savedOwner;
        nonce := _savedNonce;
    };
}


