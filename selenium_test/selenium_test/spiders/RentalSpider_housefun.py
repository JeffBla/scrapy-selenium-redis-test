import scrapy
import logging
import time
from collections import defaultdict
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from scrapy_redis.spiders import RedisSpider

from selenium_test.items import RentalItem


class RentalSpider_housefun(RedisSpider):
    name = 'housefun'
    allowed_domains = ['rent.housefun.com.tw']
    redis_key = f'{name}:start_urls'

    def make_request_from_data(self, data):
        url = data.decode('utf-8')
        return SeleniumRequest(url=url,
                               wait_time=10,
                               wait_until=EC.presence_of_element_located(
                                   (By.CSS_SELECTOR, 'article.DataList.both')),
                               callback=self.parse)

    def parse(self, response):
        while True:

            for house_info in response.css('article.DataList.both'):
                yield self.ParseHouse(house_info, response)

            # next page
            next_button = response.request.meta['driver'].find_elements(
                By.CSS_SELECTOR, 'ul.m-pagination-bd li.has-arrow a')[-1]
            onclick = next_button.get_attribute('onclick')
            if onclick:
                response.request.meta['driver'].execute_script(onclick)

                # Give the page some time to load
                time.sleep(5)

                new_response = response.replace(
                    body=response.request.meta['driver'].page_source)
                yield from self.parse(new_response)
            else:
                break

    def ParseHouse(self, house_info, response):
        property_info = defaultdict(lambda: None)
        property_info['title'] = house_info.css('h3 a::text').get().strip()
        price = house_info.css('span.infos.num::text').get().strip().split(
            ' ')[0]
        property_info['price'] = int(price.replace(',', ''))
        property_info['address'] = house_info.css(
            'address.addr::text').get().strip()
        info_list = house_info.css('span.infos::text').getall()
        for info in info_list:
            if '坪' in info:
                try:  # there are -- in the info
                    property_info['area'] = float(info.split('坪')[0])
                except:
                    pass
            elif '代理人' in info or '仲介' in info or '房東' in info:
                property_info['published_by'] = info
        try:
            property_info['floor'] = int(
                house_info.css('span.pattern::text').get().split('/')[0].split(
                    '：')[1].strip())
        except:
            pass

        # url
        property_info['url'] = response.url + house_info.css(
            'h3 a::attr(href)').get()
        property_info['img_url'] = house_info.css(
            'img::attr(src)').get().strip()

        item = RentalItem()
        item['title'] = property_info['title']
        item['price'] = property_info['price']
        item['address'] = property_info['address']
        item['published_by'] = property_info['published_by']
        item['area'] = property_info['area']
        item['floor'] = property_info['floor']
        item['house_type'] = property_info['house_type']
        item['url'] = property_info['url']
        item['img_url'] = property_info['img_url']
        item['coming_from'] = self.name
        return item

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()


if __name__ == '__main__':
    import sys
    sys.path.append(
        '/home/jeffbla/Project/RentHouseCrawler/RentHouseWebCrawler')

    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    process = CrawlerProcess(get_project_settings())
    process.crawl(RentalSpider_housefun)
    process.start()
