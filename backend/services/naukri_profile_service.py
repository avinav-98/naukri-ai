from backend.naukri.profile_scraper import scrape_profile


def get_profile(user_id=1):

    profile_name = scrape_profile(user_id)

    return {
        "name": profile_name
    }