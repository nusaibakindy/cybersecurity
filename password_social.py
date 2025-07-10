import itertools
import time

def guess_password_from_info(secret):
    """
    Attempts to guess a password using a targeted wordlist generated from
    selected personal information. The generator will loop indefinitely
    through the guesses until it finds the secret.
    """
    print("\nStarting targeted password attack...\n")

    # Define keywords and numbers from personal info.
    keywords = [
        "sara", "dammam", "king", "faisal", "university", "rayan",
        "majid", "mohandis", "hyundai", "tucson", "fitness", "fan"
    ]
    numbers = ["2016", "16", "5", "2020", "20", "2025"]

    # Create a list to hold all potential guesses
    potential_guesses = []

    # Pattern 1: A keyword combined with a number (e.g., keyword+number)
    for keyword in keywords:
        for num in numbers:
            potential_guesses.append(f"{keyword}{num}")
            potential_guesses.append(f"{keyword.capitalize()}{num}")

    # Pattern 2: The keywords themselves (in both lowercase and capitalized)
    for keyword in keywords:
        potential_guesses.append(keyword)
        potential_guesses.append(keyword.capitalize())

    # Pattern 3: Two keywords combined
    for combo in itertools.permutations(keywords, 2):
        potential_guesses.append(f"{combo[0]}{combo[1]}")
        potential_guesses.append(f"{combo[0].capitalize()}{combo[1].capitalize()}")

    # Pattern 4: Keyword + number + keyword
    for k1 in keywords:
        for num in numbers:
            for k2 in keywords:
                potential_guesses.append(f"{k1}{num}{k2}")
                potential_guesses.append(f"{k1.capitalize()}{num}{k2.capitalize()}")

    # Pattern 5: Two keywords combined followed by a number
    for combo in itertools.permutations(keywords, 2):
        for num in numbers:
            potential_guesses.append(f"{combo[0]}{combo[1]}{num}")
            potential_guesses.append(f"{combo[0].capitalize()}{combo[1].capitalize()}{num}")

    # Pattern 6: Three keywords concatenated
    for combo in itertools.permutations(keywords, 3):
        potential_guesses.append(f"{combo[0]}{combo[1]}{combo[2]}")
        potential_guesses.append(f"{combo[0].capitalize()}{combo[1].capitalize()}{combo[2].capitalize()}")

    # Pattern 7: Three keywords concatenated with a trailing number
    for combo in itertools.permutations(keywords, 3):
        for num in numbers:
            potential_guesses.append(f"{combo[0]}{combo[1]}{combo[2]}{num}")
            potential_guesses.append(f"{combo[0].capitalize()}{combo[1].capitalize()}{combo[2].capitalize()}{num}")

    attempt = 1
    # Keep looping indefinitely through all potential guesses
    while True:
        for guess in potential_guesses:
            print(f"Attempt #{attempt}: Trying '{guess}'")
            if guess == secret:
                print(f"\nSUCCESS! Password found: '{secret}'")
                return
            attempt += 1
            time.sleep(0.005)

def main():
    """
    Main function to run the password guessing simulation.
    """
    print("This program simulates guessing a password based on personal information.")
    print("-" * 20)
    
    # Prompt the user for the secret password to guess
    secret_password = input("\nEnter a password to test against: ").strip()

    if not secret_password:
        print("Password cannot be empty.")
        return

    guess_password_from_info(secret_password)

if __name__ == "__main__":
    main()