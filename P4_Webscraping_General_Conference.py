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
            conn.close()

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
            speaker = speaker_tag.get_text(strip=True).replace("By ", "") if speaker_tag else None

            # Title
            title_tag = talk_soup.select_one("h1")
            title = title_tag.get_text(strip=True) if title_tag else None

            if title and "sustaining" not in title.lower():
                # Kicker
                kicker_tag = talk_soup.select_one(".kicker")
                kicker = kicker_tag.get_text(strip=True) if kicker_tag else None

                # 4 (2.0) Get references
                # FULL dictionary (paste your full version here)
                standard_works_dict = {
                    'Speaker_Name': '',
                    'Talk_Name': '',
                    'Kicker': '',
                    'Matthew': 0, 'Mark': 0, 'Luke': 0, 'John': 0, 'Acts': 0,
                    'Romans': 0, '1 Corinthians': 0, '2 Corinthians': 0,
                    'Galatians': 0, 'Ephesians': 0, 'Philippians': 0,
                    'Colossians': 0, '1 Thessalonians': 0, '2 Thessalonians': 0,
                    '1 Timothy': 0, '2 Timothy': 0, 'Titus': 0, 'Philemon': 0,
                    'Hebrews': 0, 'James': 0, '1 Peter': 0, '2 Peter': 0,
                    '1 John': 0, '2 John': 0, '3 John': 0, 'Jude': 0,
                    'Revelation': 0,
                    'Genesis': 0, 'Exodus': 0, 'Leviticus': 0, 'Numbers': 0,
                    'Deuteronomy': 0, 'Joshua': 0, 'Judges': 0, 'Ruth': 0,
                    '1 Samuel': 0, '2 Samuel': 0, '1 Kings': 0, '2 Kings': 0,
                    '1 Chronicles': 0, '2 Chronicles': 0, 'Ezra': 0,
                    'Nehemiah': 0, 'Esther': 0, 'Job': 0, 'Psalm': 0,
                    'Proverbs': 0, 'Ecclesiastes': 0, 'Song of Solomon': 0,
                    'Isaiah': 0, 'Jeremiah': 0, 'Lamentations': 0,
                    'Ezekiel': 0, 'Daniel': 0, 'Hosea': 0, 'Joel': 0,
                    'Amos': 0, 'Obadiah': 0, 'Jonah': 0, 'Micah': 0,
                    'Nahum': 0, 'Habakkuk': 0, 'Zephaniah': 0,
                    'Haggai': 0, 'Zechariah': 0, 'Malachi': 0,
                    '1 Nephi': 0, '2 Nephi': 0, 'Jacob': 0, 'Enos': 0,
                    'Jarom': 0, 'Omni': 0, 'Words of Mormon': 0,
                    'Mosiah': 0, 'Alma': 0, 'Helaman': 0,
                    '3 Nephi': 0, '4 Nephi': 0, 'Mormon': 0,
                    'Ether': 0, 'Moroni': 0,
                    'Doctrine and Covenants': 0,
                    'Moses': 0, 'Abraham': 0,
                    'Joseph Smith—Matthew': 0,
                    'Joseph Smith—History': 0,
                    'Articles of Faith': 0
                }

                #Get footnotes
                footnotes_section = talk_soup.find("footer", class_="notes")

                if footnotes_section is not None:

                    footnote_text = footnotes_section.get_text()

                    # Loop through each book
                    for key in standard_works_dict:

                        # Skip non-book fields
                        if key in ["Speaker_Name", "Talk_Name", "Kicker"]:
                            continue

                        # Count occurrences of each book name
                        count = footnote_text.count(key)

                        standard_works_dict[key] = count

                else:
                    # No references in this talk
                    print("No footnotes found for this talk.")

                #store other values
                standard_works_dict["Speaker_Name"] = speaker
                standard_works_dict["Talk_Name"] = title
                standard_works_dict["Kicker"] = kicker

                #append to list
                talk_data.append(standard_works_dict)


        # 5. Save to PostgreSQL
        df = pd.DataFrame(talk_data)
        df.to_sql("general_conference", engine, if_exists="replace", index=False)

        # 6. Confirmation
        print("You've saved the scraped data to your postgres database.")

    elif choice == "2":
        pass

    else:
        bContinue = False