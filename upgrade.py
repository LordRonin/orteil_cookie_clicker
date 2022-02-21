import re

from selenium import webdriver
from selenium.webdriver.common.by import By

import product


class Upgrade:

    def __init__(self, upgrade, driver, tooltip_data, products, wallet, maker):
        self.maker = maker
        self.driver = driver
        self.wallet = wallet
        self.products = products

        self.upgrade = upgrade
        self.product_id = upgrade.get_attribute("id")

        self.text = tooltip_data
        self.name = self.get_name()
        self.price = self.get_price()  # get data from self.text

        self.cps = None
        self.object_effect_pairs = []  # multiplier for affected buildings
        self.get_affected_effect()
        self.ratio = self.get_ratio()  # price / cookie_per_sec_increase ratio

    def click(self):
        self.mouse_over(self.driver.find_element(By.ID, "upgrades"))
        self.upgrade.click()

    def __repr__(self):
        return f"* * * * *   U P G R A D E   * * * * *\n" \
               f"ID: {self.product_id}, Name: {self.name}\n" \
               f"Price: {self.price}, CpS+ {self.cps}, Ratio: {self.ratio}\n" \
               f"Effect pairs: {self.object_effect_pairs}\n"

    def update(self, products, wallet):
        self.wallet = wallet
        self.products = products
        self.ratio = self.get_ratio()

    def mouse_over(self, element):
        webdriver.ActionChains(self.driver).move_to_element(element).perform()

    def get_ratio(self):
        cps_increase = 0
        for pair in self.object_effect_pairs:
            target, multiplier = pair
            if target == "Total CpS":
                cps_increase += self.wallet.money_per_sec * multiplier
            elif target == "Mouse":
                # Assuming 5 clicks per second on Big Cookie.
                cps_increase += self.wallet.money_per_click * multiplier * 20
            elif target == "Clicking":
                # Assuming 5 clicks per second on Big Cookie.
                cps_increase += self.wallet.money_per_sec * multiplier * 20
            else:
                cps_increase += self.products[target].cps_total * multiplier
        self.cps = cps_increase
        try:
            return self.price / cps_increase
        except ZeroDivisionError:
            return self.price

    def get_affected_effect(self):
        for pair in self.process_description():
            affected, effect = pair

            affected = affected.strip()
            if affected == 'Factories':
                affected = 'Factory'
            elif affected[-1] == "s":
                affected = affected[:-1]

            if isinstance(effect, str) and ('%' in effect):
                effect = effect.strip()
                effect = float(effect.replace("%", "")) / 100
            elif isinstance(effect, str) and (effect.strip() == 'twice'):
                effect = 2
            elif isinstance(effect, str) and ('times' in effect):
                effect = effect.strip()
                effect = float(effect[0])

            self.object_effect_pairs.append((affected, effect))

    def get_name(self):
        lines = self.text.split("\n")
        try:
            name = lines[1].strip()
        except IndexError:
            self.maker.initialize_upgrades()
        else:
            return name

    def get_price(self):
        lines = self.text.split("\n")
        price_str = lines[0]
        price = product.multiply_by_name(price_str)
        return price

    def get_up_type(self):
        up_type = ""
        pattern = re.compile(r'\[(\w*)]')
        matches = pattern.finditer(self.text)
        for match in matches:
            up_type = match.group(1)
        return up_type

    def process_description(self):
        text = self.text
        affected_effect_tuples = []  # append tuples (affected, effect)

        # Mouse and Cursors x2
        if self._check_if(r'mouse\sand\scursors'):
            affected_effect_tuples.append(('Mouse', 2))
            affected_effect_tuples.append(('Cursor', 2))

        # clicking affects Mouse with % .group(1)
        elif self._check_if(r'clicking\sgains\s.?(\d+%)'):
            x = self._check_if(r'clicking\sgains\s.?(\d+%)')
            affected_effect_tuples.append(('Clicking', x[0]))

        # fingers update effect unknown (let it be affecting Mouse by 2)
        elif self._check_if(r'from\sthousand\sfinger\w?\sby\s?(\d+)'):
            affected_effect_tuples.append(("Mouse", 2))

        # common pattern with name of affected building [0][0] CUT LAST 's' remember FACTORIES, multiplier [0][2]
        elif self._check_if(r'(\w*\s\w*)(s|ies)?\sare\s(\w+)\sas\sefficient'):
            affected, empty, effect = self._check_if(r'(\w*\s?\w*)(s|ies)?\sare\s(\w+)\sas\sefficient')[0]
            affected_effect_tuples.append((affected, effect))

        # \s?(\w*\s?\w*)(s|ies)?\sare\s((\w+)|(\d+\stimes))\sas\sefficient

        # Kitten affects Total CpS, value ~ 15% (approximately)
        elif self._check_if(r'you\sgain\smore\scps[\w\s]*milk'):
            affected_effect_tuples.append(('Total CpS', '15%'))

        # Golden cookie appearance x2, assume affects Total CpS with value of 20%
        elif self._check_if(r'golden\scookies?\sappear'):
            affected_effect_tuples.append(('Total CpS', '20%'))

        # Cookie upgrades affect Total CpS value [0]
        elif self._check_if(r'cookie\sproduction\smultiplier\s.?(\d+%)'):
            x = self._check_if(r'cookie\sproduction\smultiplier\s.?(\d+%)')
            affected_effect_tuples.append(('Total CpS', x[0]))

        # Other cases not implemented yet. Assume they give 1% boost to Total CpS.
        else:
            affected_effect_tuples.append(('Total CpS', '1%'))
        return affected_effect_tuples

    # Function to avoid filling re.findall function again and again.
    def _check_if(self, regex: str):
        return re.findall(regex, self.text, re.I)
