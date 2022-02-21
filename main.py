import time

from decision_maker import DecisionMaker

SAVE_PERIOD = 5 * 60  # Save game every 5 minutes.

maker = DecisionMaker()

# If you want to load saved game, uncomment a line below.
maker.load_save()

# for _ in range(20):
#     maker.click_cookie()
# maker.products['Cursor'].buy()
# maker.wallet.update_money()

timer = time.time() + 20
save_timer = time.time() + SAVE_PERIOD

while time.time() < timer:
    maker.do_staff()

    for _ in range(300):
        maker.click_cookie()
    timer = time.time() + 15

    # Save game
    if time.time() > save_timer:
        maker.save_game()
        save_timer = time.time() + SAVE_PERIOD
        maker.update_all_info()
