import scrapy, time, os
from urlparse import urlparse, parse_qs

# scrapy crawl allteamsconftotal -a begin=2011 -a end=2016

class AllTeamsConfTotal(scrapy.Spider):

    name = "allteamsconftotal"

    domain =  "http://www.sports-reference.com"
    url = "http://www.sports-reference.com/cbb/seasons/"
    url_end = "-school-stats.html"
    dirpath = "AllTeamsConfTotal"
    filename = "AllTeamsConfTotal.txt"

    def __init__(self, *args, **kwargs):

        super(AllTeamsConfTotal, self).__init__(*args, **kwargs)
        self.start_urls = [self.url + self.begin + self.url_end]

        try: 
            os.makedirs(self.dirpath)
        except OSError:
            if not os.path.isdir(self.dirpath):
                raise
        open(self.dirpath + '/' + self.filename, 'w').close()

    def parse(self, response):

        year = int(filter(str.isdigit, urlparse(response.url).path))

        schools = response.xpath('//table[contains(@id,"basic_school_stats")]/tbody/tr[not(contains(@class," thead over_header")) and not(contains(@class," thead"))]/td/a/@href').extract()

        for school in schools:
            req = scrapy.Request(self.domain + school, callback=self.parse_school)
            req.meta["year"] = year
            req.meta["school"] = school.split('/')[-2]
            yield req

        if year < int(self.end):
            yield scrapy.Request(self.url + str(year + 1) + self.url_end, callback=self.parse)

    def parse_school(self, response):
        with open(self.dirpath + "/" + self.filename, 'a') as f:
            row = response.xpath('//table[contains(@id,"team_stats_conf")]/tbody/tr')[0].xpath('./td//text()').extract()[1:] + response.xpath('//table[contains(@id,"team_stats_conf")]/tbody/tr')[2].xpath('./td//text()').extract()[1:]
            if row:
                if len(row) == 48:
                    output = str(response.meta["year"]) + "," + response.meta["school"] + "," + ','.join(row) + "\n"
                    f.write(output)