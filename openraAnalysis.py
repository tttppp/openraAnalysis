#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: Determine which player the DeployTransform command belongs to, and whether it's a deploy or an undeploy.

from collections import defaultdict, Counter
import os, sys
import requests

SEASON = 9
POPULAR = 20
PREFIX = 'RAGL-'
ABRIDGE_OUTPUT = True
ITEM_TO_FIND = None

POPULAR_FOR_PLAYER = 5
POPULAR_FOR_MAP = 10

if SEASON == 6:
    path = '../../Downloads/Season6/'
elif SEASON == 7:
    path = '../../.openra/Replays/ra/release-20190314/'
elif SEASON == 8:
    path = '../../.openra/Replays/ra/release-20190314/'
elif SEASON == 9:
    path = '../../.openra/Replays/ra/release-20200503/'
else:
    print('Unknown season', SEASON)
    raise Exception

FINGERPRINT_CACHE_FILE = 'fingerprint.cache'

filenames = []
for root, dirs, files in os.walk(path):
    for filename in files:
        if filename.startswith(PREFIX):
            filenames.append(filename)
#filenames = ['OpenRA-2019-08-21T181947Z.orarep']

itemMap = [{
           b'powr': 'PP',
           b'tent': 'Rx',
           b'barr': 'Rx',
           b'proc': 'Rf',
           b'weap': 'WF',
           b'fix': 'SD',
           b'dome': 'RD',
           b'hpad': 'HP',
           b'afld': 'AF',
           b'afld.ukraine': 'AF',
           b'apwr': 'AP',
           b'kenn': 'Ke',
           b'stek': 'TC',
           b'atek': 'TC',
           b'spen': 'SP',
           b'syrd': 'NY'
           },{
           b'pbox': 'PB',
           b'hbox': 'CP',
           b'gun': 'Tu',
           b'ftur': 'FT',
           b'tsla': 'Ts',
           b'agun': 'AA',
           b'sam': 'Sa',
           b'gap': 'GG',
           b'pdox': 'Cs',
           b'iron': 'IC',
           b'mslo': 'MS',
           b'fenc': '--',
           b'sbag': '--',
           b'brik': '==',
           b'silo': 'Si',
           # Fakes
           b'facf': 'C?', # Fake Conyard
           b'mslf': 'M?', # Fake Missile Silo
           b'fpwr': 'P?', # Fake Power Plant
           b'domf': 'R?', # Fake Radar Dome
           b'fixf': 'F?', # Fake Service Depot
           b'syrf': 'Y?', # Fake Naval Yard
           b'weaf': 'W?', # Fake War Factory
           b'tenf': 'X?', # Fake Barracks
           b'pdof': 'S?', # Fake chronosphere
           },{
           b'e1': 'm', # Rifle
           b'e2': 'g', # Gren
           b'e3': 'r', # Rocket
           b'e4': 'f', # Flamer
           b'e6': 'e', # Engineer
           b'e7': '!', # Tanya
           b'medi': '+', # Medic
           b'mech': '*', # Mechanic
           b'dog': 'd', # Dog
           b'shok': 's', # Shockie
           b'thf': 't', # Thief
           b'hijacker': 't', # Thief
           b'spy': '?', # Spy
           b'spy.england': '?', # Spy
           },{
           b'1tnk': 'lt', # Light Tank
           b'2tnk': 'mt', # Medium Tank
           b'3tnk': 'ht', # Heavy Tank
           b'4tnk': 'ma', # Mammoth Tank
           b'ftrk': 'ft', # Flak
           b'apc': 'ap', # APC
           b'harv': 'ha', # Harvester
           b'jeep': 'ra', # Ranger
           b'arty': 'ar', # Arti
           b'ttnk': 'tt', # Tesla Tank
           b'v2rl': 'v2', # V2
           b'mnly': 'ml', # Minelayer
           b'dtrk': 'dt', # Demo
           b'mrj': 'rj', # Radar Jammer
           b'mgg': 'mg', # Mobile Gap Generator
           b'ctnk': 'ct', # Chrono Tank
           b'stnk': 'pt', # Phase Transport
           b'qtnk': '!t', # Mad Tank
           b'truk': '$$', # Supply Truck
           b'mcv': 'mc', # MCV
           },{
           b'hind': 'hi', # Hind
           b'mh60': 'bh', # Blackhawk
           b'heli': 'lb', # Longbow
           b'tran': 'ch', # Chinook
           b'yak': 'yk', # Yak
           b'mig': 'mi' # Mig
           },{
           b'ss': 'sub',
           b'msub': 'msb',
           b'dd': 'des',
           b'ca': 'cru',
           b'lst': 'tra',
           b'pt': 'gun'
           }]

