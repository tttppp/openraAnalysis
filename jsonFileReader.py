#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter
import json
import math
import sys
import re

# The prefix that the RAGL files all begin with.
PREFIX = 'RAGL-'
# Which RAGL season to analyse replays for (leave blank for all).
SEASON = int(sys.argv[1]) if len(sys.argv) > 1 else None
if SEASON is not None:
    PREFIX += 'S{:02d}-'.format(SEASON)
# Which division to analyse replays for (leave blank for all).
DIVISION = sys.argv[2] if len(sys.argv) > 2 else None
if DIVISION is not None:
    PREFIX += '{}-'.format(DIVISION)

ALL_SEASONS = range(1,10+1)
#ALL_SEASONS = ['RATL']

itemNames = {'!': 'Tanya',
 '!t': 'Mad Tank',
 '$$': 'Supply Truck',
 '*': 'Mechanic',
 '+': 'Medic',
 '--': 'Fence',
 '==': 'Concrete Wall',
 '?': 'Spy',
 'A?': 'Fake Advance Power',
 'AA': 'AA Gun',
 'AF': 'Airfield',
 'AP': 'Advanced Power Plant',
 'C?': 'Fake Conyard',
 'CP': 'Camo Pillbox',
 'Cs': 'Chronosphere',
 'F?': 'Fake Service Depot',
 'FT': 'Flame Tower',
 'GG': 'Gap Generator',
 'HP': 'Helipad',
 'IC': 'Iron Curtain',
 'Ke': 'Kennel',
 'M?': 'Fake Missile Silo',
 'MS': 'Missile Silo',
 'NY': 'Naval Yard',
 'P?': 'Fake Power Plant',
 'PB': 'Pillbox',
 'PP': 'Power Plant',
 'R?': 'Fake Radar Dome',
 'RD': 'Radar Dome',
 'Rf': 'Refinery',
 'Rx': 'Barracks',
 'S?': 'Fake Chronosphere',
 'SD': 'Service Depot',
 'SP': 'Sub Pen',
 'Sa': 'SAM Site',
 'Si': 'Silo',
 'T?': 'Fake Tech Center',
 'TC': 'Tech Centre',
 'Ts': 'Teslacoil',
 'Tu': 'Turret',
 'W?': 'Fake War Factory',
 'WF': 'War Factory',
 'X?': 'Fake Barracks',
 'Y?': 'Fake Naval Yard',
 'ap': 'APC',
 'ar': 'Arti',
 'bh': 'Blackhawk',
 'ch': 'Chinook',
 'cru': 'Cruiser',
 'ct': 'Chrono Tank',
 'd': 'Dog',
 'des': 'Destroyer',
 'dt': 'Demo',
 'e': 'Engineer',
 'f': 'Flamer',
 'ft': 'Flak',
 'g': 'Gren',
 'gun': 'Gunboat',
 'ha': 'Harvester',
 'ht': 'Heavy Tank',
 'lb': 'Longbow',
 'lt': 'Light Tank',
 'm': 'Rifle',
 'ma': 'Mammoth Tank',
 'mc': 'MCV',
 'mg': 'Mobile Gap Generator',
 'mi': 'Mig',
 'ml': 'Minelayer',
 'msb': 'Missile Sub',
 'mt': 'Medium Tank',
 'pt': 'Phase Transport',
 'r': 'Rocket',
 'ra': 'Ranger',
 'rj': 'Radar Jammer',
 's': 'Shockie',
 'sub': 'Submarine',
 't': 'Thief',
 'tra': 'Naval Transport',
 'tt': 'Tesla Tank',
 'v2': 'V2',
 'yk': 'Yak'}

all_builds = []
all_players = []
all_chats = []
all_queues = []
all_actions = []
for season in ALL_SEASONS:
    with open('builds.{}.json'.format(season)) as f:
        all_builds += json.load(f)
    with open('players.{}.json'.format(season)) as f:
        all_players += json.load(f)
    with open('chats.{}.json'.format(season)) as f:
        all_chats += json.load(f)
    with open('queues.{}.json'.format(season)) as f:
        all_queues += json.load(f)
    with open('actions.{}.json'.format(season)) as f:
        all_actions += json.load(f)

