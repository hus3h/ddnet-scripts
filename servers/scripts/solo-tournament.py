#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ddnet import *
import sys
import msgpack
from cgi import escape

reload(sys)
sys.setdefaultencoding('utf8')

def printFooter():
  print """
  </section>
  </article>
  </body>
</html>"""

def printLadder(ranks):
  string = '<div class="ladder">\n'
  currentPos = 0
  currentRank = 0
  skips = 1
  lastPoints = 0
  if len(ranks) > 0:
    string += '<table class="tight">\n'
    for r in ranks:
      currentPos += 1
      if r[1] != lastPoints:
        lastPoints = r[1]
        currentRank += skips
        skips = 1
      else:
        skips += 1
      if currentPos > 20:
        string += '<tr class="allPoints" style="display: none">\n'
      else:
        string += '<tr>\n'
      string += u'  <td class="rankglobal">%d.</td><td class="points">%d points</td><td><a href="%s">%s</a></td></tr>' % (currentRank, r[1], escape(playerWebsite(u'%s' % r[0])), escape(r[0]))
    string += '</table>\n'
  string += '</div>'

  return string

con = mysqlConnect()

rankLadder = {}
teamrankLadder = {}
pointsLadder = {}
serversString = ""
players = {}
maps = {}
totalPoints = 0
serverRanks = {}

types = sys.argv[1:]

menuText = '<ul>\n'
for type in types:
  menuText += '<li><a href="#%s">%s Server</a></li>\n' % (type, type.title())
menuText += '</ul>'

print header("Quick Tournament #5 - DDraceNetwork", menuText, "")

f = open("tournament")
tournamentMaps = []
for line in f:
  tournamentMaps.append(line.rstrip('\n'))