def bytesToInt(b):
    return int('0x' + b.encode('hex'), 16)

def loadCachedFingerprints():
    fingerprintToProfile = {}
    try:
        with open(FINGERPRINT_CACHE_FILE) as fingerprintCache:
            lines = fingerprintCache.readlines()
            for line in lines:
                fingerprint, profileID, profileName = line.strip().split('\t')
                fingerprintToProfile[fingerprint] = {'profileID': profileID, 'profileName': profileName}
    except IOError:
        # Assume that this is the first run and the fingerprint cache file doesn't exist yet.
        pass
    return fingerprintToProfile

def getAbbreviationsFromFilename(filename):
    potentialAbbreviations = []
    for bit in filename.split('-')[2:]:
        if len(bit) == 3:
            potentialAbbreviations.append(bit)
    return potentialAbbreviations

buildsByMap = defaultdict(list)
builds = []
queues = []
unitList = defaultdict(list)
players = []
fingerPrintToProfile = loadCachedFingerprints()
for filename in filenames:
    f = open(path + filename, 'rb')
    x = f.read()
    f.close()
    
    try:
        mapTitleField = b'MapTitle: '
        mapTitleIndex = x.index(mapTitleField) + len(mapTitleField)
        mapTitle = x[mapTitleIndex:mapTitleIndex + x[mapTitleIndex:].index(b'\n')]
    except:
        print('No map title found in {} - replay corrupted?'.format(filename))
        continue
    
    length = len(x)
    startGame = x.index(b'StartGame')

    def outputEvent(event):
        for q, queue in enumerate(itemMap):
            if event in queue.keys():
                return q, queue[event]
        print('UNKNOWN:', event.decode('utf-8'), 'in', filename)
        raise Exception
    
    def getPos(x, term, start):
        try:
            return x[start:].index(term) + len(term) + start
        except ValueError:
            # No more terms found.
            return len(x)
    
    def getField(x, pos, field):
        start = getPos(x, field + b': ', pos)
        end = getPos(x, b'\n', start)
        return x[start:end-1]
    
    def getPlayer(x, pos):
        if SEASON >= 9:
            return x[pos+1]
        return x[pos]
    
    def getStartProductionEvents(x, pos):
        l = bytesToInt(x[pos + 5])
        player = getPlayer(x, pos)
        item = x[pos + 6: pos + 6 + l]
        count = bytesToInt(x[pos + 6 + l])
        q, item = outputEvent(item)
        return player, q, [item] * count
    
    def getPlaceBuildingEvents(x, pos):
        l = bytesToInt(x[pos + 11])
        player = getPlayer(x, pos)
        item = x[pos + 12: pos + 12 + l]
        if SEASON == 6:
            l = bytesToInt(x[pos + 19])
            item = x[pos + 20: pos + 20 + l]
        q, item = outputEvent(item)
        return player, q, ['[' + item + ']']
    
    def getCancelProductionEvent(x, pos):
        l = bytesToInt(x[pos + 5])
        player = getPlayer(x, pos)
        item = x[pos + 6: pos + 6 + l]
        count = bytesToInt(x[pos + 6 + l])
        q, item = outputEvent(item)
        return player, q, [item] * count
    
    # Try to get player information.
    for playerId in [0, 1]:
        pos = -1
        while True:
            pos = getPos(x, b'Player@{}:'.format(playerId), pos + 1)
            if pos >= len(x):
                break
            playerPos = pos
        fingerprint = getField(x, playerPos, b'Fingerprint')
        if fingerprint != '':
            if not fingerPrintToProfile.has_key(fingerprint):
                response = requests.get('https://forum.openra.net/openra/info/' + fingerprint)
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line.startswith('ProfileID: '):
                        profileID = line[len('ProfileID: '):]
                    elif line.startswith('ProfileName: '):
                        profileName = line[len('ProfileName: '):]
                fingerPrintToProfile[fingerprint] = {'profileID': profileID, 'profileName': profileName}
                with open(FINGERPRINT_CACHE_FILE, 'a') as fingerprintCache:
                    fingerprintCache.write('{}\t{}\t{}\n'.format(fingerprint, profileID, profileName))
                
        name = getField(x, playerPos, b'Name')
        outcome = getField(x, playerPos, b'Outcome')
        clientIndex = getField(x, playerPos, b'ClientIndex')
        faction = getField(x, playerPos, b'FactionName')
        pos = -1
        while True:
            pos = getPos(x, b'Client@{}:'.format(clientIndex), pos + 1)
            if pos >= len(x):
                break
            clientPos = pos
        factionPick = getField(x, clientPos, b'Faction')
        
        players.append({'fingerprint': fingerprint,
                        'name': name,
                        'profileID': 'Unknown' if fingerprint == '' else fingerPrintToProfile[fingerprint]['profileID'],
                        'profileName': name if fingerprint == '' else fingerPrintToProfile[fingerprint]['profileName'],
                        'filename': filename,
                        'abbreviations': getAbbreviationsFromFilename(filename),
                        'faction': faction,
                        'factionPick': factionPick,
                        'outcome': outcome})
    
    events = defaultdict(lambda : defaultdict(list))
    startProductionTerm = b'StartProduction'
    placeBuildingTerm = b'PlaceBuilding'
    cancelProductionTerm = b'CancelProduction'
    pos = startGame
    build = defaultdict(list)
    try:
        while True:
            startProductionPos = getPos(x, startProductionTerm, pos)
            placeBuildingPos = getPos(x, placeBuildingTerm, pos)
            cancelProductionPos = getPos(x, cancelProductionTerm, pos)
            minPos = min(startProductionPos, placeBuildingPos, cancelProductionPos)
            if minPos == len(x):
                break
            if startProductionPos == minPos:
                player, q, eventList = getStartProductionEvents(x, minPos)
            if placeBuildingPos == minPos:
                player, q, eventList = getPlaceBuildingEvents(x, minPos)
                if q == 0:
                    for item in eventList:
                        build[player].append(item)
            if cancelProductionPos == minPos:
                player, q, eventList = getCancelProductionEvent(x, minPos)
                for item in eventList:
                    try:
                        events[player][q].remove(item)
                    except ValueError:
                        # Cancelled something that wasn't being produced.
                        pass
            else:
                events[player][q] += eventList
            pos = minPos
    except ZeroDivisionError:
        # Used for debugging.
        sys.tracebacklimit = 0
        raise Exception
    except:
        print('Skipping ' + filename)
    
    for player, eventList in events.items():
        for q, queue in eventList.items():
            # Can be used to find which game contains an unusual item.
            if ITEM_TO_FIND in queue:
                print(ITEM_TO_FIND, ' found in ', filename, mapTitle, 'Count:', queue.count(ITEM_TO_FIND))
            #print(player, q, ','.join(queue))
            unitList[q] += queue
        #if ''.join(build[player]).startswith('[PP][Rf][WF][Rf][PP][Rx]'):
        #    print(filename, mapTitle)
        builds.append(build[player])
        buildsByMap[mapTitle].append(build[player])
        queues.append(eventList)

