import sqlite3
import numpy as np
import pickle
import os.path
from operator import itemgetter

from sklearn import svm
from sklearn.ensemble import RandomForestClassifier
from sklearn import linear_model
from sklearn.cluster import KMeans

def getData(conn, names1, names2, names1Recent, names2Recent, years, testYear, bagOfPlayers, previousN):
	if previousN == 0:
		cursor = conn.execute('SELECT AllGamesDetailed.season, AllGamesDetailed.id1, AllGamesDetailed.id2, CASE WHEN score1 > score2 THEN 1 ELSE 0 END, %s FROM AllGamesDetailed \
								JOIN AllTeamsConfTotal team_1 ON AllGamesDetailed.id1 = team_1.id AND AllGamesDetailed.season = team_1.season \
								JOIN AllTeamsConfTotal team_2 ON AllGamesDetailed.id2 = team_2.id AND AllGamesDetailed.season = team_2.season \
								WHERE (AllGamesDetailed.season IN (%s) or (AllGamesDetailed.season = %d and type != "NCAA")) and field IN ("H","A","N")' % (",".join(names1 + names2), ",".join(map(str,years)), testYear))
	else:
		cursor = conn.execute('SELECT AllGamesDetailed.season, AllGamesDetailed.id1, AllGamesDetailed.id2, CASE WHEN score1 > score2 THEN 1 ELSE 0 END, %s FROM AllGamesDetailed \
								JOIN AllTeamsConfTotal team_1 ON AllGamesDetailed.id1 = team_1.id AND AllGamesDetailed.season = team_1.season \
								JOIN AllTeamsConfTotal team_2 ON AllGamesDetailed.id2 = team_2.id AND AllGamesDetailed.season = team_2.season \
								JOIN RecentAvg%d team_1_recent ON AllGamesDetailed.id1 = team_1_recent.schoolid AND AllGamesDetailed.date = team_1_recent.date \
								JOIN RecentAvg%d team_2_recent ON AllGamesDetailed.id2 = team_2_recent.schoolid AND AllGamesDetailed.date = team_2_recent.date \
								WHERE (AllGamesDetailed.season IN (%s) or (AllGamesDetailed.season = %d and type != "NCAA")) and field IN ("H","A","N")' % (",".join(names1 + names1Recent + names2 + names2Recent),previousN, previousN, ",".join(map(str,years)), testYear))

	result = np.array(map(list, list(cursor)))
	seasons = result[:,0].astype(int)
	schoolIDs = result[:,1:3].astype(str)
	labels = result[:,3].astype(np.uint8)
	features = result[:,4:].astype(float)
	features = insertBagOfPlayersToFeatures(bagOfPlayers, seasons, schoolIDs, features)
	return labels, features

def getDataTesting(conn, names1, names2, names1Recent, names2Recent, years, bagOfPlayers, previousN):
	if previousN == 0:
		cursor = conn.execute('SELECT AllGamesDetailed.season, AllGamesDetailed.date, AllGamesDetailed.id1, AllGamesDetailed.id2, CASE WHEN score1 > score2 THEN 1 ELSE 0 END, %s FROM AllGamesDetailed \
								JOIN AllTeamsConfTotal team_1 ON AllGamesDetailed.id1 = team_1.id AND AllGamesDetailed.season = team_1.season \
								JOIN AllTeamsConfTotal team_2 ON AllGamesDetailed.id2 = team_2.id AND AllGamesDetailed.season = team_2.season \
								WHERE AllGamesDetailed.season IN (%s) and type = "NCAA"' % (",".join(names1 + names2), ",".join(map(str,years))))
	else:
		cursor = conn.execute('SELECT AllGamesDetailed.season, AllGamesDetailed.date, AllGamesDetailed.id1, AllGamesDetailed.id2, CASE WHEN score1 > score2 THEN 1 ELSE 0 END, %s FROM AllGamesDetailed \
								JOIN AllTeamsConfTotal team_1 ON AllGamesDetailed.id1 = team_1.id AND AllGamesDetailed.season = team_1.season \
								JOIN AllTeamsConfTotal team_2 ON AllGamesDetailed.id2 = team_2.id AND AllGamesDetailed.season = team_2.season \
								JOIN RecentAvg%d team_1_recent ON AllGamesDetailed.id1 = team_1_recent.schoolid AND AllGamesDetailed.date = team_1_recent.date \
								JOIN RecentAvg%d team_2_recent ON AllGamesDetailed.id2 = team_2_recent.schoolid AND AllGamesDetailed.date = team_2_recent.date \
								WHERE AllGamesDetailed.season IN (%s) and type = "NCAA"' % (",".join(names1 + names1Recent + names2 + names2Recent), previousN, previousN, ",".join(map(str,years))))

	result = np.array(map(list, list(cursor)))

	seasons = np.zeros(result.shape[0]/2, dtype = int)
	schoolIDs = []
	features = np.zeros((result.shape[0]/2, result.shape[1]- 5))
	labels = np.zeros(result.shape[0]/2, dtype = np.uint8)

	n = 0
	for i in xrange(result.shape[0]):
		if result[i, 4] == '-1':
			continue
		features[n,:] = result[i,5:].astype(np.float32)
		for j in xrange(i + 1, result.shape[0]):
			if result[i, 1] == result[j, 1] and result[i, 2] == result[j, 3] and result[i, 3] == result[j, 2]:
				result[j, 4] = '-1'
				break
		seasons[n] = result[i,0].astype(int)
		#schoolIDs[n] = result[i,2:4].astype(str)
		schoolIDs.append(result[i,2:4].astype(str))
		labels[n] = result[i,4].astype(np.uint8)
		n = n + 1
	schoolIDs = np.array(schoolIDs)
	features = insertBagOfPlayersToFeatures(bagOfPlayers, seasons, schoolIDs, features)
	#print features1
	#print features2
	return labels, features

