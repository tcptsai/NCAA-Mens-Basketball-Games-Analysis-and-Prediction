import scrapy, time, os
from urlparse import urlparse, parse_qs

class GameSpider(scrapy.Spider):
    months = [11, 12, 1, 2, 3, 4]
    name = "allgamestatus"

    url = "http://www.sports-reference.com/cbb/boxscores/index.cgi?month=11&day=1&year="

    def __init__(self, *args, **kwargs):
        super(GameSpider, self).__init__(*args, **kwargs)
        self.start_urls = [self.url + self.begin]

    def parse(self, response):
        month = int(parse_qs(urlparse(response.url).query)['month'][0])
        year = int(parse_qs(urlparse(response.url).query)['year'][0])

        if month < 11:
            dirpath = "AllGameStatus/" + str(year - 1) + "_" + str(year)
        else:
            dirpath = "AllGameStatus/" + str(year) + "_" + str(year + 1)


        try: 
            os.makedirs(dirpath)
        except OSError:
            if not os.path.isdir(dirpath):
                raise

        domain = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(response.url))
        links = response.xpath('//a[text()="Final"]/@href').extract()
        for link in links:
            filepath = dirpath + '/' + link.split('/')[-1].split('.')[0]
            if os.path.isfile(filepath):
                continue
            req = scrapy.Request(domain + link, callback=self.parse_game)
            req.meta["filepath"] = filepath
            yield req
            #yield scrapy.Request(domain + link, callback=self.parse_game)

        next = response.xpath('//div[@id="page_content"]/a[contains(@href,"day")]/@href').extract()[-1]
        next_month = int(parse_qs(urlparse(next).query)['month'][0])

        if next_month in self.months:
            yield scrapy.Request(domain + next, callback=self.parse)
        elif year < int(self.end):
            print "scraping..." + str(year)
            yield scrapy.Request(self.url + str(year), callback=self.parse)


    def parse_game(self, response):
        with open(response.meta["filepath"], 'w') as f:
            output = ""
            tables = response.xpath('//table[contains(@class,"sortable") and not(contains(@id,"_advanced"))]')
            assert len(tables) == 2, "Error num of tables"

            def getRowContent(rowItems, defaultValue):
                return [item.xpath('.//text()').extract()[0] if item.xpath('.//text()').extract() else defaultValue for item in rowItems]

            for table in tables:
                school_id = table.xpath('@id').extract_first()
                thead_row = table.xpath('./thead/tr[not(contains(@class,"over_header"))]')[0]
                tbody_rows = table.xpath('./tbody/tr')
                assert len(tbody_rows) != 0, "Error num of tbody_rows"
                tfoot_row = table.xpath('./tfoot/tr')[0]

                output = output + school_id + "\n"
                #output = output + ', '.join(thead_row.xpath('./th/text()').extract()) + "\n"
                output = output + ', '.join(getRowContent(thead_row.xpath('./th'),u'')) + "\n"

                for row in tbody_rows:
                    row_class = row.xpath('@class').extract_first()
                    if "thead" in row_class:
                        ths = row.xpath('./th/text()').extract()
                        assert len(ths) != 0, "Error num of ths"
                        #output = output + ', '.join(ths) + "\n"
                        output = output + ', '.join(getRowContent(row.xpath('./th'),u'')) + "\n"
                    else:
                        tds = row.xpath('./td//text()').extract()
                        assert len(tds) != 0, "Error num of tds"
                        #output = output + ', '.join(tds) + "\n"
                        output = output + ', '.join(getRowContent(row.xpath('./td'),u'0')) + "\n"

                #output = output + ', '.join(tfoot_row.xpath('./td/text()').extract()) + "\n\n"
                output = output + ', '.join(getRowContent(tfoot_row.xpath('./td'),u'0')) + "\n"

            f.write(output)