# Faction win/loss ratio.
factionWin = Counter()
factionLoss = Counter()
for player in players:
    faction = player['faction']
    factionPick = player['factionPick']
    if player['outcome'] == 'Won':
        factionWin[faction] += 1
        factionWin[factionPick] += 1
        factionWin[(faction, factionPick)] += 1
    elif player['outcome'] == 'Lost':
        factionLoss[faction] += 1
        factionLoss[factionPick] += 1
        factionLoss[(faction, factionPick)] += 1
print('Faction        Win Rate       From Random A/S     Picked Win Rate')
for factionTuple in [('England', ('England', 'RandomAllies'), 'england'),
                    ('France', ('France', 'RandomAllies'), 'france'),
                    ('Germany', ('Germany', 'RandomAllies'), 'germany'),
                    ('RandomAllies', '', ''),
                    ('Russia', ('Russia', 'RandomSoviet'), 'russia'),
                    ('Ukraine', ('Ukraine', 'RandomSoviet'), 'ukraine'),
                    ('RandomSoviet', '', ''),
                    ('Random', '', '')]:
    factionReports = []
    for faction in factionTuple:
        if faction in factionWin or faction in factionLoss:
            factionReports.append('{: >3}/{: >3} {:0.0f}%'.format(factionWin[faction], (factionWin[faction] + factionLoss[faction]), factionWin[faction] * 100.0 / (factionWin[faction] + factionLoss[faction])))
        else:
            factionReports.append('    ---    ')
    print('{: <12} {}'.format(factionTuple[0], '        '.join(factionReports)))

