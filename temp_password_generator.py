import argparse
import secrets
import string
import sys


def generate_password(length: int, *, use_digits: bool = True,
                      use_uppercase: bool = True, use_symbols: bool = True,
                      use_lowercase: bool = True) -> str:
    """Generate a password using a cryptographically secure random source."""
    groups = []
    if use_lowercase:
        groups.append(string.ascii_lowercase)
    if use_digits:
        groups.append(string.digits)
    if use_uppercase:
        groups.append(string.ascii_uppercase)
    if use_symbols:
        groups.append("!@#$%^&*()-_=+[]{};:,.?/\\")

    if not groups:
        raise ValueError("Select at least one character type.")
    if length < len(groups):
        raise ValueError(f"Length must be at least {len(groups)} for the selected character groups.")

    alphabet = "".join(groups)
    # Include at least one character from every selected group.
    password_chars = [secrets.choice(group) for group in groups]
    password_chars.extend(secrets.choice(alphabet) for _ in range(length - len(password_chars)))
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def run_ascii_gui() -> None:
    """Show a small terminal menu for choosing password character types."""
    options = {
        "lowercase": True,
        "uppercase": True,
        "numbers": True,
        "symbols": True,
    }
    option_names = list(options)

    while True:
        print("\n+----------------------------------+")
        print("|       PASSWORD GENERATOR        |")
        print("+----------------------------------+")
        print(f"| 1. Lowercase letters  [{'x' if options['lowercase'] else ' '}] |")
        print(f"| 2. Uppercase letters  [{'x' if options['uppercase'] else ' '}] |")
        print(f"| 3. Numbers            [{'x' if options['numbers'] else ' '}] |")
        print(f"| 4. Symbols            [{'x' if options['symbols'] else ' '}] |")
        print("| 5. Generate password(s)        |")
        print("| Q. Quit                        |")
        print("+----------------------------------+")

        choice = input("Choose an option: ").strip().lower()
        if choice == "q":
            print("Goodbye.")
            return
        if choice in {"1", "2", "3", "4"}:
            key = option_names[int(choice) - 1]
            options[key] = not options[key]
            continue
        if choice != "5":
            print("Please choose 1-5 or Q.")
            continue

        try:
            length = int(input("Password length: ").strip())
            count = int(input("How many passwords? ").strip())
            if length < 1 or count < 1:
                print("Length and count must both be at least 1.")
                continue

            for _ in range(count):
                password = generate_password(
                    length,
                    use_lowercase=options["lowercase"],
                    use_uppercase=options["uppercase"],
                    use_digits=options["numbers"],
                    use_symbols=options["symbols"],
                )
                print(password)
        except ValueError as exc:
            print(f"Could not generate password: {exc}")
        except EOFError:
            print("\nGoodbye.")
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cryptographically secure passwords.")
    parser.add_argument("--interactive", action="store_true", help="open the ASCII menu")
    parser.add_argument("-l", "--length", type=int, default=16, help="password length (default: 16)")
    parser.add_argument("-n", "--count", type=int, default=1, help="number of passwords (default: 1)")
    parser.add_argument("--no-lowercase", action="store_true", help="exclude lowercase letters")
    parser.add_argument("--no-digits", action="store_true", help="exclude digits")
    parser.add_argument("--no-uppercase", action="store_true", help="exclude uppercase letters")
    parser.add_argument("--no-symbols", action="store_true", help="exclude symbols")
    args = parser.parse_args()

    if args.interactive or len(sys.argv) == 1:
        run_ascii_gui()
        return

    if args.length < 1:
        parser.error("--length must be at least 1")
    if args.count < 1:
        parser.error("--count must be at least 1")

    try:
        for _ in range(args.count):
            print(generate_password(
                args.length,
                use_lowercase=not args.no_lowercase,
                use_digits=not args.no_digits,
                use_uppercase=not args.no_uppercase,
                use_symbols=not args.no_symbols,
            ))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
