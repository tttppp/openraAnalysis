#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: Determine which player the DeployTransform command belongs to, and whether it's a deploy or an undeploy.

from collections import defaultdict, Counter
import os, sys

SEASON = 9
POPULAR = 20
PREFIX = 'RAGL-'
#PREFIX = ''
ABRIDGE_OUTPUT = True
ITEM_TO_FIND = None

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

buildsByMap = defaultdict(list)
builds = []
unitList = defaultdict(list)
players = []
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
    #print(x[startGame:])

    def outputEvent(event):
        for q, queue in enumerate(itemMap):
            if event in queue.keys():
                return q, queue[event]
        print('UNKNOWN:', event.decode('utf-8'), 'in', filename)
        raise Exception
    
    #StartProduction\x03\x00\x00\x00$\x04powr\x01\x00\x00\x00\x07\x00\x00\x00\t
    #StartProduction\x03\x00\x00\x00,\x04powr\x01\x00\x00\x00\xTT\x03\x00\x00\t
    
    #PlaceBuilding\x03\x00\x00\x00e\x02\xGG\x00\x00\x00\x??\x00\x00\x00\x00\x00\x00\x00\x00\x04powr\x03\x00\x00\x00\x07\x00\x00\x00\t
    #PlaceBuilding\x03\x00\x00\x00e\x02\x00\x..\x90\x00\x00\x04proc\x03\x00\x00\x00\xTT\x03\x00\x00\t
    
    def getPos(x, term, start):
        try:
            return x[start:].index(term) + len(term) + start
        except ValueError:
            # No more terms found.
            return len(x)
    
    def getField(x, pos, field):
        start = getPos(x, field + b': ', playerPos)
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
                        'filename': filename,
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

for q in unitList.keys():
    print('~~~ Queue {} ~~~'.format(q))
    outStrs = []
    for item, count in Counter(unitList[q]).most_common():
        if '[' not in item or ']' not in item:
            outStrs.append('{}: {}'.format(item, count))
    print(', '.join(outStrs))

def buildToStr(build):
    return ''.join(build)

def findPopularBuilds(builds):
    buildTree = defaultdict(lambda : defaultdict(list))
    buildTree[0][''] = builds
    out = []
    for depth in range(100):
        for priorBuilt, oldBuilds in buildTree[depth].items():
            newBuildIsPopular = False
            for build in oldBuilds:
                shallowBuild = buildToStr(build[:depth + 1])
                buildTree[depth + 1][shallowBuild].append(build)
                if len(buildTree[depth + 1][shallowBuild]) >= POPULAR:
                    newBuildIsPopular = True
            if len(oldBuilds) >= POPULAR and not newBuildIsPopular:
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

# Determine who the players were
fingerprints = Counter(map(lambda p: p['fingerprint'], players))
playersByFingerprint = defaultdict(Counter)
for player in players:
    playersByFingerprint[player['fingerprint']][player['name']] += 1

mapPickCounter = Counter()
for mapTitle in buildsByMap.keys():
    mapPickCounter[mapTitle] += len(buildsByMap[mapTitle])
for mapTitle, count in mapPickCounter.most_common():
    print('### {} (Picked {} time(s)) ###'.format(mapTitle, count / 2))
    findPopularBuilds(buildsByMap[mapTitle])

print('--- Overall (Total {} game(s)) ---'.format(len(builds)))
allBuilds = []
for builds in buildsByMap.values():
    allBuilds += builds
findPopularBuilds(allBuilds)

def expand(item):
    return '{1}{0}'.format(item[0], item[1])

#print('---Overall Positions---')
positionCount = Counter()
for builds in buildsByMap.values():
    for build in builds:
        partialBuild = Counter()
        for building in build:
            partialBuild[building] += 1
            positionCount[''.join(map(str, sorted(map(expand, partialBuild.items()))))] += 1
for position, count in positionCount.items():
    if count > POPULAR:
#        print(count, position)
        pass
