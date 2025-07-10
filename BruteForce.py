# Password BruteForce:

def main():
    # Prompt the user for their "secret" password: 5 lowercase letters followed by 2 digits
    secret = input("Enter a password (5 lowercase letters followed by 2 digits): ").strip()
    if len(secret) != 7 or not secret[:5].islower() or not secret[5:].isdigit():
        print("Password must be 5 lowercase letters followed by 2 digits.")
        return

    print("\nStarting brute-force…\n")

    from itertools import product
    import string

    guess = None
    # Generate all possible combinations: 5 letters and 2 digits
    for letters in product(string.ascii_lowercase, repeat=5):
        for numbers in product(string.digits, repeat=2):
            guess = ''.join(letters) + ''.join(numbers)
            print(f"Trying: {guess}")
            if guess == secret:
                print(f"\nPassword found: {secret!r}")
                return

if __name__ == "__main__":
    main()


