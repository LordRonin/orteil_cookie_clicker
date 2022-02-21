import time

from selenium.common import exceptions
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By

import product
import upgrade
import money_tracker

CHROME_DRIVER_PATH = "E:/Programming/chromedriver.exe"
URL = "https://orteil.dashnet.org/cookieclicker/"
SAVE_FILENAME = "latest_save.txt"


class DecisionMaker:

    def __init__(self):
        self.service = Service(CHROME_DRIVER_PATH)
        self.driver = webdriver.Chrome(service=self.service)
        self.driver.get(URL)
        time.sleep(8)  # wait while the page opens

        self._dismiss_cookies()
        self.adjust_settings()

        self.cookie_img = self.driver.find_element(by=By.ID, value="bigCookie")

        self.wallet = money_tracker.MoneyTracker(self.driver)
        self.wallet.update()

        self.products = {}
        self._initialize_products()
        self.upgrades = {}
        self.initialize_upgrades()

        self.best_choice = self.products['Cursor']
        self.update_best_choice()

    def click_cookie(self):
        try:
            self.cookie_img.click()
        except exceptions.ElementClickInterceptedException:
            self.check_bonus()
            self.cookie_img.click()

    def update_all_info(self):

        # In case of unexpected stuck events or infinite clicking loops.
        self.wallet.update()
        for key in self.products.keys():
            self.products[key].update_data()
        self.initialize_upgrades()
        self.buy_best()

    def do_staff(self):
        # self._dismiss_achievements()
        self.check_bonus()
        self.wallet.update_money()
        if self.wallet.money > self.best_choice.price:
            self.buy_best()
            self.do_staff()

    def mouse_over(self, element):
        try:
            webdriver.ActionChains(self.driver).move_to_element(element).perform()
        except exceptions.StaleElementReferenceException:
            print(f"ERROR: Could not :hover element {element.get_attribute('id')}")

    def _initialize_products(self):
        all_elements = self.driver.find_elements(By.CSS_SELECTOR, ".product")
        for element in all_elements:
            new_product = product.Product(element, self.driver, self.wallet)
            self.products[new_product.get_name()] = new_product

    def buy_best(self):
        self.wallet.update_money()
        self.update_best_choice()
        print(f"AIMING TO BUY {self.best_choice.name} WITH RATIO = {self.best_choice.ratio}")
        if self.wallet.money > self.best_choice.price:
            print(f"***********    BOUGHT   *************\n{self.best_choice}\n")
            if isinstance(self.best_choice, product.Product):
                self.best_choice.buy()
                self.best_choice.update_data()
            else:
                self.buy_upgrade(self.best_choice)
                self.update_best_choice()

            # Avoid repeating upgrades hovering.
            # Check available upgrades if amount changed then re-initialize them.
            if len(self.driver.find_elements(By.CSS_SELECTOR, "div.crate.upgrade")) > len(self.upgrades):
                self.initialize_upgrades()
        else:
            self.wallet.update()
            print(f"* NOT ENOUGH MONEY * Money: {self.wallet.money} --- Cost: {self.best_choice.price}\n")

    def update_best_choice(self):
        best_ratio = 10 ** 30  # Lower ratio is better
        best_choice = self.best_choice
        for key in dict(self.products, **self.upgrades).keys():
            try:
                # self.products[key].update_data()
                if self.products[key].ratio < best_ratio:
                    best_ratio = self.products[key].ratio
                    best_choice = self.products[key]
            except KeyError:
                # Key is not found in self.products look for key in self.upgrades.
                self.upgrades[key]['instance'].update(self.products, self.wallet)
                if self.upgrades[key]['instance'].ratio < best_ratio:
                    best_ratio = self.upgrades[key]['instance'].ratio
                    best_choice = self.upgrades[key]['instance']

        print(f"BEST BUY IS {best_choice}\n")
        self.best_choice = best_choice

    def buy_upgrade(self, up_instance):
        try:
            up_instance.click()
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):

            # Exception occurs when upgrade was appeared or upgrade was bought by user.
            print(f"ERROR: Couldn't locate {up_instance.product_id}: {up_instance.name}")
            self.initialize_upgrades()
            new_up_instance = None
            for key in self.upgrades.keys():
                if up_instance.name == self.upgrades[key]['name']:
                    new_up_instance = self.upgrades[key]['instance']

            # Check if upgrade with searched name was already purchased.
            if new_up_instance:
                self.buy_upgrade(new_up_instance)
        else:
            time.sleep(0.2)
            for key in self.products.keys():
                self.products[key].update_data()
            print(f"* * * * *    BOUGHT   * * * * *\n{up_instance}")
            self.initialize_upgrades()

    def initialize_upgrades(self):
        self.upgrades.clear()
        self.mouse_over(self.driver.find_element(By.ID, "upgrades"))
        self.wallet.update()
        try:
            all_upgrades = self.driver.find_elements(By.CSS_SELECTOR, "div.crate.upgrade")
            for up in all_upgrades:
                self.mouse_over(up)
                try:
                    tooltip_tag = self.driver.find_element(By.CSS_SELECTOR, "#tooltipAnchor").text
                except exceptions.StaleElementReferenceException:
                    pass
                else:
                    upgrade_id = up.get_attribute('id')
                    new_upgrade = upgrade.Upgrade(up, self.driver, tooltip_tag, self.products, self.wallet, self)
                    self.upgrades[upgrade_id] = {"instance": new_upgrade,
                                                 "name": new_upgrade.name}
                    # print(new_upgrade)
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            print("NO UPGRADES FOUND")
        else:
            pass
        self.mouse_over(self.driver.find_element(by=By.ID, value="bigCookie"))

    def load_save(self):
        try:
            with open(SAVE_FILENAME, encoding="utf-8") as file:
                r = file.read()
        except FileNotFoundError:
            print(f"File \"{SAVE_FILENAME}\" was not found in directory.\n"
                  f"Loading failed. Starting from scratch.")
        else:
            try:
                preferences_button = self.driver.find_element(By.ID, "prefsButton")
                preferences_button.click()
                import_button = self.driver.find_element(By.LINK_TEXT, "Import save")
                import_button.click()
                text_area_prompt = self.driver.find_element(By.ID, "textareaPrompt")
                text_area_prompt.send_keys(r)
                confirmation_button = self.driver.find_element(By.ID, "promptOption0")
                confirmation_button.click()
                close_preferences_button = self.driver.find_element(By.CSS_SELECTOR, "#menu .menuClose")
                close_preferences_button.click()
            except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
                print(f"Load failed... Trying again.")
                self.load_save()
            else:
                print("Load successful. !!! Have fun !!!")

    def save_game(self):
        preferences_button = self.driver.find_element(By.ID, "prefsButton")
        preferences_button.click()
        try:
            export_save = self.driver.find_element(By.LINK_TEXT, "Export save")
            export_save.click()
            text_area_prompt = self.driver.find_element(By.ID, 'textareaPrompt')
            save_string = text_area_prompt.text
            with open(SAVE_FILENAME, mode='w', encoding="utf-8") as file:
                file.write(save_string)
            confirm_button = self.driver.find_element(By.CSS_SELECTOR, ".optionBox > #promptOption0")
            confirm_button.click()
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            print(f"ERROR: FAILED to save game progress")
        except exceptions.ElementClickInterceptedException:
            close_preferences_button = self.driver.find_element(By.CSS_SELECTOR, "#menu .menuClose")
            close_preferences_button.click()
            self.save_game()
        else:
            try:
                close_preferences_button = self.driver.find_element(By.CSS_SELECTOR, "#menu .menuClose")
                close_preferences_button.click()
            except exceptions.StaleElementReferenceException:
                print(f"ERROR: FAILED to save game progress")
            else:
                print(f"Successfully saved to file {SAVE_FILENAME}")

    def adjust_settings(self):
        preferences_button = self.driver.find_element(By.ID, "prefsButton")
        preferences_button.click()
        try:
            fancy_button = self.driver.find_element(By.ID, "fancyButton")
            fancy_button.click()
            particles_button = self.driver.find_element(By.ID, "particlesButton")
            particles_button.click()
            cursors_button = self.driver.find_element(By.ID, "cursorsButton")
            cursors_button.click()
            wobbly_button = self.driver.find_element(By.ID, "wobblyButton")
            wobbly_button.click()
            ask_lumps_button = self.driver.find_element(By.ID, "askLumpsButton")
            ask_lumps_button.click()
            milk_button = self.driver.find_element(By.ID, "milkButton")
            milk_button.click()
            custom_grandmas = self.driver.find_element(By.ID, "customGrandmasButton")
            custom_grandmas.click()
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            print("ERROR: Settings adjustment failed.")
        finally:
            close_preferences_button = self.driver.find_element(By.CSS_SELECTOR, "#menu .menuClose")
            close_preferences_button.click()

    def _dismiss_cookies(self):
        try:
            accept_ = self.driver.find_element(By.CSS_SELECTOR, "div.cc_banner-wrapper a.cc_btn")
        except (exceptions.NoSuchElementException, exceptions.ElementClickInterceptedException):
            print("ERROR: dismiss button not found")
        else:
            accept_.click()

    def _dismiss_achievements(self):
        # First try to close all achievements notification with one button.
        try:
            all_achievements_close_button = self.driver.find_element(By.CSS_SELECTOR, "div.framed.close.sidenote")
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException,
                exceptions.ElementClickInterceptedException):
            # If only one achievement badge exists or fails to find [close all] button try to close one at a time.
            try:
                achievement_close_button = self.driver.find_element(By.CSS_SELECTOR, "#notes div.close")
            except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException,
                    exceptions.ElementClickInterceptedException):
                pass
            else:
                achievement_close_button.click()
        else:
            all_achievements_close_button.click()

    def check_bonus(self):
        try:
            shimmers = self.driver.find_elements(By.CSS_SELECTOR, "#shimmers div.shimmer")
        except (exceptions.NoSuchElementException, exceptions.StaleElementReferenceException):
            pass
        except exceptions.ElementClickInterceptedException:
            self.check_bonus()
        else:
            shimmers = self.driver.find_elements(By.CSS_SELECTOR, "#shimmers div.shimmer")
            for shimmer in shimmers:
                shimmer.click()
                self.check_bonus()
