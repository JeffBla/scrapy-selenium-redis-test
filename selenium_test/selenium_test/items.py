import scrapy


class RentalItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    address = scrapy.Field()
    published_by = scrapy.Field()
    area = scrapy.Field()
    floor = scrapy.Field()
    house_type = scrapy.Field()
    url = scrapy.Field()
    img_url = scrapy.Field()
    coming_from = scrapy.Field()
