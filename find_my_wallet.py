"""
TON Wallet Address Finder - Tonkeeper Compatible
Supports BOTH mnemonic types:
  - TON native mnemonics (tonsdk default)
  - BIP39 mnemonics (used by Tonkeeper, MyTonWallet)

Usage:
    pip install tonsdk mnemonic PyNaCl
    python find_my_wallet.py
"""

SENDER_MNEMONIC = "cash matrix behind engage hover shoulder include dove process bachelor body cousin lemon around kitten utility trend sunset arm swift host purity animal dose"  # <-- paste your 24-word seed phrase here

# ──────────────────────────────────────────────────────────────────────────────

import hashlib
import hmac
import struct

def bip39_mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """Standard BIP39: mnemonic -> 64-byte seed via PBKDF2."""
    mnemonic_bytes  = mnemonic.strip().encode("utf-8")
    salt            = ("mnemonic" + passphrase).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha512", mnemonic_bytes, salt, 2048)


def derive_ed25519_key_from_seed(seed: bytes) -> tuple:
    """
    Tonkeeper BIP39 path: m/44'/607'/0'
    Derives Ed25519 keypair following SLIP-0010 for Ed25519.
    """
    # SLIP-0010 master key derivation
    I  = hmac.new(b"ed25519 seed", seed, hashlib.sha512).digest()
    kL, kR = I[:32], I[32:]

    # Hardened child derivation helper
    def ckd_priv(kpar, cpar, index):
        data = b"\x00" + kpar + struct.pack(">I", 0x80000000 | index)
        I2   = hmac.new(cpar, data, hashlib.sha512).digest()
        return I2[:32], I2[32:]

    # Path: m / 44' / 607' / 0'
    for index in [44, 607, 0]:
        kL, kR = ckd_priv(kL, kR, index)

    # Generate public key from private key using PyNaCl
    import nacl.signing
    signing_key = nacl.signing.SigningKey(kL)
    pub_key     = bytes(signing_key.verify_key)
    return kL, pub_key


def pub_key_to_wallet_address(pub_key: bytes, version: str, workchain: int = 0) -> dict:
    """Build wallet address from raw public key without tonsdk mnemonic derivation."""
    from tonsdk.contract.wallet import Wallets, WalletVersionEnum
    from tonsdk.crypto import mnemonic_new

    version_map = {
        "v3r1": WalletVersionEnum.v3r1,
        "v3r2": WalletVersionEnum.v3r2,
        "v4r2": WalletVersionEnum.v4r2,
    }

    # Use tonsdk's wallet builder but inject our derived public key directly
    # We create a wallet instance and override the public key
    ver = version_map[version]

    # Build wallet state_init from pubkey to compute address
    if ver == WalletVersionEnum.v3r1:
        from tonsdk.contract.wallet import WalletV3ContractR1 as WalletClass
    elif ver == WalletVersionEnum.v3r2:
        from tonsdk.contract.wallet import WalletV3ContractR2 as WalletClass
    else:
        from tonsdk.contract.wallet import WalletV4ContractR2 as WalletClass

    w = WalletClass(public_key=pub_key, wc=workchain)
    bounceable     = w.address.to_string(True,  True,  False)
    non_bounceable = w.address.to_string(True,  False, False)
    raw            = w.address.to_string(False, False, False)
    return {
        "bounceable":     bounceable,
        "non_bounceable": non_bounceable,
        "raw":            raw,
    }


def try_ton_native(words):
    """Try tonsdk native TON mnemonic derivation."""
    from tonsdk.contract.wallet import Wallets, WalletVersionEnum
    results = {}
    for name, ver in [("v3r2", WalletVersionEnum.v3r2), ("v4r2", WalletVersionEnum.v4r2)]:
        try:
            _, pub, priv, wallet = Wallets.from_mnemonics(words, ver, workchain=0)
            results[f"TON-native {name}"] = {
                "bounceable":     wallet.address.to_string(True,  True,  False),
                "non_bounceable": wallet.address.to_string(True,  False, False),
                "raw":            wallet.address.to_string(False, False, False),
            }
        except Exception as e:
            results[f"TON-native {name}"] = {"error": str(e)}
    return results


def try_bip39(mnemonic):
    """Try BIP39 derivation (Tonkeeper / MyTonWallet style)."""
    try:
        seed = bip39_mnemonic_to_seed(mnemonic)
        priv_key, pub_key = derive_ed25519_key_from_seed(seed)
        results = {}
        for ver in ["v3r2", "v4r2"]:
            try:
                addrs = pub_key_to_wallet_address(pub_key, ver)
                results[f"BIP39 {ver}"] = addrs
            except Exception as e:
                results[f"BIP39 {ver}"] = {"error": str(e)}
        return results, priv_key, pub_key
    except ImportError:
        print("⚠️  PyNaCl not installed — skipping BIP39 check.")
        print("    Run: pip install PyNaCl\n")
        return {}, None, None
    except Exception as e:
        return {"BIP39 error": {"error": str(e)}}, None, None


def find_wallet_addresses(mnemonic: str):
    words = mnemonic.strip().split()
    if len(words) != 24:
        print(f"❌ Expected 24 words, got {len(words)}.")
        return

    print("\n" + "="*65)
    print("  TON Wallet Finder — All Derivation Methods")
    print("="*65)

    all_results = {}

    # Method 1: TON native
    print("\n📦 Method 1: TON Native Mnemonic (tonsdk default)")
    native = try_ton_native(words)
    all_results.update(native)

    # Method 2: BIP39 (Tonkeeper)
    print("📦 Method 2: BIP39 Mnemonic (Tonkeeper / MyTonWallet)\n")
    bip39_results, priv_key, pub_key = try_bip39(mnemonic)
    all_results.update(bip39_results)

    # Print all
    for label, addrs in all_results.items():
        if "error" in addrs:
            print(f"  [{label}] ❌ {addrs['error']}")
        else:
            print(f"  [{label}]")
            print(f"    EQ... (bounceable)     : {addrs['bounceable']}")
            print(f"    UQ... (non-bounceable) : {addrs['non_bounceable']}")
            print()

    print("="*65)
    print("\n👆 Find the address that matches your Tonkeeper wallet.")
    print("   Then update ton_faucet_bot.py:")
    print("     - Set WALLET_VERSION to the matching version (v3r2 or v4r2)")
    print("     - Set USE_BIP39 = True  if it matched a BIP39 result")
    print("     - Set USE_BIP39 = False if it matched a TON-native result\n")

    if pub_key:
        print(f"   BIP39 derived public key : {pub_key.hex()}")
    print()


if __name__ == "__main__":
    if "word1" in SENDER_MNEMONIC:
        print("❌ Paste your 24-word seed phrase into SENDER_MNEMONIC at the top of this file!")
    else:
        find_wallet_addresses(SENDER_MNEMONIC)
