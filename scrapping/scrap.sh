#!/bin/bash

scrapy crawl allgamesdetailed -a begin=2011 -a end=2016
scrapy crawl allplayersaverage -a begin=2011 -a end=2016
scrapy crawl allteamsconftotal -a begin=2011 -a end=2016
scrapy crawl allgamestatus -a begin=2010 -a end=2016
