#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: Determine which player the DeployTransform command belongs to, and whether it's a deploy or an undeploy.
# TODO: Avoid builds like "[PP][PP]..." where the player has tried to place a building in an invalid location.

from collections import defaultdict, Counter
import os, sys
import requests

# Which RAGL season to analyse replays for.
SEASON = 9
# The prefix that the RAGL files all begin with. This can be edited to further restrict input files to MASTERS or MINIONS.
PREFIX = 'RAGL-S{:02d}-'.format(SEASON)
# We only want to output "popular" builds. Ignore builds that happened less than this often:
POPULAR = 20
POPULAR_FOR_MAP = 10
POPULAR_FOR_PLAYER = 3
POPULARITY_FOR_BUILD_STATE = 100
# If true then print '..' to show that a build order is the same as the previous one.
ABRIDGE_OUTPUT = True
# This can be used to find builds that contain an unusual item. E.g Set it to 'Si' to output replays featuring a (queued) silo.
ITEM_TO_FIND = None

# The location of the OpenRA support directory.
# The support directory is where the game keeps the saved settings, maps, replays, logs and mod assets.  The default location is as follows, but one can choose to move it to an arbitrary location by passing an Engine.SupportDir argument to the Game.exe
#     Windows:      \Users\<Username>\AppData\Roaming\OpenRA\
#     macOS:        /Users/<username>/Library/Application Support/OpenRA/
#     GNU/Linux:    ~/.config/openra
# Older releases (before playtest-20190825) used different locations, which newer versions may continue to use in some circumstances:
#     Windows:      \Users\<Username>\My Documents\OpenRA\
#     GNU/Linux:    /home/<username>/.openra/
OPENRA_SUPPORT_DIRECTORY = '{}/.openra'.format(os.path.expanduser('~'))

# Load the replays from the corresponding location for the RAGL season.
if SEASON == 4:
    path = '{}/Replays/ra/release-20170527/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON == 5:
    path = '{}/Replays/ra/release-20180307/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON == 6:
    path = '{}/Replays/ra/release-20180923/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON == 7:
    path = '{}/Replays/ra/release-20190314/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON == 8:
    path = '{}/Replays/ra/release-20190314/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON == 9:
    path = '{}/Replays/ra/release-20200503/'.format(OPENRA_SUPPORT_DIRECTORY)
else:
    print('Unknown season', SEASON)
    raise Exception

# A local file to store the responses from the OpenRA forum fingerprint endpoint.
FINGERPRINT_CACHE_FILE = 'fingerprint.cache'

# Find all filenames for replays matching the restrictions.
filenames = []
for root, dirs, files in os.walk(path):
    for filename in files:
        if filename.startswith(PREFIX):
            filenames.append(filename)

# Mapping from official (variable length) title, to unified output format.
# A couple of examples:
# * The two airfields 'afld' and 'afld.ukraine' are both mapped to 'AF'.
# * Infantry 'e1' to 'e7' are mapped to more representative characters.
itemMap = [{
           b'powr': 'PP', # Powerplant
           b'tent': 'Rx', # Barracks (Allies)
           b'barr': 'Rx', # Barracks (Soviet)
           b'proc': 'Rf', # Refinery
           b'weap': 'WF', # War Factory
           b'fix': 'SD', # Service Depot
           b'dome': 'RD', # Radar Dome
           b'hpad': 'HP', # Helipad
           b'afld': 'AF', # Airfield
           b'afld.ukraine': 'AF', # Airfield (Ukraine)
           b'apwr': 'AP', # Advanced Power Plant
           b'kenn': 'Ke', # Kennel
           b'stek': 'TC', # Tech Centre (Soviet)
           b'atek': 'TC', # Tech Centre (Allies)
           b'spen': 'SP', # Sub Pen
           b'syrd': 'NY' # Naval Yard
           },{
           b'pbox': 'PB', # Pillbox
           b'hbox': 'CP', # Camo Pillbox
           b'gun': 'Tu', # Turret
           b'ftur': 'FT', # Flame Tower
           b'tsla': 'Ts', # Teslacoil
           b'agun': 'AA', # AA Gun
           b'sam': 'Sa', # SAM Site
           b'gap': 'GG', # Gap Generator
           b'pdox': 'Cs', # Chronosphere
           b'iron': 'IC', # Iron Curtain
           b'mslo': 'MS', # Missile Silo
           b'fenc': '--', # Barbed Wire Fence
           b'sbag': '--', # Sandbag
           b'brik': '==', # Concrete Wall
           b'silo': 'Si', # Silo
           # Fakes
           b'facf': 'C?', # Fake Conyard
           b'mslf': 'M?', # Fake Missile Silo
           b'fpwr': 'P?', # Fake Power Plant
           b'domf': 'R?', # Fake Radar Dome
           b'fixf': 'F?', # Fake Service Depot
           b'syrf': 'Y?', # Fake Naval Yard
           b'weaf': 'W?', # Fake War Factory
           b'tenf': 'X?', # Fake Barracks
           b'pdof': 'S?', # Fake Chronosphere
           b'atef': 'T?', # Fake Allied Tech Center
           b'fapw': 'A?', # Fake Advance Power
           },{
           b'e1': 'm', # Rifle ("Minigunner")
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
           b'ss': 'sub', # Submarine
           b'msub': 'msb', # Missile Sub
           b'dd': 'des', # Destroyer
           b'ca': 'cru', # Cruiser
           b'lst': 'tra', # Naval Transport
           b'pt': 'gun' # Gunboat
           }]

