import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

import os
import json
import datetime as dt

import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO)

# GOAL -> save PDFs to disk

config = {
    "main_page": "https://huggingface.co",
    "daily_papers_url": "https://huggingface.co/papers",
    "daily_papers_folder": "database/daily_papers/",
}


class HuggingfaceClient:

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config

    @staticmethod
    def get_content(url: str) -> Optional[str]:
        logging.info(f"running get_content_of_daily_papers_page, url: {url}")
        response = requests.get(url)
        logging.info(response.status_code)
        try:
            response.raise_for_status()
        except Exception as exc:
            logging.error(f"{url} returned {exc}")
        else:
            try:
                content = response.content
            except Exception as exc:
                logging.error(f"Could not retrieve content of response, reason: {exc}")
            return content

    @staticmethod
    def make_soup(website_content: str) -> BeautifulSoup:
        try:
            soup = BeautifulSoup(website_content, features="lxml")
        except Exception as exc:
            # TODO: better logging
            logging.error(f"Could not make soup")
        else:
            return soup

    def get_links_to_hf_papers(self, soup: BeautifulSoup) -> Optional[List[str]]:
        if articles := soup.find_all("article"):
            return [
                self.config["main_page"] + article.find("a")["href"]
                for article in articles
            ]
        else:
            # TODO: better logging
            logging.error("No daily papers found")

    def extract_data_from_paper_page(self, link_to_paper: str) -> Dict[str, Any]:
        # TODO: extract getting response from get_content_of_daily_papers_page into separate method and use it here
        content = self.get_content(link_to_paper)
        soup = self.make_soup(content)
        title = soup.find("h1").text
        arxiv_id = link_to_paper.split("/")[-1]
        abstract = soup.find("h2").parent.find("p").text
        paper_link = [
            a["href"] for a in soup.find_all("a") if "arxiv.org/pdf" in a["href"]
        ][0]
        data = {
            "title": title,
            "arxiv_id": arxiv_id,
            "abstract": abstract,
            "paper_link": paper_link,
        }

        return data

    def download_paper(self, paper_url: str, arxiv_id: str, folder: str) -> None:
        content = self.get_content(paper_url)
        print(paper_url)
        with open(folder + arxiv_id + ".pdf", "wb") as f:
            f.write(content)

    @staticmethod
    def save_papers_data_to_json(all_data: List[Dict[str, Any]], folder: str) -> None:
        with open(folder + "metadata.json", "w") as f:
            f.write(json.dumps(all_data))

    def _make_daily_papers_folder(self, date: str) -> str:
        folder = self.config["daily_papers_folder"] + date + "/"
        os.mkdir(folder)  # TODO: shutil it parents ok etc
        return folder

    def download_daily_papers_and_their_metadata(self) -> None:
        date = str(dt.date.today())
        folder = self._make_daily_papers_folder(date)
        daily_papers_page_content = self.get_content(self.config["daily_papers_url"])
        daily_papers_soup = self.make_soup(daily_papers_page_content)
        links_to_hf_papers = self.get_links_to_hf_papers(daily_papers_soup)
        all_data = []
        for link_to_hf_paper in links_to_hf_papers:
            paper_data = self.extract_data_from_paper_page(link_to_hf_paper)
            self.download_paper(
                paper_data["paper_link"], paper_data["arxiv_id"], folder
            )
            all_data.append(paper_data)
        self.save_papers_data_to_json(all_data, folder)


if __name__ == "__main__":
    hc = HuggingfaceClient(config)
    hc.download_daily_papers_and_their_metadata()
