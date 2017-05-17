import sqlite3
import os

def inputGameToDB(conn, fileName):
	with open(fileName, 'r') as f:
		lines = f.readlines()
		i = 0
		n = 2
		date = fileName.split('/')[-1][:10]
		season = int(fileName.split('/')[-2][-4:])
		#print "%s %d %s" % (date, season, schoolid)
		while n and i < len(lines):
			#print lines[i]
			schoolid = lines[i].rstrip()
			i = i + 1
			while i < len(lines):
				if 'School Totals' in lines[i]:
					#print lines[i]
					data = lines[i].rstrip().split(',')
					data = map(float, data[1:])
					break
				i = i + 1
			if len(data) != 22:
				print "%s: %s wrong data num" % (fileName, name)
			#print "INSERT INTO AllGamesStatsTemp VALUES (%d, '%s', '%s', %s)" % (season, date, schoolid, ",".join(map(str, data)))
			conn.execute("INSERT INTO AllGamesStatsTemp VALUES (%d, '%s', '%s', %s)" % (season, date, schoolid, ",".join(map(str, data))))
			i = i + 1
			n = n - 1
		if n != 0:
			print "%s: wrong school num" % (fileName)

conn = sqlite3.connect("./ncaa.db3")
conn.execute("DROP TABLE IF EXISTS AllGamesStatsTemp")
conn.execute("CREATE TABLE AllGamesStatsTemp (\n\
   season INT,\n\
   date TEXT,\n\
   schoolid TEXT,\n\
   mp DECIMAL,\n\
   fg DECIMAL,\n\
   fga DECIMAL,\n\
   fgp DECIMAL,\n\
   twp DECIMAL,\n\
   twpa DECIMAL,\n\
   twpp DECIMAL,\n\
   thp DECIMAL,\n\
   thpa DECIMAL,\n\
   thpp DECIMAL,\n\
   ft DECIMAL,\n\
   fta DECIMAL,\n\
   ftp DECIMAL,\n\
   orb DECIMAL,\n\
   drb DECIMAL,\n\
   trb DECIMAL,\n\
   ast DECIMAL,\n\
   stl DECIMAL,\n\
   blk DECIMAL,\n\
   tov DECIMAL,\n\
   pf DECIMAL,\n\
   pts DECIMAL\n\
)")

for dirPath, dirNames, fileNames in os.walk("../scrapping/AllGameStatus/"):
	for fileName in fileNames:
		if fileName[0] == '.':
			continue
		inputGameToDB(conn, os.path.join(dirPath, fileName))

conn.execute("DROP TABLE IF EXISTS AllGamesStats")
conn.execute("CREATE TABLE AllGamesStats (\n\
   season INT,\n\
   date TEXT,\n\
   schoolid TEXT,\n\
   type TEXT,\n\
   mp DECIMAL,\n\
   fg DECIMAL,\n\
   fga DECIMAL,\n\
   fgp DECIMAL,\n\
   twp DECIMAL,\n\
   twpa DECIMAL,\n\
   twpp DECIMAL,\n\
   thp DECIMAL,\n\
   thpa DECIMAL,\n\
   thpp DECIMAL,\n\
   ft DECIMAL,\n\
   fta DECIMAL,\n\
   ftp DECIMAL,\n\
   orb DECIMAL,\n\
   drb DECIMAL,\n\
   trb DECIMAL,\n\
   ast DECIMAL,\n\
   stl DECIMAL,\n\
   blk DECIMAL,\n\
   tov DECIMAL,\n\
   pf DECIMAL,\n\
   pts DECIMAL\n\
)")

cursor = conn.execute("pragma table_info('AllGamesStatsTemp')")
names = []
for item in cursor.fetchall():
	if item[1] in ['season', 'date', 'schoolid']:
		continue
	names.append('AllGamesStatsTemp.' + item[1])

conn.execute("INSERT INTO AllGamesStats SELECT AllGamesStatsTemp.season, AllGamesStatsTemp.date, AllGamesStatsTemp.schoolid, type, %s FROM AllGamesStatsTemp \
			JOIN AllGamesDetailed ON AllGamesStatsTemp.schoolid = AllGamesDetailed.id1 AND AllGamesStatsTemp.date = AllGamesDetailed.date\
			" % (",".join(names)))
conn.execute("DROP TABLE IF EXISTS AllGamesStatsTemp")

conn.commit()