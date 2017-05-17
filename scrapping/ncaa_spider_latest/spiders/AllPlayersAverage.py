import scrapy, time, os
from urlparse import urlparse, parse_qs

# scrapy crawl allplayersaverage -a begin=2011 -a end=2016

class AllPlayersAverage(scrapy.Spider):

    name = "allplayersaverage"

    domain =  "http://www.sports-reference.com"
    url = "http://www.sports-reference.com/cbb/seasons/"
    url_end = "-school-stats.html"
    dirpath = "AllPlayersAverage"
    filename = "AllPlayersAverage.txt"

    def __init__(self, *args, **kwargs):

        super(AllPlayersAverage, self).__init__(*args, **kwargs)
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
            req = scrapy.Request(self.domain + school, callback=self.parse_player)
            req.meta["year"] = year
            req.meta["school"] = school.split('/')[-2]
            yield req

        if year < int(self.end):
            yield scrapy.Request(self.url + str(year + 1) + self.url_end, callback=self.parse)

    def parse_player(self, response):
        with open(self.dirpath + "/" + self.filename, 'a') as f:
            players = response.xpath('//table[contains(@id,"per_game_conf")]/tbody/tr')
            for player in players:
                if player:
                    output = str(response.meta["year"]) + "," + response.meta["school"] + "," + player.xpath('./td/a/@href').extract()[0].split('/')[-1][:-5]
                    numList = player.xpath('./td')[2:]
                    for number in numList:
                        temp = number.xpath('.//text()').extract()
                        if len(temp) == 0:
                            output = output + "," + str(0)
                        else:
                            output = output + "," + temp[0]
                    output = output + "\n"
                    f.write(output)