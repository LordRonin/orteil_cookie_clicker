# Using this class was not implemented.


class Choicer:

    def __init__(self, products: dict, upgrades: dict, cookies_per_click: float, money_per_sec: float, money_available):
        self.products = products
        self.upgrades = upgrades
        self.cookies_per_click = cookies_per_click
        self.money_per_sec = money_per_sec
        self.money = money_available
        self.best_buy = None

    '''Best pick out of affordable options (enough money to buy right now)
    is the one that gives the BEST price / cookie_per_second increase'''