### Load the replay files. ###

def bytesToInt(b):
    """Convert a binary string value to an integer."""
    return int('0x' + b.encode('hex'), 16)

def loadCachedFingerprints():
    """Load any fingerprint information stored by previous runs."""
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
    """Try to pick out player abbreviations from the replay file name (e.g. 'RAGL-S09-MASTER-GROUP-MRC-PUN-G1.orarep' -> ['MRC', 'PUN'])"""
    potentialAbbreviations = []
    for bit in filename.split('-')[2:]:
        if len(bit) == 3:
            potentialAbbreviations.append(bit)
    return potentialAbbreviations

# Initialise some empty collections for the various reports.
buildsByMap = defaultdict(list)
builds = []
queues = []
unitList = defaultdict(list)
players = []
fingerPrintToProfile = loadCachedFingerprints()
# Process each replay in turn.
for filename in filenames:
    # Store the binary data in a variable called x.
    f = open(path + filename, 'rb')
    x = f.read()
    f.close()
    
    # Try to find the map name.
    try:
        mapTitleField = b'MapTitle: '
        mapTitleIndex = x.index(mapTitleField) + len(mapTitleField)
        mapTitle = x[mapTitleIndex:mapTitleIndex + x[mapTitleIndex:].index(b'\n')]
    except:
        print('No map title found in {} - replay corrupted?'.format(filename))
        continue

    def getPlayer(x, pos):
        """Get the id of the player that gave the command."""
        if SEASON >= 9:
            return x[pos+1]
        return x[pos]
    
    def outputEvent(item):
        """Look up an item in the itemMap.
        
        Output the unified item code along with the index of the queue it came from.
        For example if the input is 'powr' then the output is 0, 'PP'."""
        for q, queue in enumerate(itemMap):
            if item in queue.keys():
                return q, queue[item]
        print('UNKNOWN:', item.decode('utf-8'), 'in', filename)
        raise Exception
    
    def getStartProductionEvents(x, pos):
        """Get information about a StartProduction event. Return the player id, the queue index and the item(s)."""
        l = bytesToInt(x[pos + 5])
        player = getPlayer(x, pos)
        item = x[pos + 6: pos + 6 + l]
        count = bytesToInt(x[pos + 6 + l])
        q, item = outputEvent(item)
        return player, q, [item] * count
    
    def getPlaceBuildingEvents(x, pos):
        """Get information about a PlaceBuilding event. Return the player id, the queue index and the item."""
        player = getPlayer(x, pos)
        # Different OpenRA releases have slightly different offsets.
        offset = (17 if SEASON <= 4 else (19 if SEASON <= 6 else 11))
        l = bytesToInt(x[pos + offset])
        item = x[pos + offset + 1: pos + offset + 1 + l]
        q, item = outputEvent(item)
        return player, q, ['[' + item + ']']
    
    def getCancelProductionEvent(x, pos):
        """Get information about a CancelProduction event. Return the player id, the queue index and the item(s)."""
        l = bytesToInt(x[pos + 5])
        player = getPlayer(x, pos)
        item = x[pos + 6: pos + 6 + l]
        count = bytesToInt(x[pos + 6 + l])
        q, item = outputEvent(item)
        return player, q, [item] * count

    def getPos(x, term, start):
        """Search for a binary string and return the position just after it.
        
        x: The binary content to search through.
        term: The binary string to search for.
        start: The position to start the search from.
        Returns: The position just after the search term finishes, or the length of the content if the term is not found."""
        try:
            return x[start:].index(term) + len(term) + start
        except ValueError:
            # No more terms found.
            return len(x)

    def getField(x, field, start):
        """Search for the value of a field (e.g. 'Color: F5F872').
        
        x: The binary content to search through.
        field: The field name to search for (e.g. 'Color').
        start: The position to start the search from.
        Returns: The corresponding value (e.g. 'F5F872')."""
        fieldStart = getPos(x, field + b': ', start)
        fieldEnd = getPos(x, b'\n', fieldStart)
        return x[fieldStart:fieldEnd-1]

    # Build information comes after the "StartGame" command.
    startGame = x.index(b'StartGame')
    
    # Try to get player information.
    for playerId in [0, 1]:
        pos = -1
        while True:
            pos = getPos(x, b'Player@{}:'.format(playerId), pos + 1)
            if pos >= len(x):
                break
            playerPos = pos
        fingerprint = getField(x, b'Fingerprint', playerPos)
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
                
        name = getField(x, b'Name', playerPos)
        outcome = getField(x, b'Outcome', playerPos)
        clientIndex = getField(x, b'ClientIndex', playerPos)
        faction = getField(x, b'FactionName', playerPos)
        pos = -1
        while True:
            pos = getPos(x, b'Client@{}:'.format(clientIndex), pos + 1)
            if pos >= len(x):
                break
            clientPos = pos
        factionPick = getField(x, b'Faction', clientPos)
        
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

        if len(events) != 2:
            # Probably one of the players gave no orders.
            print('Found game with {} player(s): {}'.format(len(events), filename))
            players = players[:-2]
            raise Exception
            
        for player, eventList in events.items():
            for q, queue in eventList.items():
                # Can be used to find which game contains an unusual item.
                if ITEM_TO_FIND in queue:
                    print(ITEM_TO_FIND, ' found in ', filename, mapTitle, 'Count:', queue.count(ITEM_TO_FIND))
                #print(player, q, ','.join(queue))
                unitList[q] += queue
            #if ''.join(build[player]).startswith('[PP][PP][PP]'):
            #    print(filename, mapTitle)
            builds.append(build[player])
            buildsByMap[mapTitle].append(build[player])
            queues.append(eventList)
    except ZeroDivisionError:
        # Used for debugging.
        sys.tracebacklimit = 0
        raise Exception
    except:
        print('Skipping ' + filename)