def getModel(modelName, labels, features, retrain):
	classifer = None
	fileName = "./models/" + modelName + ".model"
	if not retrain and os.path.isfile(fileName):
		with open(fileName, 'r') as modelFile:
			classifer = pickle.load(modelFile)
			modelFile.close()
	elif modelName == 'svm_model_rbf':
		classifer = svm.SVC()
		classifer.fit(features, labels)
	elif modelName == 'random_forest':
		classifer = RandomForestClassifier()
		classifer.fit(features, labels)
	elif modelName == 'bayesian_ridge':
		classifer = linear_model.BayesianRidge()
		classifer.fit(features, labels)
	elif modelName == 'logistic_regression':
		classifer = linear_model.LogisticRegression()
		classifer.fit(features, labels)

	with open(fileName, 'w') as modelFile:
		pickle.dump(classifer, modelFile)
		modelFile.close()

	return classifer

def test(modelName, classifer, labels, features):
	prediction = classifer.predict(features)
	if modelName == "bayesian_ridge":
		prediction = np.rint(prediction)
	return len(prediction[prediction == labels])/float(len(prediction))

def test2(modelName, classifer, labels, features):
	proba1 = classifer.predict_proba(features)[:,1]
	#print proba1
	features = np.concatenate((features[:,(features.shape[1])/2:], features[:,:(features.shape[1])/2]), axis = 1)
	proba2 = (1 - classifer.predict_proba(features)[:,1])
	#print proba2
	proba = (proba1 + proba2) / 2
	prediction = np.zeros(labels.shape, dtype = np.uint8)
	prediction[proba > 0.5] = 1
	return len(prediction[prediction == labels])/float(len(prediction))


def getCorrelation(conn, names, years):
	cursor = conn.execute("SELECT score1, %s FROM allgame \
							JOIN allteamavg ON allgame.id1 = allteamavg.id AND allgame.season = allteamavg.year \
							WHERE season IN (%s)" % (",".join(map(lambda x: "allteamavg." + x, names)), ",".join(map(str,years))))
	result = np.array(map(list, list(cursor)))
	result = zip(names, np.corrcoef(result, rowvar = 0)[0][1:])
	result = sorted(result, key=lambda x: abs(x[1]), reverse = True)
	x = []
	for t in result:
		if abs(t[1]) > 0.2:
			x.append('\'' + t[0] + '\'')
			print t[0]
	print ','.join(x)

def getBagOfPlayers(conn, numClusters):
	cursor = conn.execute("SELECT * FROM AllPlayersAverage")
	result = np.array(map(list, list(cursor)))

	playersSeason = result[:,0].astype(int)
	playersSchoolID = result[:,1].astype(str)
	playersAvg = result[:,4:].astype(float)

	codebook = KMeans(n_clusters = numClusters)
	codebook.fit(playersAvg)
	# print np.bincount(codebook.predict(playersAvg), minlength = numClusters)
	# print playersAvg

	bagOfPlayers = {}

	for season in np.unique(playersSeason):
		for schoolID in np.unique(playersSchoolID):
			maskSeason = (playersSeason == season)
			maskSchool = (playersSchoolID == schoolID)
			maskSeasonSchool = maskSeason & maskSchool
			if np.count_nonzero(maskSeasonSchool) == 0:
				#print "No data %d %s" % (season, schoolID)
				continue
			seasonSchoolPlayersAvg = playersAvg[maskSeasonSchool]
			histogram = np.bincount(codebook.predict(seasonSchoolPlayersAvg), minlength = numClusters)
			bagOfPlayers[(season, schoolID)] = histogram / float(np.sum(histogram))

	# print bagOfPlayers[(2012,'air-force')]
	# print np.sum(bagOfPlayers[(2012,'air-force')])
	return bagOfPlayers

