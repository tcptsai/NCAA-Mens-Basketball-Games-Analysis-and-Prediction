The whole pipeline is: Scrapping -> Database -> Prediction -> Visualization

We have finished data scrapping, built database and predicted outcomes for you. You can just run a http server in visualization folder to see the heatmap.

If you want to run the whole pipeline from scratch, please follow the instructions below.

A. Scrapping
1. Install Scrapy on Python 2.7: http://scrapy.org/
2. In scrapping folder, run scrap.sh to scrap data.

B. Database
1. Install SQLite: https://www.sqlite.org/download.html
2. In database folder, run buildDB.sh to build database.
3. If you want to use the average status of previous N games as feature, run the following command:
	python compute_recent_avg.py N

C. Prediction
1. In prediction folder, run:
	python run.py

D. Visualization
1. In visualization, run a http sever.
2. Access heatmap.html through HTTP.
