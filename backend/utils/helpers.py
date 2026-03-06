import datetime

def current_time():

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_text(text):

    if text:
        return text.strip()

    return ""