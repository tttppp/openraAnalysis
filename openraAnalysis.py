#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: Determine which player the DeployTransform command belongs to, and whether it's a deploy or an undeploy.

from collections import defaultdict
import os

SEASON = 7
POPULAR = 5

if SEASON == 6:
    path = '../../Downloads/Season6/'
elif SEASON == 7:
    path = '../../.openra/Replays/ra/release-20190314/'
else:
    print('Unknown season', SEASON)
    raise Exception

filenames = []
for root, dirs, files in os.walk(path):
    for filename in files:
        if filename.startswith('RAGL'):
            filenames.append(filename)

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
           b'facf': 'C?',
           b'mslf': 'M?',
           b'fpwr': 'P?',
           b'domf': 'R?',
           },{
           b'e1': 'm',
           b'e2': 'g',
           b'e3': 'r',
           b'e4': 'f',
           b'e6': 'e',
           b'e7': '!',
           b'medi': '+',
           b'mech': '*',
           b'dog': 'd',
           b'shok': 's',
           b'thf': 't',
           b'hijacker': 't',
           b'spy': '?',
           b'spy.england': '?',
           },{
           b'1tnk': 'lt',
           b'2tnk': 'mt',
           b'3tnk': 'ht',
           b'4tnk': 'ma',
           b'ftrk': 'ft',
           b'apc': 'ap',
           b'harv': 'ha',
           b'jeep': 'ra',
           b'arty': 'ar',
           b'ttnk': 'tt',
           b'v2rl': 'v2',
           b'mnly': 'ml',
           b'dtrk': 'dt',
           b'mrj': 'rj',
           b'mgg': 'mg',
           b'ctnk': 'ct',
           b'stnk': 'pt',
           b'truk': '$$',
           b'mcv': 'mc',
           },{
           b'hind': 'hi',
           b'heli': 'lb',
           b'tran': 'ch',
           b'yak': 'yk',
           b'mig': 'mi'
           }]

buildsByMap = defaultdict(list)
builds = []
for filename in filenames:
    f = open(path + filename, 'rb')
    x = f.read()
    f.close()
    
    mapTitleField = b'MapTitle: '
    mapTitleIndex = x.index(mapTitleField) + len(mapTitleField)
    mapTitle = x[mapTitleIndex:mapTitleIndex + x[mapTitleIndex:].index(b'\n')]
    
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
    
    def getStartProductionEvents(x, pos):
        l = x[pos + 5]
        item = x[pos + 6: pos + 6 + l]
        count = x[pos + 6 + l]
        q, item = outputEvent(item)
        return x[pos], q, [item] * count
    
    def getPlaceBuildingEvents(x, pos):
        l = x[pos + 11]
        item = x[pos + 12: pos + 12 + l]
        if SEASON == 6:
            l = x[pos + 19]
            item = x[pos + 20: pos + 20 + l]
        q, item = outputEvent(item)
        return x[pos], q, ['[' + item + ']']
    
    def getCancelProductionEvent(x, pos):
        l = x[pos + 5]
        item = x[pos + 6: pos + 6 + l]
        count = x[pos + 6 + l]
        q, item = outputEvent(item)
        return x[pos], q, [item] * count
    
    events = defaultdict(lambda : defaultdict(list))
    startProductionTerm = b'StartProduction'
    placeBuildingTerm = b'PlaceBuilding'
    cancelProductionTerm = b'CancelProduction'
    pos = startGame
    build = defaultdict(list)
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
    
    for player, eventList in events.items():
        for q, queue in eventList.items():
            #print(player, q, ','.join(queue))
            pass
        #if ''.join(build[player]).startswith('[PP][Rf][WF][Rf][PP][Rx]'):
        #    print(filename, mapTitle)
        builds.append(build[player])
        buildsByMap[mapTitle].append(build[player])

print(len(builds))

def buildToStr(build):
    return ''.join(build)

def findPopularBuilds(builds):
    buildTree = defaultdict(lambda : defaultdict(list))
    buildTree[0][''] = builds
    for depth in range(100):
        for priorBuilt, oldBuilds in buildTree[depth].items():
            newBuildIsPopular = False
            for build in oldBuilds:
                shallowBuild = buildToStr(build[:depth + 1])
                buildTree[depth + 1][shallowBuild].append(build)
                if len(buildTree[depth + 1][shallowBuild]) >= POPULAR:
                    newBuildIsPopular = True
            if len(oldBuilds) >= POPULAR and not newBuildIsPopular:
                print(len(oldBuilds), priorBuilt)

for mapTitle in buildsByMap.keys():
    print('###', mapTitle, '###')
    findPopularBuilds(buildsByMap[mapTitle])
    
