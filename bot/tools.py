# Day 2: tools are normal Python functions the agent can decide to call
from pathlib import Path

import pandas as pd
import requests
from agents import function_tool
from pydantic import BaseModel

MENU_FILE = Path(__file__).parent.parent / "data" / "menu.csv"
ICED_SURCHARGE = 0.30


def load_menu():
    return pd.read_csv(MENU_FILE)


def menu_text(category=""):
    menu = load_menu()
    if category:
        menu = menu[menu["category"] == category.lower()]
    lines = [f"{row['item']} (${row['price']:.2f}) - {row['description']}" for _, row in menu.iterrows()]
    return "\n".join(lines) if lines else "Nothing in that category."


class OrderLine(BaseModel):
    item: str
    quantity: int
    iced: bool


def bill_text(order):
    menu = load_menu()
    menu["key"] = menu["item"].str.lower()
    lines, total = [], 0.0
    for line in order:
        match = menu[menu["key"] == line.item.lower().strip()]
        if match.empty:
            lines.append(f"{line.item}: not on the menu")
            continue
        price = float(match["price"].iloc[0])
        if line.iced:
            price += ICED_SURCHARGE
        cost = price * line.quantity
        total += cost
        name = match["item"].iloc[0] + (" Peng" if line.iced else "")
        lines.append(f"{line.quantity} x {name} = ${cost:.2f}")
    lines.append(f"TOTAL: ${total:.2f}")
    return "\n".join(lines)


def weather_text(area="City"):
    url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
    data = requests.get(url, timeout=10).json()["data"]
    latest = data["items"][0]
    period = latest["valid_period"]["text"]
    for forecast in latest["forecasts"]:
        if area.lower() in forecast["area"].lower():
            return f"{forecast['area']}, {period}: {forecast['forecast']}"
    areas = ", ".join(f["area"] for f in latest["forecasts"])
    return f"No area called '{area}'. Try one of: {areas}"


# --- Wrap the plain functions as tools for the agent ---
# The docstring is what the agent reads to decide WHEN to use each tool.

@function_tool
def get_menu(category: str) -> str:
    """Get the kopitiam menu with prices. category: 'drink', 'food', or '' (empty) for everything."""
    return menu_text(category)


@function_tool
def calculate_bill(order: list[OrderLine]) -> str:
    """Calculate the bill. Use the exact item names from the menu. Set iced=True for 'peng' (iced) drinks."""
    return bill_text(order)


@function_tool
def get_weather(area: str) -> str:
    """Get the live 2-hour weather forecast for a Singapore area, e.g. 'Bedok', 'Jurong West'. Use 'City' if unsure."""
    return weather_text(area)
