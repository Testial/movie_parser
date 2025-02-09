import scrapy
import re
from movie_parser.items import MovieParserItem

class MovieSpider(scrapy.Spider):
    name = 'movie'
    allowed_domains = ['ru.wikipedia.org']
    start_urls = ['https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту']

    def parse(self, response):
        category_div = response.xpath('//div[contains(@class, "mw-category") and contains(@class, "mw-category-columns")]')
        groups = category_div.xpath('.//div[contains(@class, "mw-category-group")]')
        for group in groups:
            links = group.xpath('.//a/@href').getall()
            for link in links:
                yield response.follow(link, callback=self.parse_movie)

        next_page = response.xpath('//div[@id="mw-pages"]//a[contains(text(), "Следующая")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_movie(self, response):

        item = MovieParserItem()

        film_table = response.xpath('//table[@data-name="Фильм"]')
        if not film_table:
            return

        title_parts = film_table.xpath('.//th[contains(@class, "infobox-above")]//text()[not(ancestor::style) and not(ancestor::sup)]').getall()
        title = " ".join(title_parts).strip()
        if title:
            item['title'] = title
        else:
            item['title'] = response.xpath('//h1/text()').get(default="").strip()

        mapping = {
            'жанр': 'genre',
            'режиссёр': 'director',
            'год': 'year'
        }

        rows = film_table.xpath('.//tr')
        for row in rows:
            header_parts = row.xpath('./th//text()[not(ancestor::style) and not(ancestor::sup)]').getall()
            header_text = " ".join(header_parts).strip().lower()

            for key, field in mapping.items():
                if key in header_text:
                    data_parts = row.xpath('./td//text()[not(ancestor::style) and not(ancestor::sup)]').getall()
                    data_text = " ".join(data_parts).strip()
                    if field == 'year':
                        years = re.findall(r'\b(\d{4})\b', data_text)
                        unique_years = list(dict.fromkeys(years))
                        data_text = ",".join(unique_years)
                    item[field] = data_text

            if re.search(r'^стран', header_text):
                data_parts = row.xpath('./td//text()[not(ancestor::style) and not(ancestor::sup)]').getall()
                data_text = " ".join(data_parts).strip()
                item['country'] = data_text

        yield item
