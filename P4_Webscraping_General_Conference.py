# Author: Courtney Bingham, Anna Pettit, Ethan Lawson, Braden Adams

# Imports
from bs4 import BeautifulSoup
import requests
import pandas as pd
import sqlalchemy
import matplotlib.pyplot as plot

# Database connection
engine = sqlalchemy.create_engine(
    "postgresql://postgres:admin@localhost:5432/is303"
)

bContinue = True
while bContinue:
    choice = input("If you want to scrape data, enter 1. If you want to see summaries of stored data, enter 2. Enter any other value to exit the program: ")

    if choice == "1":

        # 1. Drop table
        drop_table_query = sqlalchemy.text("DROP TABLE IF EXISTS general_conference;")
        with engine.connect() as conn:
            conn.execute(drop_table_query)
            conn.commit()

        # 2. Load main page
        url = "https://www.churchofjesuschrist.org/study/general-conference/2025/10?lang=eng"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # 3. Get talk links
        links = soup.select("a[href]")
        base_url = "https://www.churchofjesuschrist.org"
        talk_links = []

        for link in links:
            href = link.get("href")

            if not href:
                continue

            if "/study/general-conference/2025/10/" in href:
                if "session" in href.lower():
                    continue
                if "sustaining" in href.lower():
                    continue

                full_url = base_url + href

                if full_url not in talk_links:
                    talk_links.append(full_url)

        print("Total talk links found:", len(talk_links))

        talk_data = []

        # 4. Visit each talk
        for talk_url in talk_links:
            print("Visiting:", talk_url)

            talk_response = requests.get(talk_url)
            talk_soup = BeautifulSoup(talk_response.text, "html.parser")

            # Speaker
            speaker_tag = talk_soup.select_one(".byline")
            speaker = speaker_tag.get_text(strip=True) if speaker_tag else None

            # Title
            title_tag = talk_soup.select_one("h1")
            title = title_tag.get_text(strip=True) if title_tag else None

            # Kicker
            kicker_tag = talk_soup.select_one(".kicker")
            kicker = kicker_tag.get_text(strip=True) if kicker_tag else None

            # Reference selector
            references = talk_soup.find_all("a")

            refs = [ref for ref in references if "scripture" in ref.get("href", "")]

            print("Refs found:", len(refs))

            bible = 0
            bom = 0
            dc = 0
            pgp = 0

            for ref in refs:
                text = ref.get_text().lower()

                if any(book in text for book in [
                    "gen", "ex", "lev", "num", "deut", "joshua", "judges",
                    "samuel", "kings", "psalm", "proverbs", "isaiah",
                    "jeremiah", "ezekiel", "matt", "mark", "luke", "john",
                    "acts", "rom", "cor", "gal", "eph", "phil", "col",
                    "thess", "tim", "titus", "hebrews", "james", "peter", "rev"
                ]):
                    bible += 1

                elif any(book in text for book in [
                    "nephi", "alma", "mosiah", "helaman", "ether",
                    "moroni", "jacob", "enos", "jarom", "omni"
                ]):
                    bom += 1

                elif "d&c" in text or "doctrine and covenants" in text:
                    dc += 1

                elif any(book in text for book in ["moses", "abraham"]):
                    pgp += 1

            talk_data.append({
                "speaker": speaker,
                "title": title,
                "kicker": kicker,
                "bible_refs": bible,
                "book_of_mormon_refs": bom,
                "dc_refs": dc,
                "pgp_refs": pgp
            })

        print("Total talks scraped:", len(talk_data))

        # 5. Save to PostgreSQL
        df = pd.DataFrame(talk_data)
        df.to_sql("general_conference", engine, if_exists="replace", index=False)

        # 6. Confirmation
        print("You've saved the scraped data to your postgres database.")

    elif choice == "2":
        pass

    else:
        bContinue = False