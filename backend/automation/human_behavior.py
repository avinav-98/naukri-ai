import random

def random_delay(page):

    page.wait_for_timeout(random.randint(1500,4000))


def random_scroll(page):

    page.mouse.wheel(0, random.randint(200,800))


def random_mouse_move(page):

    page.mouse.move(
        random.randint(100,800),
        random.randint(100,600)
    )