### Build the reports. ###

# A report of the faction popularity and win/loss ratio.
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

# A report of the buildings and units that were queued, and how effective they were.
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

def findPopularBuilds(builds, popularLimit=POPULAR):
    """Print a report of all popular build orders.
    
    builds: The complete set of build orders (every item built).
    popularLimit: How many occurrences are needed to class it as "popular"."""
    buildTree = defaultdict(lambda : defaultdict(list))
    buildTree[0][''] = builds
    out = []
    for depth in range(100):
        for priorBuilt, oldBuilds in buildTree[depth].items():
            newBuildIsPopular = False
            for build in oldBuilds:
                shallowBuild = ''.join(build[:depth + 1])
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

def makeFactionString(playerPicks):
    """Create a string showing how often various factions were picked.
    
    'E', 'F', 'G', 'R' and 'U' are used for the five factions, 'A' and 'S' for random Allies/Soviets
    and '?' is used to indicate faction was picked completely at random.
    For example 'U:73%,A:17%,?:10%' indicates that random Ukraine was picked 73% of the time, Random
    Allies 17% and Random 10%."""
    factionStrings = []
    for faction, count in playerPicks.most_common():
        letter = faction[0].upper()
        if faction == 'RandomAllies':
            letter = 'A'
        elif faction == 'RandomSoviet':
            letter = 'S'
        elif faction == 'Random':
            letter = '?'
        rate = '{:0.0f}%'.format(count * 100.0 / sum(playerPicks.values()))
        factionStrings.append('{}:{}'.format(letter, rate))
    return ','.join(factionStrings)

# A report for each player of their most common build orders.
for profileName in set(map(lambda player: player['profileName'], players)):
    playerBuilds = []
    wins = 0
    losses = 0
    playerPicks = Counter()
    for i, player in enumerate(players):
        if player['profileName'] == profileName:
            playerBuilds.append(builds[i])
            if player['outcome'] == 'Won':
                wins += 1
            elif player['outcome'] == 'Lost':
                losses += 1
            playerPicks[player['factionPick']] += 1
    winRate = '{:0.0f}%'.format(wins * 100.0 / (wins + losses))
    factionStr = makeFactionString(playerPicks)
    print('=== {} (Played {} game(s), Win Rate {}, Factions {}) ==='.format(profileName, len(playerBuilds), winRate, factionStr))
    findPopularBuilds(playerBuilds, POPULAR_FOR_PLAYER)

# A report for each map of the most popular build orders.
mapPickCounter = Counter()
for mapTitle in buildsByMap.keys():
    mapPickCounter[mapTitle] += len(buildsByMap[mapTitle])
for mapTitle, count in mapPickCounter.most_common():
    print('### {} (Picked {} time(s)) ###'.format(mapTitle, count / 2))
    findPopularBuilds(buildsByMap[mapTitle], POPULAR_FOR_MAP)

# A report of the overall most popular build orders.
print('--- Overall (Total {} game(s)) ---'.format(len(builds)))
findPopularBuilds(builds)

def expand(item):
    return '{1}{0}'.format(item[0], item[1])

# An experimental report of common it is to have build a particular set of buildings regardless of the order in which they were built.
print('---Overall Build States---')
positionCount = Counter()
for buildsForMap in buildsByMap.values():
    for build in buildsForMap:
        partialBuild = Counter()
        for building in build:
            partialBuild[building] += 1
            positionCount[''.join(map(str, sorted(map(expand, partialBuild.items()))))] += 1
for position, count in positionCount.most_common():
    if count >= POPULARITY_FOR_BUILD_STATE:
        print(count, position)
        pass