for q in unitList.keys():
    print('~~~ Queue {} ~~~'.format(q))
    outStrs = []
    for item, count in Counter(unitList[q]).most_common():
        if '[' not in item or ']' not in item:
            wins = 0
            losses = 0
            for i, queue in enumerate(queues):
                if item in queue[q]:
                    if players[i]['outcome'] == 'Won':
                        wins += 1
                    elif players[i]['outcome'] == 'Lost':
                        losses += 1
            winRate = '{:0.0f}%'.format(wins * 100.0 / (wins + losses))
            outStrs.append('{}: {} ({} builds, {} wins)'.format(item, count, wins + losses, winRate))
    print(', '.join(outStrs))

def buildToStr(build):
    return ''.join(build)

def findPopularBuilds(builds, popularLimit=POPULAR):
    buildTree = defaultdict(lambda : defaultdict(list))
    buildTree[0][''] = builds
    out = []
    for depth in range(100):
        for priorBuilt, oldBuilds in buildTree[depth].items():
            newBuildIsPopular = False
            for build in oldBuilds:
                shallowBuild = buildToStr(build[:depth + 1])
                buildTree[depth + 1][shallowBuild].append(build)
                if len(buildTree[depth + 1][shallowBuild]) >= popularLimit:
                    newBuildIsPopular = True
            if len(oldBuilds) >= popularLimit and not newBuildIsPopular:
                out.append([priorBuilt, len(oldBuilds)])
    previousBuild = ''
    for outLine in sorted(out):
        if ABRIDGE_OUTPUT:
            i = 0
            outLineOriginal = outLine[0]
            while 4*i+3 < min(len(previousBuild), len(outLine[0])):
                if previousBuild[4*i:4*i+4] != outLine[0][4*i:4*i+4]:
                    break
                outLine[0] = outLine[0][:4*i] + ' .. ' + outLine[0][4*i+4:]
                i += 1
            previousBuild = outLineOriginal
        print('{} {}'.format(outLine[1], outLine[0]))

for profileName in set(map(lambda player: player['profileName'], players)):
    playerBuilds = []
    wins = 0
    losses = 0
    for i, player in enumerate(players):
        if player['profileName'] == profileName:
            playerBuilds.append(builds[i])
            if player['outcome'] == 'Won':
                wins += 1
            elif player['outcome'] == 'Lost':
                losses += 1
    winRate = '{:0.0f}%'.format(wins * 100.0 / (wins + losses))
    print('=== {} (Played {} game(s), Win Rate {}) ==='.format(profileName, len(playerBuilds), winRate))
    findPopularBuilds(playerBuilds, POPULAR_FOR_PLAYER)

mapPickCounter = Counter()
for mapTitle in buildsByMap.keys():
    mapPickCounter[mapTitle] += len(buildsByMap[mapTitle])
for mapTitle, count in mapPickCounter.most_common():
    print('### {} (Picked {} time(s)) ###'.format(mapTitle, count / 2))
    findPopularBuilds(buildsByMap[mapTitle], POPULAR_FOR_MAP)

print('--- Overall (Total {} game(s)) ---'.format(len(builds)))
findPopularBuilds(builds)

def expand(item):
    return '{1}{0}'.format(item[0], item[1])

#print('---Overall Positions---')
positionCount = Counter()
for buildsForMap in buildsByMap.values():
    for build in buildsForMap:
        partialBuild = Counter()
        for building in build:
            partialBuild[building] += 1
            positionCount[''.join(map(str, sorted(map(expand, partialBuild.items()))))] += 1
for position, count in positionCount.items():
    if count > POPULAR:
#        print(count, position)
        pass
