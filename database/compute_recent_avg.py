import sqlite3
import numpy as np
import os, sys

def computeRecentAvg(conn, tableName, season, date, schoolid, names, N):
	cursor = conn.execute("SELECT %s FROM AllGamesStats \
            WHERE season = %d AND date < '%s' AND schoolid = '%s' AND type != 'NCAA'\
				ORDER BY date DESC LIMIT %d" % (','.join(names), season, date, schoolid, N))
	result = np.array(map(list, list(cursor))).astype(float)
	if result.shape[0] < N:
		return
	avg = np.average(result, axis = 0)
	# print "%d %s %s" % (season, date, schoolid)
	# print result
	# print avg
	conn.execute("INSERT INTO %s VALUES (%d, '%s', '%s', %s)" % (tableName, season, date, schoolid, ",".join(map(str, avg))))

if len(sys.argv) < 2:
   print "Please provide N"
   exit(-1)

N = int(sys.argv[1])
conn = sqlite3.connect("./ncaa.db3")
tableName = "RecentAvg%d" % (N)
conn.execute("DROP TABLE IF EXISTS %s" % (tableName))
conn.execute("CREATE TABLE %s (\n\
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
)" % (tableName))

cursor = conn.execute("pragma table_info('AllGamesStats')")
names = []
for item in cursor.fetchall():
	if item[1] in ['season', 'date', 'schoolid', 'type']:
		continue
	names.append(item[1])

#print names

cursor = conn.execute("SELECT season, date, schoolid FROM AllGamesStats")
result = np.array(map(list, list(cursor)))

for item in result:
	computeRecentAvg(conn, tableName, item[0].astype(int), item[1], item[2], names, N)

# print result

conn.commit()