def insertBagOfPlayersToFeatures(bagOfPlayers, seasons, schoolIDs, features):
	if not bagOfPlayers:
		return features
	featuresNew = []
	for i in xrange(features.shape[0]):
		if (seasons[i], schoolIDs[i,0]) in bagOfPlayers and (seasons[i], schoolIDs[i,1]) in bagOfPlayers:
			featuresNew.append(np.concatenate((features[i,:features.shape[1]/2], bagOfPlayers[(seasons[i], schoolIDs[i,0])], features[i,features.shape[1]/2:], bagOfPlayers[(seasons[i], schoolIDs[i,1])])))
			#featuresNew.append(np.concatenate((bagOfPlayers[(seasons[i], schoolIDs[i,0])], bagOfPlayers[(seasons[i], schoolIDs[i,1])])))
		else:
			print "%d %s %s not found" % (seasons[i], schoolIDs[i,0], schoolIDs[i,1])
	return np.array(featuresNew)


def getSchoolFeatures(conn, names, schools, year, bagOfPlayers):
	cursor = conn.execute('SELECT id, %s FROM AllTeamsConfTotal \
							WHERE season = %d and id IN (%s)' % (",".join(names), year, ",".join(map(lambda x: '"' + x + '"',schools))))

	result = map(list, list(cursor))
	schoolFeatures = [None] * len(schools)#np.zeros((len(schools), len(result[0]) - 1))
	for data in result:
		i = schools.index(data[0])
		if bagOfPlayers:
			schoolFeatures[i] = np.concatenate((np.array(data[1:]), bagOfPlayers[year, data[0]]))
		else:
			schoolFeatures[i] = np.array(data[1:])
		# if (year, data[0]) in bagOfPlayers:
		# 	schoolFeatures[i,:] = schoolFeatures[i,:] + 
	#print schoolFeature[:5]
	return np.array(schoolFeatures)

def outputMatrix(conn, names, classifer, bagOfPlayers):
	schoolList = [
	'north-carolina',
	'florida-gulf-coast',
	'southern-california',
	'providence',
	'indiana',
	'chattanooga',
	'kentucky',
	'stony-brook',
	'notre-dame',
	'michigan',
	'west-virginia',
	'stephen-f-austin',
	'wisconsin',
	'pittsburgh',
	'xavier',
	'weber-state',
	'virginia',
	'hampton',
	'texas-tech',
	'butler',
	'purdue',
	'arkansas-little-rock',
	'iowa-state',
	'iona',
	'seton-hall',
	'gonzaga',
	'utah',
	'fresno-state',
	'dayton',
	'syracuse',
	'michigan-state',
	'middle-tennessee',
	'kansas',
	'austin-peay',
	'colorado',
	'connecticut',
	'maryland',
	'south-dakota-state',
	'california',
	'hawaii',
	'arizona',
	'wichita-state',
	'miami-fl',
	'buffalo',
	'iowa',
	'temple',
	'villanova',
	'north-carolina-asheville',
	'oregon',
	'holy-cross',
	'saint-josephs',
	'cincinnati',
	'baylor',
	'yale',
	'duke',
	'north-carolina-wilmington',
	'texas',
	'northern-iowa',
	'texas-am',
	'green-bay',
	'oregon-state',
	'virginia-commonwealth',
	'oklahoma',
	'cal-state-bakersfield'
	]

	schoolFeatures = getSchoolFeatures(conn, names, schoolList, 2016, bagOfPlayers)

	features = np.zeros((schoolFeatures.shape[0]*schoolFeatures.shape[0], schoolFeatures.shape[1]*2))
	n = 0;
	for i in xrange(len(schoolList)):
		for j in xrange(len(schoolList)):
			features[n,:] = np.concatenate((schoolFeatures[i], schoolFeatures[j]))
			n = n + 1

	proba = classifer.predict_proba(features)[:,1]
	matrix = np.reshape(proba, (len(schoolList), len(schoolList)))

	for row in xrange(len(schoolList)):
		matrix[row][row] = 0.5
		for col in xrange(row+1,len(schoolList)):
			matrix[row][col] = (matrix[row][col] + (1 - matrix[col][row])) / 2
			matrix[col][row] = 1 - matrix[row][col]
	data = matrix.tolist()

	rowAvg = []
	for i in range(len(data)):
		total = 0
		for j in range(len(data[i])):
			total +=  float(data[i][j])
		pass
		avg = total / len(data[i])
		rowAvg.append((i, schoolList[i], avg))
	rowAvg = sorted(rowAvg, key=itemgetter(2), reverse=True)

	schoolList = [a[1] for a in rowAvg]
	f1 = open("../visualization/SchoolList.csv", "w")
	f1.write(",".join(schoolList))
	f1.close()

	sortedData = [[]] * len(data)
	for i, e in enumerate(rowAvg):
		dstData = [d for d in data[e[0]]]
		srcData = data[e[0]]
		for j, f in enumerate(rowAvg):
			dstData[j] = srcData[f[0]]
		sortedData[i] = dstData
	data = sortedData

	f2 = open("../visualization/sorted.tsv", "w")
	f2.write("row_index" + "\t" + "col_index" + "\t" + "val" + "\n")
	for i in range(64):
		for j in range(64):
			f2.write(str(i) + "\t" + str(j) + "\t" + str(data[i][j]) + "\n")
	f2.close()

