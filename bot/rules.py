# Day 1 brain: plain if/else rules (no AI yet)

prices = {
    "kopi": 1.40,
    "kopi-o": 1.20,
    "kopi-c": 1.50,
    "teh": 1.40,
    "teh-o": 1.20,
    "teh-c": 1.50,
    "milo": 1.80,
}


def reply_with_rules(text, name="friend"):
    text = text.lower().strip()

    if text in ["/start", "hi", "hello"]:
        return f"Hello {name}! Uncle here. Type 'menu' to see what we have."

    if text == "menu":
        lines = [f"{drink.title()}: ${price:.2f}" for drink, price in prices.items()]
        return "Today's menu:\n" + "\n".join(lines)

    # Check longer names first so "kopi-o" is not matched as "kopi"
    for drink in sorted(prices, key=len, reverse=True):
        if drink in text:
            return f"One {drink.title()} coming up! That's ${prices[drink]:.2f}."

    return "Aiyo, Uncle don't understand. Type 'menu' lah."