def getDataFor(season=None, division=None):
    builds = list(all_builds)
    players = list(all_players)
    chats = list(all_chats)
    queues = list(all_queues)
    actions = list(all_actions)
    
    # The prefix that the RAGL files all begin with.
    prefix = 'RAGL-'
    if season is not None:
        prefix += 'S{:02d}-'.format(season)
    # Which division to analyse replays for (leave blank for all).
    if division is not None:
        if season is not None:
            prefix += '{}-'.format(division)
        else:
            print('Unsupported request to filter by division but not season: {} {}'.format(season, division))
            sys.exit(1)
    
    toDelete = []
    for i in range(len(players)):
        if not players[i]['filename'].startswith(prefix):
            toDelete.append(i)
    for i in reversed(toDelete):
        del builds[i]
        del players[i]
        # Chats are per game, not per player.
        if i % 2 == 0:
            del chats[i//2]
        del queues[i]
        del actions[i]
    if len(players) == 0:
        print('WARNING: No builds to analyse for {} {}'.format(season, division))
    return builds, players, chats, queues, actions

def getDataForRATL(division, season='01'):
    builds = list(all_builds)
    players = list(all_players)
    chats = list(all_chats)
    queues = list(all_queues)
    actions = list(all_actions)
    
    # The prefix that the RAGL files all begin with.
    prefix = 'RATL-'
    if season is not None:
        prefix += 'S{}-'.format(season)
    # Which division to analyse replays for (leave blank for all).
    if division is not None:
        if season is not None:
            prefix += '{}-'.format(division)
        else:
            print('Unsupported request to filter by division but not season: {} {}'.format(season, division))
            sys.exit(1)
    
    toDelete = []
    for i in range(len(players)):
        if not players[i]['filename'].startswith(prefix):
            toDelete.append(i)
    for i in reversed(toDelete):
        del builds[i]
        del players[i]
        # Chats are per game, not per player.
        if i % 2 == 0:
            del chats[i/2]
        del queues[i]
        del actions[i]
    if len(players) == 0:
        print('WARNING: No builds to analyse for {} {}'.format(season, division))
    return builds, players, chats, queues, actions

def getFactionType(faction):
    if faction in ['England', 'France', 'Germany']:
        return 'Allies'
    elif faction in ['Russia', 'Ukraine']:
        return 'Soviet'
    raise Exception('Unexpected faction type: ' + faction)

def mean(values):
    if len(values) == 0:
        raise Exception('Cannot compute mean of empty list')
    return sum(values) * 1.0 / len(values)

def standardError(successes, trails):
    p = successes * 1.0 / trails
    return math.sqrt((p * (1-p)) / (trails + 1))

def findGames(filterFn, formatFns):
    for season in ALL_SEASONS:
        builds, players, chats, queues, actions = getDataFor(season)
        for i in range(len(builds)):
            entry = {'build': builds[i], 'player': players[i], 'chat': chats[i // 2],
                     'queue': queues[i], 'action': actions[i], 'season': season, 'i': i}
            if filterFn(entry):
                displayValues = [str(formatFn(entry)) for formatFn in formatFns]
                print('{},{}'.format(entry['player']['filename'], ','.join(displayValues)))
    print('')

def findMatches(filterFn, formatFns):
    for season in ALL_SEASONS:
        builds, players, chats, queues, actions = getDataFor(season)
        for i in range(len(builds) // 2):
            entry = {'builds': builds[2*i:2*i+2], 'players': players[2*i:2*i+2], 'chat': chats[i],
                     'queues': queues[2*i:2*i+2], 'actions': actions[2*i:2*i+2], 'season': season, 'i': i}
            if filterFn(entry):
                displayValues = [str(formatFn(entry)) for formatFn in formatFns]
                print('{},{}'.format(entry['players'][0]['filename'], ','.join(displayValues)))
    print('')

def getFeatureCounts(featureFn, filterFn):
    categories = set()
    for season in ALL_SEASONS:
        builds, players, chats, queues, actions = getDataFor(season)
        counts = Counter()
        for i in range(len(builds)):
            entry = {'build': builds[i], 'player': players[i], 'chat': chats[i // 2],
                     'queue': queues[i], 'action': actions[i], 'season': season, 'i': i}
            if filterFn(entry):
                category = featureFn(entry)
                categories.add(category)
        values = []
        for j in range(columns):
            if perEntry:
                counts[j] *= 1.0 / len(builds)
            values.append(valueFn(counts[j]))
        print('{},{}'.format(season, ','.join(values)))
    print('')

def getCounts(functions, valueFn = lambda x: '{:d}'.format(x), perEntry=False):
    columns = len(functions)
    for season in ALL_SEASONS:
        builds, players, chats, queues, actions = getDataFor(season)
        counts = Counter()
        for i in range(len(builds)):
            entry = {'build': builds[i], 'player': players[i], 'chat': chats[i // 2],
                     'queue': queues[i], 'action': actions[i], 'season': season, 'i': i}
            for j, fn in enumerate(functions):
                counts[j] += fn(entry)
        values = []
        for j in range(columns):
            if perEntry:
                counts[j] *= 1.0 / len(builds)
            values.append(valueFn(counts[j]))
        print('{},{}'.format(season, ','.join(values)))
    print('')

PERCENT = lambda x: '{:.4f}'.format(100 * x)

def perPlayerEvaluation(season, functions, denominatorIsFilter):
    builds, players, chats, queues, actions = getDataFor(season)
    numerators = [0] * len(functions)
    denominators = [0] * len(functions)
    for i in range(len(builds)):
        entry = {'build': builds[i], 'player': players[i], 'chat': chats[i // 2],
                 'queue': queues[i], 'action': actions[i], 'season': season, 'i': i}
        
        for j, (numeratorFn, denominatorFn) in enumerate(functions):
            denominator = denominatorFn(entry)
            if denominator > 0 or not denominatorIsFilter:
                numerators[j] += numeratorFn(entry)
                denominators[j] += denominator
    return numerators, denominators

def perMatchEvaluation(season, functions, denominatorIsFilter):
    builds, players, chats, queues, actions = getDataFor(season)
    numerators = Counter()
    denominators = Counter()
    for i in range(len(builds) // 2):
        entry = {'builds': builds[2*i:2*i+2], 'players': players[2*i:2*i+2], 'chat': chats[i],
                 'queues': queues[2*i:2*i+2], 'actions': actions[2*i:2*i+2], 'season': season, 'i': i}

        for j, (numeratorFn, denominatorFn) in enumerate(functions):
            denominator = denominatorFn(entry)
            if denominator > 0 or not denominatorIsFilter:
                numerators[j] += numeratorFn(entry)
                denominators[j] += denominator
    return numerators, denominators

def quotientValues(numerators, denominators, valueFn, includeError):
    values = []
    for j in range(len(numerators)):
        numerator, denominator = numerators[j], denominators[j]
        if denominator == 0:
            values.append('--')
        else:
            quotient = numerator * 1.0 / denominator
            values.append(valueFn(quotient))
    if includeError:
        for j in range(len(numerators)):
            numerator, denominator = numerators[j], denominators[j]
            error = (0 if denominator == 0 else standardError(numerator, denominator))
            values.append(valueFn(error))   
    return values

def getStats(functions, valueFn = lambda x: '{:.4f}'.format(x), includeError = False, denominatorIsFilter = True, evaluationFn = perPlayerEvaluation):
    for season in ALL_SEASONS:
        numerators, denominators = evaluationFn(season, functions, denominatorIsFilter)
        values = quotientValues(numerators, denominators, valueFn, includeError)
        print('{},{}'.format(season, ','.join(values)))
    print('')

def reduceToStats(mappingFn, filterFn, reductionFns, valueFn = lambda x: '{:.4f}'.format(x)):
    for season in ALL_SEASONS:
        builds, players, chats, queues, actions = getDataFor(season)
        data = []
        for i in range(len(builds)):
            entry = {'build': builds[i], 'player': players[i], 'chat': chats[i // 2],
                     'queue': queues[i], 'action': actions[i], 'season': season, 'i': i}
            if filterFn(entry):
                data.append(mappingFn(entry))
        values = []
        for reductionFn in reductionFns:
            seasonValue = reductionFn(data)
            values.append(valueFn(seasonValue))
        print('{},{}'.format(season, ','.join(values)))
    print('')

def allTimeStats(functions, valueFn = lambda x: '{:.4f}'.format(x), includeError = False, denominatorIsFilter = True):
    numerators = [0] * len(functions)
    denominators = [0] * len(functions)
    for season in ALL_SEASONS:
        builds, players, chats, queues, actions = getDataFor(season)
        for i in range(len(builds)):
            entry = {'build': builds[i], 'player': players[i], 'chat': chats[i // 2],
                     'queue': queues[i], 'action': actions[i], 'season': season, 'i': i}
            for j, (numeratorFn, denominatorFn) in enumerate(functions):
                denominator = denominatorFn(entry)
                if denominator > 0 or not denominatorIsFilter:
                    numerators[j] += numeratorFn(entry)
                    denominators[j] += denominator
    values = quotientValues(numerators, denominators, valueFn, includeError)
    print(','.join(values))
    print('')

def throughQueueStats(functions, bucketLimits, valueFn = lambda x: '{:.4f}'.format(x), includeError = False, denominatorIsFilter = True):
    for lower, upper in zip(bucketLimits[:-1], bucketLimits[1:]):
        numerators = Counter()
        denominators = Counter()
        for season in ALL_SEASONS:
            builds, players, chats, queues, actions = getDataFor(season)
            for i in range(len(builds)):
                # Filter the queues to just the desired range.
                entry = {'build': builds[i], 'player': players[i], 'chat': chats[i // 2],
                         'queue': [queue[lower:upper] for queue in queues[i]], 'action': actions[i], 'season': season, 'i': i}
                for j, (numeratorFn, denominatorFn) in enumerate(functions):
                    denominator = denominatorFn(entry)
                    if denominator > 0 or not denominatorIsFilter:
                        numerators[j] += numeratorFn(entry)
                        denominators[j] += denominator
        values = quotientValues(numerators, denominators, valueFn, includeError)
        print('{}-{},{}'.format(lower, upper, ','.join(values)))
    print('')

def negate(fn):
    return lambda entry: not fn(entry)

def allOf(*fns):
    """Return 1 if all of the given functions returns 1. All the given functions should return either 0 or 1."""
    return lambda entry: min(map(lambda fn: fn(entry), fns))    

def both(fnA, fnB):
    return allOf(fnA, fnB)

def anyOf(*fns):
    """Return 1 if any of the given functions returns 1. All the given functions should return either 0 or 1."""
    return lambda entry: max(map(lambda fn: fn(entry), fns))

def either(fnA, fnB):
    return anyOf(fnA, fnB)

def sumOf(fns):
    return lambda entry: sum(map(lambda fn: fn(entry), fns))

def atLeast(fn, amount):
    return lambda entry: fn(entry) >= amount

def matchSum(fn):
    return lambda entry: fn({'build': entry['builds'][0], 'player': entry['players'][0], 'chat': entry['chat'],
                             'queue': entry['queues'][0], 'action': entry['actions'][0], 'season': entry['season'], 'i': entry['i']}) \
                       + fn({'build': entry['builds'][1], 'player': entry['players'][1], 'chat': entry['chat'],
                             'queue': entry['queues'][1], 'action': entry['actions'][1], 'season': entry['season'], 'i': entry['i']})

def matchContains(fn):
    return lambda entry: max(fn({'build': entry['builds'][0], 'player': entry['players'][0], 'chat': entry['chat'],
                                 'queue': entry['queues'][0], 'action': entry['actions'][0], 'season': entry['season'], 'i': entry['i']}),
                             fn({'build': entry['builds'][1], 'player': entry['players'][1], 'chat': entry['chat'],
                                 'queue': entry['queues'][1], 'action': entry['actions'][1], 'season': entry['season'], 'i': entry['i']}))

def allGames():
    """Count each match twice - once for each player."""
    return lambda entry: 1

def allMatches():
    """Count just one player in each match."""
    return lambda entry: entry['i'] % 2

def inSeason(season):
    return lambda entry: 1 if entry['season'] == season else 0

def inSeasons(seasons):
    return lambda entry: 1 if entry['season'] in seasons else 0

def inDivision(division):
    return lambda entry: 1 if division in entry['player']['filename'] else 0

def isFaction(faction):
    return lambda entry: 1 if entry['player']['faction'] == faction else 0

def forPlayer(name):
    return lambda entry: 1 if entry['player']['profileName'] == name else 0

def isAllies():
    return lambda entry: 1 if getFactionType(entry['player']['faction']) == 'Allies' else 0

def isSoviets():
    return lambda entry: 1 if getFactionType(entry['player']['faction']) == 'Soviet' else 0

def countInQueue(q, item):
    return lambda entry: entry['queue'][q].count(item)

def allUnits(q):
    return lambda entry: len(entry['queue'][q])

def queueHas(q, item):
    return lambda entry: 1 if item in entry['queue'][q] else 0

def firstQueuedIndex(q, item):
    return lambda entry: entry['queue'][q].index(item) if item in entry['queue'][q] else 0

def built(item):
    return lambda entry: 1 if '[{}]'.format(item) in entry['build'] or '[{}]'.format(item) in entry['queue'][1] else 0

def countBuilt(item):
    return lambda entry: entry['queue'][0].count('[{}]'.format(item)) + entry['queue'][1].count('[{}]'.format(item))

def usedPower(power):
    return lambda entry: 1 if any(action for action, _, _ in entry['action'] if action == power) else 0

def countPower(power):
    return lambda entry: len([action for action, _, _ in entry['action'] if action == power])

def sentMessage(message):
    return lambda entry: 1 if any(chat for chat in entry['chat'] if re.sub(r'[^a-z]', '', chat['message'].lower()) == message and chat['clientIndex'] == entry['player']['clientIndex']) else 0

def withOutcome(outcome):
    return lambda entry: 1 if entry['player']['outcome'] == outcome else 0

def duration(unitDivisor=60):
    return lambda entry: (entry['player']['outcomeTime'] - entry['player']['startTime']) * 1.0 / unitDivisor

def hasDuration():
    return lambda entry: 1 if entry['player']['outcomeTime'] != None and entry['player']['outcomeTime'] > 0 else 0

def wonWhen(fn):
    return lambda entry: fn(entry) if entry['player']['outcome'] == 'Won' else 0

def resultWhen(fn):
    return lambda entry: fn(entry) if entry['player']['outcome'] in ['Won', 'Lost'] else 0

def winRate(fn):
    return wonWhen(fn), resultWhen(fn)

def averageCountWhenPresent(countFn):
    return countFn, lambda entry: 1 if countFn(entry) > 0 else 0

def bucketFns(mappingFn, bucketLimits):
    outputFns = []
    for lower, upper in zip(bucketLimits[:-1], bucketLimits[1:]):
        bucketFn = lambda entry, lower=lower, upper=upper: 1 if mappingFn(entry) >= lower and mappingFn(entry) < upper else 0
        outputFns.append(bucketFn)
    return outputFns

def bucketWithFilter(mappingFn, filterFn, bucketLimits):
    numeratorFns = bucketFns(mappingFn, bucketLimits)
    fnPairs = []
    for numeratorFn in numeratorFns:
        fnPairs.append((numeratorFn, filterFn))
    return fnPairs

def bucketedWinRate(mappingFn, bucketLimits):
    fns = bucketFns(mappingFn, bucketLimits)
    fnPairs = []
    for fn in fns:
        fnPairs.append(winRate(fn))
    return fnPairs

def colourToInt(rgb):
    r, g, b = rgb
    return 256 * (256 * int(r) + int(g)) + int(b)

def linearInt(x0, x, x1, y0, y1):
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

def toColour(value, limits={0: (0, 0, 0), 50: (0, 0, 255), 100: (230, 230, 255)}):
    domainLimits = sorted(limits.keys())
    below = [x for x in domainLimits if x <= value]
    above = [x for x in domainLimits if x > value]
    if len(below) == 0:
        return colourToInt(limits[domainLimits[0]])
    if len(above) == 0:
        return colourToInt(limits[domainLimits[-1]])
    lower = below[-1]
    upper = above[0]
    rgb = (linearInt(lower, value, upper, limits[lower][i], limits[upper][i]) for i in range(3))
    return colourToInt(rgb)

def rankMapsBy(numeratorFn, filterFn=allGames(), restrictToMap=True, suppressEmpty=False):
    for season in ALL_SEASONS:
        numerators = Counter()
        denominators = Counter()
        builds, players, chats, queues, actions = getDataFor(season)
        for i in range(len(builds) // 2):
            entry = {'builds': builds[2*i:2*i+2], 'players': players[2*i:2*i+2], 'chat': chats[i],
                     'queues': queues[2*i:2*i+2], 'actions': actions[2*i:2*i+2], 'season': season, 'i': i}
            mapTitle = str(season) + '; ' + entry['players'][0]['mapTitle'].encode('utf-8')
            if filterFn(entry) > 0:
                numerators[mapTitle] += numeratorFn(entry)
                denominators[mapTitle if restrictToMap else 'All'] += 1
        percentages = []
        for mapTitle in numerators.keys():
            if numerators[mapTitle] > 0 or not suppressEmpty:
                percentages.append((numerators[mapTitle] * 100.0 / denominators[mapTitle if restrictToMap else 'All'], mapTitle))
        for percent, mapTitle in reversed(sorted(percentages)):
            print('{}: {}/{} games ({:.2f}%)'.format(mapTitle, numerators[mapTitle], denominators[mapTitle if restrictToMap else 'All'], percent))
    print('')

print('Total games analysed: {}'.format(len(all_players)))

# 001
if False:
    # Win rates for Allies/Soviets.
    getStats([winRate(isAllies()),
              winRate(isSoviets())])
    # Win rates by faction.
    getStats([winRate(isFaction('England')),
              winRate(isFaction('France')),
              winRate(isFaction('Germany')),
              winRate(isFaction('Russia')),
              winRate(isFaction('Ukraine'))])
    # Game count.
    getCounts([allMatches()])

# 002
if False:
    # Usage of tech structures.
    getStats([(built('SD'), allGames()),
              (built('RD'), allGames()),
              (built('TC'), allGames())], PERCENT)
    # Win rates by tech structures.
    getStats([winRate(built('SD')),
              winRate(built('RD')),
              winRate(built('TC'))], PERCENT)

# 003
if False:
    # Usage of tech structures in Masters.
    getStats([(built('SD'), inDivision('MASTER')),
              (built('RD'), inDivision('MASTER')),
              (built('TC'), inDivision('MASTER'))], PERCENT)
    # Usage of tech structures by winners.
    getStats([(built('SD'), withOutcome('Won')),
              (built('RD'), withOutcome('Won')),
              (built('TC'), withOutcome('Won'))], PERCENT)

# 004
if False:
    # Kennel win rate.
    getStats([winRate(built('Ke'))], PERCENT, includeError=True)

# 005
if False:
    # Defences built per game.
    functions = []
    functions += [(countBuilt(defence), isAllies()) for defence in ['PB','CP','Tu','AA','GG','Cs']]
    functions += [(countBuilt(defence), isSoviets()) for defence in ['FT','Ts','Sa','IC']]
    functions += [(countBuilt(defence), allGames()) for defence in ['MS','--','==','Si']]
    getStats(functions)
    # Defence use rate.
    functions = []
    functions += [(built(defence), isAllies()) for defence in ['PB','CP','Tu']]
    functions += [(built(defence), isSoviets()) for defence in ['FT','Ts']]
    getStats(functions, PERCENT)

# 007
if False:
    # Average fakes built per game (and average total).
    functions = []
    countFns = []
    for char in 'RTMWPCASFX':
        fake = char + '?'
        functions.append((countBuilt(fake), isFaction('France')))
        countFns.append(countBuilt(fake))
    totalFn = sumOf(countFns)
    functions.append((totalFn, isFaction('France')))
    getStats(functions)
    # Fake count by bucket.
    getCounts(bucketFns(totalFn, [1, 2, 4, 8, float('inf')]))

# 008
if False:
    # Fake win rates.
    builtFakeFns = []
    for char in 'RTMWPCASFX':
        fake = char + '?'
        builtFakeFns.append(built(fake))
    getStats([winRate(isAllies()),
              winRate(isFaction('France')),
              winRate(anyOf(*builtFakeFns))], PERCENT, includeError=True)

# 009
if False:
    # Percentage of games with support power.
    getStats([(usedPower('SovietSpyPlane'), isSoviets()),
              (usedPower('SovietParatroopers'), isSoviets()),
              (usedPower('UkraineParabombs'), isFaction('Ukraine')),
              (usedPower('Chronoshift'), isAllies()),
              # Iron Curtain
              (either(usedPower('GrantExternalConditionPowerInfoOrder'), usedPower('GrantUpgradePowerInfoOrder')), isSoviets()),
              (usedPower('NukePowerInfoOrder'), allGames()),
              # Sonar Pulse
              (usedPower('SpawnActorPowerInfoOrder'), isAllies()),
              (built('RD'), isSoviets()),
              (built('RD'), isAllies()),
              (built('RD'), isFaction('Ukraine'))], PERCENT)
    # Uses of power per game.
    getStats([(countPower('SovietSpyPlane'), built('AF')),
              (countPower('SovietParatroopers'), built('AF')),
              (countPower('UkraineParabombs'), both(built('AF'), isFaction('Ukraine'))),
              (countPower('Chronoshift'), built('Cs')),
              # Iron Curtain
              (sumOf([countPower('GrantExternalConditionPowerInfoOrder'), countPower('GrantUpgradePowerInfoOrder')]), built('IC')),
              (countPower('NukePowerInfoOrder'), built('MS')),
              # Sonar Pulse (Luckily was never used, so don't need to define availability criteria).
              (countPower('SpawnActorPowerInfoOrder'), allGames())])
    # Win rate for super powers.
    getStats([winRate(usedPower('Chronoshift')),
              winRate(either(usedPower('GrantExternalConditionPowerInfoOrder'), usedPower('GrantUpgradePowerInfoOrder'))),
              winRate(usedPower('NukePowerInfoOrder')),
              winRate(built('TC')),
              winRate(both(built('TC'), isAllies())),
              winRate(both(built('TC'), isSoviets()))], PERCENT)

# 011
if False:
    # Infantry count.
    getStats([(countInQueue(2, 'm'), allGames()),
              (countInQueue(2, 'r'), allGames()),
              (countInQueue(2, 'e'), allGames()),
              (countInQueue(2, 'g'), isSoviets()),
              (countInQueue(2, 'f'), isSoviets()),
              (countInQueue(2, 'd'), isSoviets()),
              (countInQueue(2, 't'), isSoviets()),
              (countInQueue(2, 's'), isFaction('Russia')),
              (countInQueue(2, '+'), isAllies()),
              (countInQueue(2, '*'), isAllies()),
              (countInQueue(2, '?'), isAllies()),
              (countInQueue(2, '!'), isAllies())])

# 012
if False:
    # Rifle-Rocket Ratio.
    getStats([(countInQueue(2, 'm'), countInQueue(2, 'r'))], denominatorIsFilter=False)
    # Rifle-Rocket Ratio Frequency.
    rrRatioFn = lambda entry: countInQueue(2, 'm')(entry) * 1.0 / countInQueue(2, 'r')(entry) if countInQueue(2, 'r')(entry) > 0 else 1000000
    gameCountFns = bucketFns(rrRatioFn, [0, 1.5, 2.5, 3.5, 5.5, float('inf')])
    getCounts(gameCountFns, PERCENT, perEntry=True)
    # Rifle-Rocket Ratio Win Rate.
    winRateFns = map(winRate, gameCountFns)
    getStats(winRateFns, PERCENT)

# 013
if False:
    # Popularity of chat messages.
    getStats([(sentMessage('glhf'), allGames()),
              (sentMessage('gl'), allGames()),
              (sentMessage('hf'), allGames()),
              (sentMessage('hfgl'), allGames())], PERCENT)
    # Win rate for various chat messages.
    getStats([winRate(sentMessage('glhf')),
              winRate(sentMessage('gl')),
              winRate(sentMessage('hf')),
              winRate(sentMessage('hfgl'))], PERCENT)
    # Win rate for player saying "gg" first.
    def ggIndexesForClient(chats, clientIndex):
        """Return a list of the indexes of all messages by the client saying gg or ggwp."""
        return [j for j, chat in enumerate(chats) if chat['clientIndex'] == clientIndex and re.sub(r'[^a-z]', '', chat['message'].lower()) in ['gg', 'ggwp']]
    def playerWithFirstGG(entry):
        """Return the index of the player who said gg first (or None if neither player said gg)."""
        player0GGs = ggIndexesForClient(entry['chat'], entry['players'][0]['clientIndex'])
        player1GGs = ggIndexesForClient(entry['chat'], entry['players'][1]['clientIndex'])
        if not player0GGs and not player1GGs:
            return None
        elif not player0GGs:
            return 1
        elif not player1GGs:
            return 0
        return 0 if player0GGs[0] < player1GGs[0] else 1
    getStats([(lambda entry: 1 if any(entry['players'][i]['outcome'] == 'Won' for i in range(2) if playerWithFirstGG(entry) == i) else 0, allGames())], PERCENT, evaluationFn=perMatchEvaluation)

# 014
if False:
    # Average and maximum game length.
    reduceToStats(duration(), hasDuration(), [mean, max])
    # Bucketed game length.
    getStats(bucketWithFilter(duration(), hasDuration(), [0, 5, 10, 15, 20, 25, 30, 35, 40, float('inf')]), PERCENT)

# 015
if False:
    # Game length by division.
    getStats([(duration(), both(hasDuration(), inDivision('MASTER'))),
              (duration(), both(hasDuration(), inDivision('MINION'))),
              (duration(), both(hasDuration(), inDivision('RECRUIT')))])
    # Game length by faction.
    durationFn = lambda entry: (entry['players'][0]['outcomeTime'] - entry['players'][0]['startTime']) * 1.0 / 60
    hasDurationFn = lambda entry: 1 if entry['players'][0]['outcomeTime'] != None and entry['players'][0]['outcomeTime'] > 0 else 0
    hasOutcomeFn = lambda entry: 1 if entry['players'][0]['outcome'] in ['Won', 'Lost'] else 0
    winnerLoserFactionTypes = lambda entry: ([getFactionType(player['faction']) for player in entry['players'] if player['outcome'] == 'Won'] + [getFactionType(player['faction']) for player in entry['players'] if player['outcome'] == 'Lost'])
    getStats([(durationFn, allOf(hasDurationFn, hasOutcomeFn, lambda entry: 1 if winnerLoserFactionTypes(entry) == ['Allies', 'Allies'] else 0)),
              (durationFn, allOf(hasDurationFn, hasOutcomeFn, lambda entry: 1 if winnerLoserFactionTypes(entry) == ['Soviet', 'Soviet'] else 0)),
              (durationFn, allOf(hasDurationFn, hasOutcomeFn, lambda entry: 1 if winnerLoserFactionTypes(entry) == ['Allies', 'Soviet'] else 0)),
              (durationFn, allOf(hasDurationFn, hasOutcomeFn, lambda entry: 1 if winnerLoserFactionTypes(entry) == ['Soviet', 'Allies'] else 0)),], evaluationFn=perMatchEvaluation)

# 016
if False:
    # Spy usage by nation.
    functions = [(queueHas(2, '?'), isFaction('England')),
                 (queueHas(2, '?'), isFaction('France')),
                 (queueHas(2, '?'), isFaction('Germany'))]
    getStats(functions, PERCENT)
    # Overall spy usage.
    allTimeStats(functions, PERCENT)
    # Spies queued by nation.
    functions = [(countInQueue(2, '?'), both(isFaction('England'), queueHas(2, '?'))),
                 (countInQueue(2, '?'), both(isFaction('France'), queueHas(2, '?'))),
                 (countInQueue(2, '?'), both(isFaction('Germany'), queueHas(2, '?')))]
    getStats(functions)
    # Overall average spies by nation.
    allTimeStats(functions)

# 017
if False:
    # Unit proportion through queue.
    unitCountFns = []
    for unit in 'mregfdts+*?!':
        unitCountFns.append((countInQueue(2, unit), allUnits(2)))
    throughQueueStats(unitCountFns, [0, 50, 100, 150, 200, 250, 300, 350, 400], PERCENT)
    # Rifle-Rocket Ratio through queue.
    fns = [(lambda entry, season=season: countInQueue(2, 'm')(entry) * inSeason(season)(entry), countInQueue(2, 'r')) for season in ALL_SEASONS]
    throughQueueStats(fns, [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500])

# 019
if False:
    # Vehicles queued per game.
    getStats([(countInQueue(3, 'mt'), isAllies()),
              (countInQueue(3, 'ht'), isSoviets()),
              (countInQueue(3, 'ar'), isAllies()),
              (countInQueue(3, 'ft'), isSoviets()),
              (countInQueue(3, 'ra'), isAllies()),
              (countInQueue(3, 'lt'), isAllies()),
              (countInQueue(3, 'ap'), isSoviets()),
              (countInQueue(3, 'ha'), allGames()),
              (countInQueue(3, 'mc'), allGames()),
              (countInQueue(3, 'ml'), allGames()),
              (countInQueue(3, '$$'), allGames()),
              (countInQueue(3, 'mr'), isAllies()),
              # Technically these two aren't right since pt and mg swapped faction.
              (countInQueue(3, 'mg'), isFaction('England')),
              (countInQueue(3, 'pt'), isFaction('France')),
              (countInQueue(3, 'ct'), isFaction('Germany')),
              (countInQueue(3, 'v2'), isSoviets()),
              (countInQueue(3, 'mt'), isSoviets()),
              (countInQueue(3, '!t'), isSoviets()),
              (countInQueue(3, 'tt'), isFaction('Russia')),
              (countInQueue(3, 'dt'), isFaction('Ukraine'))])

# 020
if False:
    # MTs/HTs queued per game.
    getStats([(countInQueue(3, 'mt'), isAllies()),
              (countInQueue(3, 'ht'), isSoviets())])
    # MT/HT usage rate.
    getStats([(queueHas(3, 'mt'), isAllies()),
              (queueHas(3, 'ht'), isSoviets())], PERCENT)
    # Win rates for MT/HT.
    getStats([winRate(queueHas(3, 'mt')),
              winRate(queueHas(3, 'ht')),
              winRate(both(negate(queueHas(3, 'mt')), isAllies())),
              winRate(both(negate(queueHas(3, 'ht')), isSoviets()))], PERCENT, includeError=True)

# 021
if False:
    # Light vehicles queued.
    getStats([(countInQueue(3, 'lt'), isAllies()),
              (countInQueue(3, 'ra'), isAllies()),
              (countInQueue(3, 'ft'), isSoviets()),
              (countInQueue(3, 'ap'), isSoviets())])
    # Light vehicle usage rate.
    getStats([(queueHas(3, 'lt'), isAllies()),
              (queueHas(3, 'ra'), isAllies()),
              (queueHas(3, 'ft'), isSoviets()),
              (queueHas(3, 'ap'), isSoviets())], PERCENT)
    # Win rates for light vehicles.
    getStats([winRate(queueHas(3, 'lt')),
              winRate(queueHas(3, 'ra')),
              winRate(queueHas(3, 'ft')),
              winRate(queueHas(3, 'ap')),
              winRate(both(negate(queueHas(3, 'lt')), isAllies())),
              winRate(both(negate(queueHas(3, 'ra')), isAllies())),
              winRate(both(negate(queueHas(3, 'ft')), isSoviets())),
              winRate(both(negate(queueHas(3, 'ap')), isSoviets()))], PERCENT)

# 022
if False:
    # Light vehicle count in first five.
    getStats([(lambda entry: entry['queue'][3][:5].count('lt'), isAllies()),
              (lambda entry: entry['queue'][3][:5].count('ra'), isAllies()),
              (lambda entry: entry['queue'][3][:5].count('ft'), isSoviets()),
              (lambda entry: entry['queue'][3][:5].count('ap'), isSoviets())])
    # Light vehicle usage rate in first five.
    firstFiveHas = lambda item: lambda entry, item=item: 1 if item in entry['queue'][3][:5] else 0
    getStats([(firstFiveHas('lt'), isAllies()),
              (firstFiveHas('ra'), isAllies()),
              (firstFiveHas('ft'), isSoviets()),
              (firstFiveHas('ap'), isSoviets())], PERCENT)
    # Win rates for light vehicles.
    getStats([winRate(firstFiveHas('lt')),
              winRate(firstFiveHas('ra')),
              winRate(firstFiveHas('ft')),
              winRate(firstFiveHas('ap')),
              winRate(both(negate(firstFiveHas('lt')), isAllies())),
              winRate(both(negate(firstFiveHas('ra')), isAllies())),
              winRate(both(negate(firstFiveHas('ft')), isSoviets())),
              winRate(both(negate(firstFiveHas('ap')), isSoviets()))], PERCENT)

# 023
if False:
    # Harvesters/MCVs queued per game.
    getStats([(countInQueue(3, 'ha'), allGames()),
              (countInQueue(3, 'mc'), allGames())])
    # Harvesters/MCVs usage rate.
    getStats([(queueHas(3, 'ha'), allGames()),
              (queueHas(3, 'mc'), allGames())], PERCENT)
    # Win rates for Harvesters/MCVs.
    getStats([winRate(queueHas(3, 'ha')),
              winRate(queueHas(3, 'mc')),
              winRate(both(negate(queueHas(3, 'ha')), allGames())),
              winRate(both(negate(queueHas(3, 'mc')), allGames()))], PERCENT)

# 024
if False:
    # Win rate by harvester count.
    getStats(bucketedWinRate(countInQueue(3, 'ha'), [0, 1, 2, 3, 4, 5, float('inf')]), PERCENT)
    # Win rate by MCV count.
    getStats(bucketedWinRate(countInQueue(3, 'mc'), [0, 1, 2, 3, float('inf')]), PERCENT)

# 025
if False:
    # Win rate by harvester and ref count.
    allHarvesterCount = lambda entry: countInQueue(3, 'ha')(entry) + countInQueue(0, 'Rf')(entry)
    getStats(bucketedWinRate(allHarvesterCount, [0, 6, 7, 8, 9, 10, 12, float('inf')]), PERCENT)
    # Win rate and popularity of total harvester count by game length.
    for harvesterCount in range(20 + 1):
        harvesterCountFn = lambda entry, harvesterCount=harvesterCount: allHarvesterCount(entry) == harvesterCount
        for minutes in range(30 + 1):
            durationFn = lambda entry, minutes=minutes: 1 if hasDuration()(entry) and int(round(duration()(entry))) == minutes else 0
            functions = [winRate(both(harvesterCountFn, durationFn))]
            numerators = Counter()
            denominators = Counter()
            for season in ALL_SEASONS:
                deltaN, deltaD = perPlayerEvaluation(season, functions, True)
                numerators += deltaN
                denominators += deltaD
            if len(numerators) > 0:
                values = quotientValues(numerators, denominators, lambda x: toColour(x * 100, {25:(230,230,255), 50:(0,0,255), 75:(0,0,0)}), includeError=False)
                print('{},{},{},{}'.format(harvesterCount, minutes, denominators[0], values[0]))

# 026
if False:
    # Arti/V2 count.
    getStats([(countInQueue(3, 'ar'), isAllies()),
              (countInQueue(3, 'v2'), isSoviets())])    
    # Arti and V2 usages (and corresponding Radar Dome usage).
    getStats([(queueHas(3, 'ar'), isAllies()),
              (queueHas(3, 'v2'), isSoviets()),
              (built('RD'), isAllies()),
              (built('RD'), isSoviets())], PERCENT)
    # Arti/V2 win rates.
    getStats([winRate(queueHas(3, 'ar')),
              winRate(queueHas(3, 'v2')),
              winRate(both(negate(queueHas(3, 'ar')), isAllies())),
              winRate(both(negate(queueHas(3, 'v2')), isSoviets()))], PERCENT, includeError=True)

# 027
if False:
    # Compare Radar Dome usage against artis/V2s.
    getStats([winRate(queueHas(3, 'ar')),
              winRate(queueHas(3, 'v2')),
              winRate(both(negate(queueHas(3, 'ar')), isAllies())),
              winRate(both(negate(queueHas(3, 'v2')), isSoviets())),
              winRate(both(negate(queueHas(3, 'ar')), both(isAllies(), built('RD')))),
              winRate(both(negate(queueHas(3, 'v2')), both(isSoviets(), built('RD'))))], PERCENT, includeError=True)
    # Unit proportion through queue.
    unitCountFns = [(countInQueue(3, 'ar'), allUnits(3)),
                    (countInQueue(3, 'v2'), allUnits(3))]
    throughQueueStats(unitCountFns, [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60], PERCENT)

# 028
if False:
    # Mammoth, MAD tank and minelayer count.
    getStats([(countInQueue(3, 'ma'), isSoviets()),
              (countInQueue(3, '!t'), isSoviets()),
              (countInQueue(3, 'ml'), allGames()),
              (countInQueue(3, 'rj'), isAllies())])
    # Find all games with MAD Tanks.
    findGames(queueHas(3, '!t'), [lambda entry: entry['player']['profileName'], countInQueue(3, '!t')])
    # Output some extra information about Booby vs Ohmk Torque.
    findGames(both(queueHas(3, '!t'), inDivision('RECRUIT')), [lambda entry: entry['player']['profileName'], countInQueue(3, '!t'), countInQueue(2, 't'), countInQueue(4, 'mi')])
    # Mammoth, MAD tank and minelayer usages (and corresponding Radar Dome usage).
    getStats([(queueHas(3, 'ma'), isSoviets()),
              (queueHas(3, '!t'), isSoviets()),
              (queueHas(3, 'ml'), allGames()),
              (queueHas(3, 'rj'), isAllies())], PERCENT)
    # Mammoth, MAD tank and minelayer win rates.
    getStats([winRate(isSoviets())], PERCENT)
    getStats([winRate(queueHas(3, 'ma')),
              winRate(queueHas(3, '!t')),
              winRate(queueHas(3, 'ml')),
              winRate(queueHas(3, 'rj')),
              winRate(both(negate(queueHas(3, 'ma')), isSoviets())),
              winRate(both(negate(queueHas(3, '!t')), isSoviets())),
              winRate(both(negate(queueHas(3, 'ml')), allGames())),
              winRate(both(negate(queueHas(3, 'rj')), isAllies()))], PERCENT)

# 029
if False:
    # Average number of Mammoths queued when Soviet, when used and when built TC.
    getStats([(countInQueue(3, 'ma'), isSoviets()),
              (countInQueue(3, 'ma'), both(isSoviets(), built('TC'))),
              (countInQueue(3, 'ma'), queueHas(3, 'ma'))])
    # Win rates for Soviets, Soviet TC and Mammoth.
    getStats([winRate(isSoviets()),
              winRate(both(isSoviets(), built('TC'))),
              winRate(queueHas(3, 'ma'))], PERCENT, includeError=True)
    # Find out how many games had Mammoths.
    getCounts([queueHas(3, 'ma')])
    # Unit proportion through queue.
    unitCountFns = [(countInQueue(3, 'ma'), allUnits(3)),
                    (countInQueue(3, 'v2'), allUnits(3)),
                    (countInQueue(3, 'ft'), allUnits(3)),
                    (countInQueue(3, 'ap'), allUnits(3)),
                    (countInQueue(3, 'ml'), allUnits(3))]
    throughQueueStats(unitCountFns, [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60], PERCENT)

# 030
if False:
    # Supply truck count.
    getStats([(countInQueue(3, '$$'), allGames())])    
    # Supply truck popularity.
    getStats([(queueHas(3, '$$'), allGames())], PERCENT)
    # Find out how many games had Supply Trucks.
    getCounts([queueHas(3, '$$')])
    # Find all games with Supply Trucks.
    findGames(queueHas(3, '$$'), [lambda entry: entry['player']['filename'], countInQueue(3, '$$')])
    # Supply truck win rate.
    getStats([winRate(queueHas(3, '$$')),
              winRate(both(negate(queueHas(3, '$$')), allGames()))], PERCENT, includeError=True)

# 031
if False:
    # Faction vehicles average count.
    # Nb. Phase Transport went from England to France in S06 (and MGG went the other way).
    getStats([(countInQueue(3, 'mg'), either(both(inSeasons(range(1, 5+1)), isFaction('France')), both(inSeasons(range(6, 9+1)), isFaction('England')))),
              (countInQueue(3, 'pt'), either(both(inSeasons(range(1, 5+1)), isFaction('England')), both(inSeasons(range(6, 9+1)), isFaction('France')))),
              (countInQueue(3, 'ct'), isFaction('Germany')),
              (countInQueue(3, 'tt'), isFaction('Russia')),
              (countInQueue(3, 'dt'), isFaction('Ukraine'))])
    # Counts of games with faction vehicles.
    getCounts([queueHas(3, 'mg'), queueHas(3, 'pt'), queueHas(3, 'ct'), queueHas(3, 'tt'), queueHas(3, 'dt')])
    # Faction vehicles usage rate.
    getStats([(queueHas(3, 'mg'), either(both(inSeasons(range(1, 5+1)), isFaction('France')), both(inSeasons(range(6, 9+1)), isFaction('England')))),
              (queueHas(3, 'pt'), either(both(inSeasons(range(1, 5+1)), isFaction('England')), both(inSeasons(range(6, 9+1)), isFaction('France')))),
              (queueHas(3, 'ct'), isFaction('Germany')),
              (queueHas(3, 'tt'), isFaction('Russia')),
              (queueHas(3, 'dt'), isFaction('Ukraine'))], PERCENT)
    # Win rates for faction vehicles.
    getStats([winRate(queueHas(3, 'mg')),
              winRate(queueHas(3, 'pt')),
              winRate(queueHas(3, 'ct')),
              winRate(queueHas(3, 'tt')),
              winRate(queueHas(3, 'dt'))], PERCENT)

# 032
if False:
    # Games containing MGGs.
    findGames(queueHas(3, 'mg'), [lambda entry: (entry['player']['profileName'] + ',' + entry['player']['mapTitle']).encode('utf-8'), countInQueue(3, 'mg')])

# 033
if False:
    # Air unit count.
    getStats([(countInQueue(4, 'bh'), isAllies()),
              (countInQueue(4, 'ch'), isAllies()),
              (countInQueue(4, 'lb'), isAllies()),
              (countInQueue(4, 'yk'), isSoviets()),
              (countInQueue(4, 'mi'), isSoviets())])
    # Air unit usage.
    getStats([(queueHas(4, 'bh'), isAllies()),
              (queueHas(4, 'ch'), isAllies()),
              (queueHas(4, 'lb'), isAllies()),
              (queueHas(4, 'yk'), isSoviets()),
              (queueHas(4, 'mi'), isSoviets())], PERCENT)
    # Air unit win rates.
    getStats([winRate(queueHas(4, 'bh')),
              winRate(queueHas(4, 'ch')),
              winRate(queueHas(4, 'lb')),
              winRate(queueHas(4, 'yk')),
              winRate(queueHas(4, 'mi'))], PERCENT)

# 034
if False:
    # Air unit count with all prerequisite buildings.
    getStats([(countInQueue(4, 'bh'), built('HP')),
              (countInQueue(4, 'ch'), built('HP')),
              (countInQueue(4, 'lb'), both(built('HP'), built('TC'))),
              (countInQueue(4, 'yk'), built('AF')),
              (countInQueue(4, 'mi'), both(built('AF'), built('TC')))])
    # Games containing Chinooks.
    getCounts([queueHas(4, 'ch')])
    # Win rates of tier three air units compared with Soviet/Allied Tech Centers.
    getStats([winRate(queueHas(4, 'lb')),
              winRate(queueHas(4, 'mi')),
              winRate(allOf(negate(queueHas(4, 'lb')), built('TC'), isAllies())),
              winRate(allOf(negate(queueHas(4, 'mi')), built('TC'), isSoviets())),
              winRate(both(built('TC'), isAllies())),
              winRate(both(built('TC'), isSoviets()))], PERCENT, includeError=True)

# 035
if False:
    # Games containing chinooks.
    findGames(queueHas(4, 'ch'), [lambda entry: (entry['player']['profileName'] + ',' + entry['player']['mapTitle']).encode('utf-8'), countInQueue(4, 'ch')])

# 036
if False:
    # Naval unit count.
    getStats([(countInQueue(5, 'sub'), isSoviets()),
              (countInQueue(5, 'msb'), isSoviets()),
              (countInQueue(5, 'gun'), isAllies()),
              (countInQueue(5, 'des'), isAllies()),
              (countInQueue(5, 'cru'), isAllies()),
              (countInQueue(5, 'tra'), allGames())])
    # Naval unit usage.
    getStats([(queueHas(5, 'sub'), isSoviets()),
              (queueHas(5, 'msb'), isSoviets()),
              (queueHas(5, 'gun'), isAllies()),
              (queueHas(5, 'des'), isAllies()),
              (queueHas(5, 'cru'), isAllies()),
              (queueHas(5, 'tra'), allGames())], PERCENT)
    # Number of games with each unit.
    getCounts([queueHas(5, 'sub'),
               queueHas(5, 'msb'),
               queueHas(5, 'gun'),
               queueHas(5, 'des'),
               queueHas(5, 'cru'),
               queueHas(5, 'tra')])
    # Naval unit win rates.
    getStats([winRate(queueHas(5, 'sub')),
              winRate(queueHas(5, 'msb')),
              winRate(queueHas(5, 'gun')),
              winRate(queueHas(5, 'des')),
              winRate(queueHas(5, 'cru')),
              winRate(queueHas(5, 'tra'))], PERCENT)
    # Matches containing Naval Yards or Sub Pens.
    rankMapsBy(matchContains(either(built('SP'), built('NY'))), suppressEmpty=True)

# 037
if False:
    # Games containing naval.
    findGames(either(built('SP'), built('NY')), [lambda entry: (entry['player']['profileName'] + ',' + entry['player']['mapTitle']).encode('utf-8')])

# 038
if False:
    # Demo trucks
    findGames(atLeast(countInQueue(3, 'dt'), 5), [lambda entry: (entry['player']['profileName'] + ',' + entry['player']['mapTitle']).encode('utf-8'), countInQueue(3, 'dt')])

# 040
if False:
    # First time Tech building built by season.
    getStats([(firstQueuedIndex(0, 'SD'), queueHas(0, 'SD')),
              (firstQueuedIndex(0, 'RD'), queueHas(0, 'RD')),
              (firstQueuedIndex(0, 'TC'), queueHas(0, 'TC'))])
    # Win rate of tech buildings by season.
    for building in ['SD', 'RD', 'TC']:
        #getStats(bucketedWinRate(firstQueuedIndex(0, building), [0, 10, 20, 30, 40, 50, float('inf')]), PERCENT)
        fn = firstQueuedIndex(0, building)
        getStats(bucketWithFilter(wonWhen(fn), resultWhen(fn), [0, 10, 20, 30, 40, 50, float('inf')]), PERCENT)

# 041
if True:
    rankMapsBy(allGames(), restrictToMap=False)
    #rankMapsBy(matchContains(built('TC')), allGames())
    #rankMapsBy(matchContains(wonWhen(isAllies())), matchContains(resultWhen(isAllies())))
    #rankMapsBy(matchContains(wonWhen(isSoviets())), matchContains(resultWhen(isSoviets())))

if False:
    #findGames(atLeast(countPower('NukePowerInfoOrder'), 5), [lambda entry: (entry['player']['profileName'] + ',' + entry['player']['mapTitle']).encode('utf-8'), countPower('NukePowerInfoOrder')])
    # Faction pick
    getStats([(isAllies(), allGames()), (isSoviets(), allGames())], PERCENT)
    findGames(both(queueHas(3, 'ma'), inDivision('PLAY')), [lambda entry: (entry['player']['profileName'] + ',' + entry['player']['mapTitle']).encode('utf-8')])

if False:
    #findGames(allOf(atLeast(countPower('NukePowerInfoOrder'), 4)), [lambda entry: (entry['player']['profileName'] + ',' + entry['player']['mapTitle']).encode('utf-8') + ',{}'.format(countPower('NukePowerInfoOrder')(entry))])
    findMatches(atLeast(matchSum(countPower('NukePowerInfoOrder')), 4), [lambda entry: (entry['players'][0]['mapTitle']).encode('utf-8') + ',{}'.format(matchSum(countPower('NukePowerInfoOrder'))(entry))])
    #findGames(both(hasDuration(), atLeast(duration(), 80)), [lambda entry: (entry['player']['mapTitle']).encode('utf-8') + ',{}'.format(duration()(entry))])
    findGames(atLeast(countBuilt('TC'), 4), [lambda entry: (entry['player']['mapTitle']).encode('utf-8') + ',{}'.format(countBuilt('TC')(entry))])
    findMatches(atLeast(matchSum(countBuilt('TC')), 7), [lambda entry: (entry['players'][0]['mapTitle']).encode('utf-8') + ',{}'.format(matchSum(countBuilt('TC'))(entry))])
    findGames(atLeast(countBuilt('CP'), 40), [lambda entry: (entry['player']['mapTitle']).encode('utf-8') + ',{}'.format(countBuilt('CP')(entry))])
    findGames(atLeast(countBuilt('MS'), 3), [lambda entry: (entry['player']['mapTitle']).encode('utf-8') + ',{}'.format(countBuilt('MS')(entry))])
    findMatches(atLeast(matchSum(countBuilt('MS')), 5), [lambda entry: (entry['players'][0]['mapTitle']).encode('utf-8') + ',{}'.format(matchSum(countBuilt('MS'))(entry))])
    findMatches(atLeast(matchSum(countPower('UkraineParabombs')), 6), [lambda entry: (entry['players'][0]['mapTitle']).encode('utf-8') + ',{}'.format(matchSum(countPower('UkraineParabombs'))(entry))])

if False:
    #findGames(both(queueHas(4, 'ch'), inSeason(4)), [lambda entry: entry['player']['mapTitle'] + ',{}'.format(countInQueue(4, 'ch')(entry))])
    #getStats([(queueHas(2, '*'), isAllies()), (queueHas(2, 't'), isSoviets())], PERCENT)
    findGames(allOf(queueHas(2, '*'), inDivision('MASTER'), inSeason(10)), [lambda entry: entry['player']['name'] + ',' + entry['player']['mapTitle'] + ',{}'.format(countInQueue(2, '*')(entry))])


# RAGL Stats
if False:
    _, players, _, _, _ = getDataFor(9)
    # Win rates for Allies/Soviets.
    for name in set([player['profileName'] for player in players]):
        print(name)
        allTimeStats([winRate(both(isAllies(), forPlayer(name))),
                      winRate(both(isSoviets(), forPlayer(name)))], PERCENT)