with con:
  cur = con.cursor()
  cur.execute("set names 'utf8';");
  for type in types:
    totalServerPoints = 0
    serverRankLadder = {}
    serverTeamrankLadder = {}
    serverPointsLadder = {}

    f = open("types/%s/maps" % type, 'r')

    serversString += '<div id="%s" class="block div-tournament"><div class="back-up"><a href="#top">&#8593;</a></div><h2>%s Server</h2>\n' % (type, type.title())
    mapsString = ""

    maps[type] = []

    for line in f:
      words = line.rstrip('\n').split('|')
      if len(words) == 0 or not words[0].isdigit():
        continue

      stars = int(words[0])

      totalPoints += globalPoints(type, stars)
      totalServerPoints += globalPoints(type, stars)

      originalMapName = words[1]
      if len(words) > 2:
        mapperName = words[2]
      else:
        mapperName = ""

      if originalMapName not in tournamentMaps:
        continue

      mapName = normalizeMapname(originalMapName)

      maps[type].append(originalMapName)

      rows = []
      teamRanks = []
      namesOnMap = {}
      names = []
      time = 0
      currentRank = 1
      currentPosition = 1
      countTeamFinishes = 0
      skips = 1

      try:
        cur.execute("select Name, r.ID, Time, Timestamp from ((select distinct ID from record_teamrace where Map = '%s' ORDER BY Time) as l) left join (select * from record_teamrace where Map = '%s') as r on l.ID = r.ID order by r.Time, r.ID, Name;" % (con.escape_string(originalMapName), con.escape_string(originalMapName)))
        rows = cur.fetchall()
      except:
        pass
      if len(rows) > 0:
        ID = rows[0][1]

      for row in rows:
        if row[1] != ID:
          if currentPosition <= 20:
            fNames = []
            for name in names:
              fNames.append('<a href="%s">%s</a>' % (escape(playerWebsite(u'%s' % name)), escape(name)))
            teamRanks.append((currentRank, joinNames(fNames), time, timestamp))
            names = []

          countTeamFinishes += 1
          if row[2] != time:
            time = row[2]
            timestamp = row[3]
            currentRank += skips
            skips = 1
          else:
            skips += 1
          currentPosition += 1
          ID = row[1]

        if row[0] not in players:
          players[row[0]] = Player({})
        if originalMapName not in players[row[0]].maps:
          players[row[0]].maps[originalMapName] = PlayerMap(currentRank, 0, 0, 0, date(2015,10,10),  date(2016,10,10))

        if currentPosition > 20:
          continue

        time = row[2]
        timestamp = row[3]
        names.append(row[0])

        if row[0] in namesOnMap:
          continue

        namesOnMap[row[0]] = True

        if row[0] in teamrankLadder:
          teamrankLadder[row[0]] += points(currentRank)
        else:
          teamrankLadder[row[0]] = points(currentRank)

        if row[0] in serverTeamrankLadder:
          serverTeamrankLadder[row[0]] += points(currentRank)
        else:
          serverTeamrankLadder[row[0]] = points(currentRank)

      if currentPosition <= 20 and time > 0:
        fNames = []
        for name in names:
          fNames.append('<a href="%s">%s</a>' % (escape(playerWebsite(u'%s' % name)), escape(name)))
        teamRanks.append((currentRank, joinNames(fNames), time, timestamp))
        countTeamFinishes += 1

      rows = []
      ranks = []
      countFinishes = 0

      try:
        cur.execute("select l.Name, minTime, l.Timestamp, playCount, minTimestamp, maxTimestamp from (select * from record_race where Map = '%s') as l JOIN (select Name, min(Time) as minTime, count(*) as playCount, min(Timestamp) as minTimestamp, max(Timestamp) as maxTimestamp from record_race where Map = '%s' group by Name order by minTime ASC) as r on l.Time = r.minTime and l.Name = r.Name GROUP BY Name ORDER BY minTime;" % (con.escape_string(originalMapName), con.escape_string(originalMapName)))
        rows = cur.fetchall()
      except:
        pass

      countFinishes = len(rows)
      currentRank = 0
      currentPosition = 0
      lastTime = 0
      skips = 1

      for row in rows:
        if row[1] != lastTime:
          lastTime = row[1]
          currentRank += skips
          skips = 1
        else:
          skips += 1

        currentPosition += 1

        if row[0] in pointsLadder:
          pointsLadder[row[0]] += globalPoints(type, stars)
        else:
          pointsLadder[row[0]] = globalPoints(type, stars)

        if row[0] in serverPointsLadder:
          serverPointsLadder[row[0]] += globalPoints(type, stars)
        else:
          serverPointsLadder[row[0]] = globalPoints(type, stars)

        if row[0] not in players:
          players[row[0]] = Player({})
        if originalMapName not in players[row[0]].maps:
          players[row[0]].maps[originalMapName] = PlayerMap(0, currentRank, globalPoints(type, stars), row[3], row[4], row[1])
        else:
          players[row[0]].maps[originalMapName] = PlayerMap(players[row[0]].maps[originalMapName][0], currentRank, globalPoints(type, stars), row[3], row[4], row[1])

        if currentPosition > 20:
          continue

        ranks.append((currentRank, row[0], row[1], row[2], row[3]))

        if row[0] in rankLadder:
          rankLadder[row[0]] += points(currentRank)
        else:
          rankLadder[row[0]] = points(currentRank)

        if row[0] in serverRankLadder:
          serverRankLadder[row[0]] += points(currentRank)
        else:
          serverRankLadder[row[0]] = points(currentRank)

      if countTeamFinishes == 1:
        mbS = ""
      else:
        mbS = "s"

      if countFinishes == 1:
        mbS2 = ""
      else:
        mbS2 = "s"

      avgTime = ""
      finishTimes = ""

      try:
        cur.execute("select avg(Time), min(Timestamp), max(Timestamp) from record_race where Map = '%s';" % con.escape_string(originalMapName))
        rows = cur.fetchall()
        avgTime = " (average time: %s)" % formatTime(rows[0][0])
        finishTimes = "first finish: %s, last finish: %s" % (escape(formatDate(rows[0][1])), escape(formatDate(rows[0][2])))
      except:
        pass

      biggestTeam = ""

      try:
        cur.execute("select count(Name) from record_teamrace where Map = '%s' group by ID order by count(Name) desc limit 1;" % con.escape_string(originalMapName))
        rows = cur.fetchall()
        biggestTeam = " (biggest team: %d)" % rows[0][0]
      except:
        pass

      if not mapperName:
        mbMapperName = ""
      else:
        mbMapperName = "<strong>by %s</strong><br/>" % escape(mapperName)

      formattedMapName = escape(originalMapName)
      mbMapInfo = ""
      try:
        with open('maps/%s.msgpack' % originalMapName, 'rb') as inp:
          unpacker = msgpack.Unpacker(inp)
          width = unpacker.unpack()
          height = unpacker.unpack()
          tiles = unpacker.unpack()

          formattedMapName = '<span title="%dx%d">%s</span>' % (width, height, escape(originalMapName))

          mbMapInfo = "<br/>"
          for tile in sorted(tiles.keys(), key=lambda i:order(i)):
            mbMapInfo += '<span title="%s"><img alt="%s" src="/tiles/%s.png" width="32" height="32"/></span> ' % (description(tile), description(tile), tile)
      except IOError:
        pass

      mapsString += u'<div class="block3 info" id="map-%s"><h3 class="inline">%s</h3><p class="inline">%s</p><p>Difficulty: %s, Points: %d<br/><a href="/maps/?map=%s"><img class="screenshot" alt="Screenshot" src="/ranks/maps/%s.png" /></a>%s<br/><span title="%s">%d tee%s finished%s</span></div>\n' % (escape(mapName), formattedMapName, mbMapperName, escape(renderStars(stars)), globalPoints(type, stars), quote_plus(originalMapName), escape(mapName), mbMapInfo, finishTimes, countFinishes, mbS2, escape(avgTime))
      #mapsString += printTeamRecords("Team Records", "teamrecords", teamRanks)
      mapsString += printSoloRecords("Records", "records", ranks)
      mapsString += '<br/>\n'

    serverPointsRanks = sorted(serverPointsLadder.items(), key=lambda r: r[1], reverse=True)
    serverTeamrankRanks = sorted(serverTeamrankLadder.items(), key=lambda r: r[1], reverse=True)
    serverRankRanks = sorted(serverRankLadder.items(), key=lambda r: r[1], reverse=True)

    serverRanks[type] = (totalServerPoints, serverPointsRanks, serverTeamrankRanks, serverRankRanks)

    serversString += '<br/><div class="all-%s" style="display: ">\n' % type
    serversString += mapsString
    serversString += '</div>\n'
    serversString += '</div>\n'

#pointsRanks = sorted(pointsLadder.items(), key=lambda r: r[1], reverse=True)
#teamrankRanks = sorted(teamrankLadder.items(), key=lambda r: r[1], reverse=True)
#rankRanks = sorted(rankLadder.items(), key=lambda r: r[1], reverse=True)

print '<div id="global" class="block div-tournament"><h2>Quick Tournament #5</h2>'
print '<p>This tournament was played on 2014-03-30 from 22:00 to 22:00 CEST.</p>'
#print printLadder(teamrankRanks)
print '</div>'
print '<div id="serverranks" style="display: ">'
print serversString
print '</div>'
printFooter()
