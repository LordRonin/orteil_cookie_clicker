import time
import re

from selenium.webdriver.common.by import By
from selenium.common import exceptions

import product


class MoneyTracker:
    """
    Class represents object that tracks amount of cookies (money) available and how many cookies are cooked per second.
    Also has methods that repeatedly check in-game "Stats" board to update how many cookies (money) are made
    by clicking the "Big Cookie" image and to update multiplier increased after upgrades made and bonuses acquired
    to a track change in base amount of cookies (money) produced by buildings that are not yet owned.
    """
    def __init__(self, driver):
        self.driver = driver
        self.money = 1
        self.money_per_sec = 1
        self.money_per_click = 1
        self.income_multiplier = 100

    def __repr__(self):
        return f"Cookies: {self.money}\n" \
               f"Cookies per sec: {self.money_per_sec}\n" \
               f"Cookies per click: {self.money_per_click}" \
               f"Multiplier: {self.income_multiplier}"

    def update(self):
        self.update_money()
        self.update_cookies_per_click()

    def update_money(self):
        money_element = self.driver.find_element(by=By.ID, value='cookies')
        cookie_available = money_element.text.rpartition('cookies')[0].strip()
        cookie_per_sec = money_element.text.rpartition(':')[2].strip()
        self.money = product.multiply_by_name(cookie_available)
        self.money_per_sec = product.multiply_by_name(cookie_per_sec)

    def update_cookies_per_click(self):
        # Read all info available in Statics.
        try:
            stats_button = self.driver.find_element(By.ID, "statsButton")
            stats_button.click()
            stats_text = self.driver.find_element(By.ID, "menu").text
        except (exceptions.StaleElementReferenceException, exceptions.ElementNotInteractableException):
            print("ERROR: Could NOT open menu to get value of cookies per click!")
        # In case Golden Cookie on top of "Stats" button. Try to again
        except exceptions.ElementClickInterceptedException:
            self.update_cookies_per_click()

        # Find regex pattern in all the text and transform it.
        else:
            pattern = re.compile(r'Cookies\sper\sclick\s?:\s?(\d{1,3}[,.]?\d*\s?\w*i?o?n?)')
            matches = pattern.finditer(stats_text)
            cook_per_click = ""
            for match in matches:
                cook_per_click = match.group(1)
            self.money_per_click = product.multiply_by_name(cook_per_click)

            pattern = re.compile(r'\(multiplier\s:\s(\d{1,3}[.,]?\d{0,3}\s?\D*[ion]?%)\)')
            matches = pattern.finditer(stats_text)
            multiplier_str = ""
            for match in matches:
                multiplier_str = match.group(1)
            multiplier_str = multiplier_str.replace("%", "").strip()
            self.income_multiplier = product.multiply_by_name(multiplier_str)
        finally:
            try:
                close_preferences_button = self.driver.find_element(By.CSS_SELECTOR, "#menu .menuClose")
                close_preferences_button.click()
            except (exceptions.StaleElementReferenceException, exceptions.ElementNotInteractableException,
                    exceptions.ElementClickInterceptedException):
                time.sleep(0.1)
                close_preferences_button = self.driver.find_element(By.CSS_SELECTOR, "#menu .menuClose")
                close_preferences_button.click()
