"""
TON Wallet Address Finder
Run this to find the correct address for your seed phrase across ALL wallet versions.
Compare the output addresses with your actual wallet in Tonkeeper/MyTonWallet.

Usage:
    pip install tonsdk
    python find_my_wallet.py
"""

SENDER_MNEMONIC = "word1 word2 ... word24"   # <-- paste your 24-word seed phrase here

# ──────────────────────────────────────────────────────────────────────────────

def find_wallet_addresses(mnemonic: str):
    try:
        from tonsdk.contract.wallet import Wallets, WalletVersionEnum
    except ImportError:
        print("❌ tonsdk not installed. Run: pip install tonsdk")
        return

    words = mnemonic.strip().split()
    if len(words) != 24:
        print(f"❌ Expected 24 words, got {len(words)}. Check your mnemonic.")
        return

    versions = {
        "v3r1": WalletVersionEnum.v3r1,
        "v3r2": WalletVersionEnum.v3r2,
        "v4r2": WalletVersionEnum.v4r2,
    }

    print("\n" + "="*65)
    print("  TON Wallet Address Finder")
    print("="*65)
    print("\nYour seed phrase generates these addresses:\n")

    for name, ver in versions.items():
        try:
            for workchain, wc_name in [(0, "basechain (normal)"), (-1, "masterchain (rare)")]:
                _, pub, priv, wallet = Wallets.from_mnemonics(words, ver, workchain=workchain)
                addr_bounceable     = wallet.address.to_string(True,  True,  False)  # EQ...
                addr_non_bounceable = wallet.address.to_string(True,  False, False)  # UQ...
                addr_raw            = wallet.address.to_string(False, False, False)  # 0:hex

                if workchain == 0:  # Only show basechain (most wallets use this)
                    print(f"  [{name}]")
                    print(f"    Bounceable     : {addr_bounceable}")
                    print(f"    Non-bounceable : {addr_non_bounceable}")
                    print(f"    Raw            : {addr_raw}")
                    print()
        except Exception as e:
            print(f"  [{name}] Error: {e}\n")

    print("="*65)
    print("\n👆 Match one of these with your wallet app (Tonkeeper etc.)")
    print("   Then set WALLET_VERSION in ton_faucet_bot.py to the matching version.")
    print("   Use the NON-BOUNCEABLE address (UQ...) to receive TON deposits.\n")


if __name__ == "__main__":
    if "word1" in SENDER_MNEMONIC:
        print("❌ Please paste your 24-word seed phrase into SENDER_MNEMONIC at the top of this file!")
    else:
        find_wallet_addresses(SENDER_MNEMONIC)
