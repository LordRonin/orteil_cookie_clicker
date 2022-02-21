import re

from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By


initial_data = {
    "product0": ('Cursor', 15, 0.1),
    "product1": ('Grandma', 100, 1),
    "product2": ('Farm', 1100, 8),
    "product3": ('Mine', 12000, 47),
    "product4": ('Factory', 130000, 260),
    "product5": ('Bank', 1.4 * (10 ** 6), 1400),
    "product6": ('Temple', 20 * (10 ** 6), 7800),
    "product7": ('Wizard tower', 330 * (10 ** 6), 44000),
    "product8": ('Shipment', 51 * (10 ** 8), 260000),
    "product9": ('Alchemy lab', 75 * (10 ** 9), 16 * (10 ** 5)),
    "product10": ('Portal', 1 * (10 ** 12), 10 * (10 ** 6)),
    "product11": ('Time machine', 14 * (10 ** 12), 65 * (10 ** 6)),
    "product12": ('Antimatter condenser', 170 * (10 ** 12), 430 * (10 ** 6)),
    "product13": ('Prism', 21 * (10 ** 14), 29 * (10 ** 8)),
    "product14": ('Chancemaker', 26 * (10 ** 15), 21 * (10 ** 9)),
    "product15": ('Fractal engine', 310 * (10 ** 15), 150 * (10 ** 9)),
    "product16": ('Javascript console', 71 * (10 ** 18), 11 * (10 ** 11)),
    "product17": ('Idleverse', 12 * (10 ** 21), 83 * (10 ** 11))
}

MULTIPLIERS = {
    'million': 10 ** 6,
    'billion': 10 ** 9,
    'trillion': 10 ** 12,
    'quadrillion': 10 ** 15,
    'quintillion': 10 ** 18,
    'sextillion': 10 ** 21,
    'septillion': 10 ** 24,
}


def multiply_by_name(money_str: str):
    try:
        money_str = money_str.replace(",", "")
        money_str = money_str.replace("\n", " ")
        money_arr = money_str.split(" ")
        if len(money_arr) > 1:
            if "ion" in money_arr[1]:
                money = float(money_arr[0]) * MULTIPLIERS[money_arr[1]]
            else:
                money = float(money_arr[0])
        else:
            money = float(money_str)
        return round(money, 1)
    except (ValueError, TypeError):
        print(f"ERROR: Couldn't convert string {money_str} into float!")
        return 10 ** 10


class Product:

    def __init__(self, product, driver, wallet):
        self.driver = driver
        self.product = product
        self.product_id = product.get_attribute('id')

        self.type = 'building'
        self.name = initial_data[self.product_id][0]
        self.base_price = initial_data[self.product_id][1]
        self.base_cps = initial_data[self.product_id][2]

        self.wallet = wallet
        self.owned = self.get_owned()
        self.price = self.get_price()
        self.cps_per_one = self.base_cps
        self.cps_total = 0
        self.text = ""
        self.multiplier = 100  # Value in % is taken from "Stats" menu. Increases base_cps of buildings.
        self.ratio = None
        self.update_data()

    def __repr__(self):
        return f"* * * * *   BUILDING   * * * * *\n" \
               f"Name: {self.name} | Owned: {self.owned} | Price: {self.price}\n" \
               f"Ratio: {self.ratio} | TOTAL CpS {self.cps_total} | CpS one {self.cps_per_one}"

    def buy(self):
        self.product.click()
        self.update_data()

    def get_name(self):
        return self.name

    def update_data(self):
        self.owned = self.get_owned()
        self.multiplier = self.wallet.income_multiplier
        self.price = self.get_price()
        self.text = self.get_data()

        if self.text == "No data":
            # Not purchased yet. Need to adjust income according to multiplier in Stats menu.
            self.cps_per_one *= self.multiplier / 100
        else:
            try:
                data_split = self.text.split("\n")

                # process first line of tooltip text.
                pattern_one = re.compile(r'each\s[\w\s]*\sprod\w*\s(\d{1,3}[.,]?\d*\s?[\w]*)\scook\w*')
                findings = pattern_one.finditer(data_split[0])
                match = ""
                for find in findings:
                    match = find.group(1)
                self.cps_per_one = multiply_by_name(match)

                # process second line of tooltip text.
                pattern_total = re.compile(
                    r'\s(\d{1,3}[.,]?\d*\s?\w*i?o?n?)\s[\w\s]*\spro\w*\s(\d{1,3}[,.]?\d*\s?\w*)\scook\w*'
                )
                findings = pattern_total.finditer(data_split[1])
                match_cookies = ""

                for find in findings:
                    match_cookies = find.group(2)
                self.cps_total = multiply_by_name(match_cookies)
            except IndexError:
                print(f"ERROR: Couldn't read data. Probably mouse movement caused distraction.")

        # After values of have changed get updated value for price/cps ratio.
        self.update_ratio()

    def update_ratio(self):
        self.ratio = self.price / self.cps_per_one
        return self.ratio

    def get_data(self):
        data_text = "No data"
        if not self.owned:
            return "No data"
        else:
            self.mouse_over(self.product)
            try:
                data_text = self.driver.find_element(by=By.CSS_SELECTOR, value='#tooltip .data').text
            except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
                print(f"ERROR: Couldn't read tooltip data. Probably mouse interactions caused distraction.")
            finally:
                return data_text

    def mouse_over(self, element):
        try:
            webdriver.ActionChains(self.driver).move_to_element(element).perform()
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            print(f"ERROR in product.Product: Could not find or :hover over BUILDING {self.name}")

    #  Data for price and amount of owned is presented by lines in the form:
    # Product name
    # price
    # owned

    def get_price(self):
        info_arr = [value for value in self.product.text.replace(",", "").split("\n")]
        try:
            price_str = info_arr[1]
            price = multiply_by_name(price_str)
        except IndexError:
            return self.base_price
        else:
            return price

    def get_owned(self):
        info_arr = self.product.text.split("\n")
        try:
            owned = float(info_arr[2])
        except IndexError:
            return 0
        else:
            return owned

    # No need to get description. There is nothing useful in that text.
    # def get_description(self):
    #     if not self.owned:
    #         return "No description"
    #     else:
    #         self.mouse_over(self.product)
    #         try:
    #             tooltip_description_text = self.driver.find_element(By.CSS_SELECTOR, '#tooltip .description').text
    #         except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
    #             return "No description"
    #         else:
    #             return tooltip_description_text
