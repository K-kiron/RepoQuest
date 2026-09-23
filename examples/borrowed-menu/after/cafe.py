"""A tiny cafe menu cache. No network, database, or third-party packages."""


def load_menu():
    return {"name": "Lunch", "items": ["soup", "bread"]}


class MenuService:
    def __init__(self):
        self._menu = load_menu()

    def menu_for(self, special=None):
        menu = {**self._menu, "items": self._menu["items"].copy()}
        if special is not None:
            menu["items"].append(special)
        return menu


def receipt(menu):
    return ", ".join(menu["items"])
