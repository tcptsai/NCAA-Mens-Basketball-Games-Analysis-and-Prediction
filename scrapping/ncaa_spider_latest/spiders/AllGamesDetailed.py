import scrapy, time, os
from urlparse import urlparse, parse_qs

# scrapy crawl allGamesdetailed -a begin=2011 -a end=2016

class AllGamesDetailed(scrapy.Spider):

    name = "allgamesdetailed"

    domain =  "http://www.sports-reference.com"
    url = "http://www.sports-reference.com/cbb/seasons/"
    url_end = "-school-stats.html"
    dirpath = "AllGamesDetailed"
    filepath = "AllGamesDetailed.txt"

    def __init__(self, *args, **kwargs):

        super(AllGamesDetailed, self).__init__(*args, **kwargs)
        self.start_urls = [self.url + self.begin + self.url_end]

        try: 
            os.makedirs(self.dirpath)
        except OSError:
            if not os.path.isdir(self.dirpath):
                raise
        open(self.dirpath + '/' + self.filepath, 'w').close()

    def parse(self, response):

        year = int(filter(str.isdigit, urlparse(response.url).path))

        schools = response.xpath('//table[contains(@id,"basic_school_stats")]/tbody/tr[not(contains(@class," thead over_header")) and not(contains(@class," thead"))]/td/a/@href').extract()

        for school in schools:
            req = scrapy.Request(self.domain + school[:-5] + "-schedule.html", callback=self.parse_school)
            req.meta["year"] = year
            req.meta["school"] = school.split('/')[-2]
            yield req

        if year < int(self.end):
            yield scrapy.Request(self.url + str(year + 1) + self.url_end, callback=self.parse)

    def parse_school(self, response):
        with open(self.dirpath + "/" + self.filepath, 'a') as f:
            rows = response.xpath('//table[contains(@id,"schedule")]/tbody/tr[not(contains(@class,"no_ranker thead"))]')
            if response.meta["year"] > 2014:
                for row in rows:
                    opp_url = row.xpath('./td')[6].xpath('./a/@href').extract()
                    if opp_url:
                        output = ""
                        output = str(response.meta["year"]) + "," + row.xpath('./td')[1].xpath('./a/@href').extract()[0].split('/')[-1][:10] + "," + response.meta["school"] + "," + opp_url[0].split('/')[-2] + "," + row.xpath('./td')[9].xpath('.//text()').extract()[0] + "," + row.xpath('./td')[10].xpath('.//text()').extract()[0] + "," + row.xpath('./td')[4].xpath('.//text()').extract()[0] + ","
                        field = row.xpath('./td')[5].xpath('.//text()').extract()
                        if not field:
                            output = output + "H\n"
                        elif field[0] == "@":
                            output = output + "A\n"
                        else:
                            output = output + "N\n"
                        f.write(output)
            else:
                for row in rows:
                    opp_url = row.xpath('./td')[4].xpath('./a/@href').extract()
                    if opp_url:
                        output = ""
                        output = str(response.meta["year"]) + "," + row.xpath('./td')[1].xpath('./a/@href').extract()[0].split('/')[-1][:10] + "," + response.meta["school"] + "," + opp_url[0].split('/')[-2] + "," + row.xpath('./td')[7].xpath('.//text()').extract()[0] + "," + row.xpath('./td')[8].xpath('.//text()').extract()[0] + "," + row.xpath('./td')[2].xpath('.//text()').extract()[0] + ","
                        field = row.xpath('./td')[3].xpath('.//text()').extract()
                        if not field:
                            output = output + "H\n"
                        elif field[0] == "@":
                            output = output + "A\n"
                        else:
                            output = output + "N\n"
                        f.write(output)