def main():
	enableBagOfPlayers = True
	bagN = 4
	previousN = 0

	conn = sqlite3.connect("../database/ncaa.db3")
	cursor = conn.execute("pragma table_info('AllTeamsConfTotal')")
	# print cursor.fetchall()
	# exit(0)

	names = []
	for item in cursor.fetchall():
		if item[1] in ['season', 'id', 'g', 'mp', 'opp_g', 'opp_mp']:
			continue
		elif item[2] == 'INT':
			if 'opp_' in item[1]:
				names.append(item[1]+'/opp_g')
			else:
				names.append(item[1]+'/g')
		else:
			names.append(item[1])

	#print names

	names1 = []
	names2 = []

	for name in names:
		i = name.find('/')
		if i < 0:
			names1.append("team_1." + name)
		else:
			names1.append("team_1." + name[:i+1] + "team_1." + name[i+1:])
	names2 = map(lambda x: x.replace("team_1", "team_2"), names1)
	# print names1
	# print names2

	cursor = conn.execute("pragma table_info('RecentAvg5')")
	namesRecent = []
	for item in cursor.fetchall():
		if item[1] in ['season', 'date', 'schoolid']:
			continue
		namesRecent.append(item[1])

	names1Recent = []
	names2Recent = []

	for name in namesRecent:
		names1Recent.append("team_1_recent." + name)
	names2Recent = map(lambda x: x.replace("team_1", "team_2"), names1Recent)
	#print names1Recent
	#print names2Recent


	# modelName = 'svm_model_rbf'
	# modelName = 'random_forest'
	# modelName = 'bayesian_ridge'
	modelName = 'logistic_regression'

	np.random.seed(32)
	bagOfPlayers = None
	if enableBagOfPlayers:
		bagOfPlayers = getBagOfPlayers(conn, bagN)

	allYears = [2011, 2012, 2013, 2014, 2015, 2016]
	testingAccuracySum = 0.0;

	for testYear in allYears:
		trainYears = allYears[:]
		trainYears.remove(testYear)
		labelsTrain, featuresTrain = getData(conn, names1, names2, names1Recent, names2Recent, trainYears, testYear, bagOfPlayers, previousN)
		labelsTest, featuresTest = getDataTesting(conn, names1, names2, names1Recent, names2Recent, [testYear], bagOfPlayers, previousN)
		classifer = getModel(modelName, labelsTrain, featuresTrain, True)
		trainingAccuracy = test(modelName, classifer, labelsTrain, featuresTrain)
		testingAccuracy = test2(modelName, classifer, labelsTest, featuresTest)
		print "%d Training accuracy = %f, Testing accuracy = %f" % (testYear, trainingAccuracy, testingAccuracy)
		testingAccuracySum = testingAccuracySum + testingAccuracy
	print "Average Testing Accuracy = %f" % (testingAccuracySum / len(allYears))

	if previousN == 0:
		outputMatrix(conn, names, classifer, bagOfPlayers)
	else:
		print "Can not compute matrix for previousN != 0"


main()