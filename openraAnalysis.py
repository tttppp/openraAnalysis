#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: Determine which player the DeployTransform command belongs to, and whether it's a deploy or an undeploy.

from collections import defaultdict, Counter
import os, sys
import requests
import json
import datetime

# Which RAGL season to analyse replays for.
SEASON = int(sys.argv[1])#9
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
# This can be used to only look at particular matchups (e.g. Set it to set(['Random']) to look at Random v Random)
FACTION_PICK_FILTER = None
# Whether to create files containing the parsed replay data.
DUMP_DATA = True

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
if SEASON == 1:
    path = '{}/Replays/ra/release-20151224/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON in [2, 3]:
    path = '{}/Replays/ra/release-20161019/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON == 4:
    path = '{}/Replays/ra/release-20170527/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON == 5:
    path = '{}/Replays/ra/release-20180307/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON == 6:
    path = '{}/Replays/ra/release-20180923/'.format(OPENRA_SUPPORT_DIRECTORY)
elif SEASON in [7, 8]:
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
           b'powr': ('PP', 'Power Plant'),
           b'tent': ('Rx', 'Barracks'), # Allies
           b'barr': ('Rx', 'Barracks'), # Soviet
           b'proc': ('Rf', 'Refinery'),
           b'weap': ('WF', 'War Factory'),
           b'fix': ('SD', 'Service Depot'),
           b'dome': ('RD', 'Radar Dome'),
           b'hpad': ('HP', 'Helipad'),
           b'afld': ('AF', 'Airfield'),
           b'afld.ukraine': ('AF', 'Airfield'),
           b'apwr': ('AP', 'Advanced Power Plant'),
           b'kenn': ('Ke', 'Kennel'),
           b'stek': ('TC', 'Tech Centre'), # Soviet
           b'atek': ('TC', 'Tech Centre'), # Allies
           b'spen': ('SP', 'Sub Pen'),
           b'syrd': ('NY', 'Naval Yard')
           },{
           b'pbox': ('PB', 'Pillbox'),
           b'hbox': ('CP', 'Camo Pillbox'),
           b'gun': ('Tu', 'Turret'),
           b'ftur': ('FT', 'Flame Tower'),
           b'tsla': ('Ts', 'Teslacoil'),
           b'agun': ('AA', 'AA Gun'),
           b'sam': ('Sa', 'SAM Site'),
           b'gap': ('GG', 'Gap Generator'),
           b'pdox': ('Cs', 'Chronosphere'),
           b'iron': ('IC', 'Iron Curtain'),
           b'mslo': ('MS', 'Missile Silo'),
           b'fenc': ('--', 'Fence'), # Barbed Wire Fence
           b'sbag': ('--', 'Fence'), # Sandbag
           b'brik': ('==', 'Concrete Wall'),
           b'silo': ('Si', 'Silo'),
           # Fakes
           b'facf': ('C?', 'Fake Conyard'),
           b'mslf': ('M?', 'Fake Missile Silo'),
           b'fpwr': ('P?', 'Fake Power Plant'),
           b'domf': ('R?', 'Fake Radar Dome'),
           b'fixf': ('F?', 'Fake Service Depot'),
           b'syrf': ('Y?', 'Fake Naval Yard'),
           b'weaf': ('W?', 'Fake War Factory'),
           b'tenf': ('X?', 'Fake Barracks'),
           b'pdof': ('S?', 'Fake Chronosphere'),
           b'atef': ('T?', 'Fake Tech Center'),
           b'fapw': ('A?', 'Fake Advance Power')
           },{
           b'e1': ('m', 'Rifle'), # "Minigunner"
           b'e2': ('g', 'Gren'),
           b'e3': ('r', 'Rocket'),
           b'e4': ('f', 'Flamer'),
           b'e6': ('e', 'Engineer'),
           b'e7': ('!', 'Tanya'),
           b'medi': ('+', 'Medic'),
           b'mech': ('*', 'Mechanic'),
           b'dog': ('d', 'Dog'),
           b'shok': ('s', 'Shockie'),
           b'thf': ('t', 'Thief'),
           b'hijacker': ('t', 'Thief'),
           b'spy': ('?', 'Spy'),
           b'spy.england': ('?', 'Spy')
           },{
           b'1tnk': ('lt', 'Light Tank'),
           b'2tnk': ('mt', 'Medium Tank'),
           b'3tnk': ('ht', 'Heavy Tank'),
           b'4tnk': ('ma', 'Mammoth Tank'),
           b'ftrk': ('ft', 'Flak'),
           b'apc': ('ap', 'APC'),
           b'harv': ('ha', 'Harvester'),
           b'jeep': ('ra', 'Ranger'),
           b'arty': ('ar', 'Arti'),
           b'ttnk': ('tt', 'Tesla Tank'),
           b'v2rl': ('v2', 'V2'),
           b'mnly': ('ml', 'Minelayer'),
           b'mnly.ap': ('ml', 'Minelayer'), # Anti-personel
           b'mnly.at': ('ml', 'Minelayer'), # Anti-tank
           b'dtrk': ('dt', 'Demo'),
           b'mrj': ('rj', 'Radar Jammer'),
           b'mgg': ('mg', 'Mobile Gap Generator'),
           b'ctnk': ('ct', 'Chrono Tank'),
           b'stnk': ('pt', 'Phase Transport'),
           b'qtnk': ('!t', 'Mad Tank'),
           b'truk': ('$$', 'Supply Truck'),
           b'mcv': ('mc', 'MCV')
           },{
           b'hind': ('hi', 'Hind'),
           b'mh60': ('bh', 'Blackhawk'),
           b'heli': ('lb', 'Longbow'),
           b'tran': ('ch', 'Chinook'),
           b'yak': ('yk', 'Yak'),
           b'mig': ('mi', 'Mig')
           },{
           b'ss': ('sub', 'Submarine'),
           b'msub': ('msb', 'Missile Sub'),
           b'dd': ('des', 'Destroyer'),
           b'ca': ('cru', 'Cruiser'),
           b'lst': ('tra', 'Naval Transport'),
           b'pt': ('gun', 'Gunboat')
           }]
# Generate the mapping from unified code to human readable name.
itemNames = {}
for items in itemMap:
    for unifiedCode, name in items.values():
        if unifiedCode in itemNames and itemNames[unifiedCode] != name:
            raise Exception('Code {} maps to both {} and {}', unifiedCode, itemNames[unifiedCode], name)
        elif unifiedCode not in itemNames:
            itemNames[unifiedCode] = name

### Load the replay files. ###

def bytesToInt(b):
    """Convert a binary string value to an integer."""
    if isinstance(b, int):
        # Python 3 does this for a single byte automatically.
        return b
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
chats = []
actions = []
fingerPrintToProfile = loadCachedFingerprints()
# Process each replay in turn.
for filename in filenames:
    # Store the binary data in a variable called x.
    f = open(path + filename, 'rb')
    x = f.read()
    f.close()
    
    def getPlayer(x, pos):
        """Get the id of the player that gave the command."""
        if SEASON >= 9:
            return x[pos+1]
        return x[pos]
    
    def outputEvent(item):
        """Look up an item in the itemMap.
        
        Output the unified item code along with the index of the queue it came from.
        For example if the input is 'powr' then the output is 0, 'PP'."""
        for q, items in enumerate(itemMap):
            if item in items.keys():
                return q, items[item][0]
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

    def getPauseProductionEvent(x, pos):
        """Get information about a PauseProduction event. Return the player id, the queue index and the item(s)."""
        l = bytesToInt(x[pos + 5])
        player = getPlayer(x, pos)
        item = x[pos + 6: pos + 6 + l]
        q, item = outputEvent(item)
        return player, q, [item]

    def getSupportPowerEvent(x, pos):
        player = getPlayer(x, pos)
        return player, None, None

    def getChat(x, pos):
        if SEASON < 9:
            l = bytesToInt(x[pos])
            message = x[pos + 1: pos + 1 + l].decode('utf-8')
            clientIndex = x[pos + 1 + l]
            globalChannel = (x[pos-8:pos] != b'TeamChat')
        else:
            # Messages in the global channel have channel == 4.
            channel = x[pos]
            globalChannel = (channel == 4)
            l = bytesToInt(x[pos + 1])
            message = x[pos + 2: pos + 2 + l].decode('utf-8')
            clientOffset = (0 if globalChannel else 4)
            clientIndex = x[pos + 2 + l + clientOffset]
        return {'globalChannel': globalChannel, 'message': message, 'clientIndex': clientIndex}

    def getPos(x, term, start):
        """Search for a binary string and return the position just after it.
        
        x: The binary content to search through.
        term: The binary string to search for.
        start: The position to start the search from.
        Returns: The position just after the search term finishes, or the length of the content if the term is not found."""
        # This is needed in Python 3 to ensure we are searching for bytes in a bytes object.
        if isinstance(term, str):
            term = term.encode('utf-8')
        try:
            return x[start:].index(term) + len(term) + start
        except ValueError:
            # No more terms found.
            return len(x)

    def getPlaceBuildingPos(x, placeBuildingTerm, start):
        """Search for the a "place building" event and return the position just after it.
        
        x: The binary string to search through.
        placeBuildingTerm: The term to search for.
        start: The position to start the search from.
        Returns: The position just after the "place building" term, or the length of the content if none was found.
        Note that this tries to ignore invalid place building events by looking for other matching "place building" events soon after."""
        placeBuildingPos = getPos(x, placeBuildingTerm, start)
        if placeBuildingPos < len(x):
            player, q, eventList = getPlaceBuildingEvents(x, placeBuildingPos)
            # If player fails to place building then there will likely be another very soon after
            # (using trial and error this seems to be less than 1000 bytes after).
            nextPlaceBuildingPos = getPos(x, placeBuildingTerm, placeBuildingPos)
            while nextPlaceBuildingPos < len(x) and nextPlaceBuildingPos < placeBuildingPos + 1000:
                nextEventPlayer, nextEventQ, nextEventList = getPlaceBuildingEvents(x, nextPlaceBuildingPos)
                if nextEventPlayer == player and nextEventQ == q and eventList == nextEventList:
                    placeBuildingPos = nextPlaceBuildingPos
                nextPlaceBuildingPos = getPos(x, placeBuildingTerm, nextPlaceBuildingPos)
        return placeBuildingPos

    def removeLastStartProductionEvent(events, player, q, item):
        """Try to remove a specified "StartProduction" event from the player's queue."""
        try:
            # Remove the last StartProduction event from the event list.
            latestStartProductionIndex = len(events[player][q]) - list(reversed(events[player][q])).index(item) - 1
            events[player][q].pop(latestStartProductionIndex)
        except ValueError:
            # Cancelled something that wasn't being produced.
            pass

    def getField(x, field, start):
        """Search for the value of a field (e.g. 'Color: F5F872').
        
        x: The binary content to search through.
        field: The field name to search for (e.g. 'Color').
        start: The position to start the search from.
        Returns: The corresponding value (e.g. 'F5F872')."""
        fieldStart = getPos(x, field + b':', start)
        fieldEnd = getPos(x, b'\n', fieldStart)
        return x[fieldStart+1:fieldEnd-1].decode('utf-8')

    def getDateFieldAsTimestamp(x, field, start):
        value = getField(x, field, start)
        return datetime.datetime.strptime(value, "%Y-%m-%d %H-%M-%S").timestamp()

    # Build information comes after the "StartGame" command.
    startGame = x.index(b'StartGame')
    
    # Get end game information.
    rootPos = getPos(x, b'Root:', 0)
    if rootPos >= len(x):
        print('Unable to find end game information in {} - replay corrupted?'.format(filename))
        continue
    try:
        finalGameTick = int(getField(x, b'FinalGameTick', rootPos))
    except:
        # Earlier releases did not include this field.
        finalGameTick = None
    mapTitle = getField(x, b'MapTitle', rootPos)
    version = getField(x, b'Version', rootPos)
    startTime = getDateFieldAsTimestamp(x, b'StartTimeUtc', rootPos)
    endTime = getDateFieldAsTimestamp(x, b'EndTimeUtc', rootPos)
    
    factionPicks = set()
    # Try to get player information.
    for playerId in [0, 1]:
        pos = -1
        while True:
            pos = getPos(x, b'Player@%d:'%playerId, pos + 1)
            if pos >= len(x):
                break
            playerPos = pos
        name = getField(x, b'Name', playerPos)
        outcome = getField(x, b'Outcome', playerPos)
        clientIndex = int(getField(x, b'ClientIndex', playerPos))
        faction = getField(x, b'FactionName', playerPos)
        fingerprint = getField(x, b'Fingerprint', playerPos)
        if fingerprint != '':
            if fingerprint not in fingerPrintToProfile:
                response = requests.get('https://forum.openra.net/openra/info/' + fingerprint)
                profileID = 'Unknown'
                profileName = name
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line.startswith('ProfileID: '):
                        profileID = line[len('ProfileID: '):]
                    elif line.startswith('ProfileName: '):
                        profileName = line[len('ProfileName: '):]
                fingerPrintToProfile[fingerprint] = {'profileID': profileID, 'profileName': profileName}
                with open(FINGERPRINT_CACHE_FILE, 'a') as fingerprintCache:
                    fingerprintCache.write('{}\t{}\t{}\n'.format(fingerprint, profileID, profileName))

        pos = -1
        while True:
            pos = getPos(x, b'Client@%d:'%clientIndex, pos + 1)
            if pos >= len(x):
                break
            clientPos = pos
        factionPick = getField(x, b'Faction', clientPos)
        
        factionPicks.add(factionPick)
        
        players.append({'fingerprint': fingerprint,
                        'name': name,
                        'profileID': 'Unknown' if fingerprint == '' else fingerPrintToProfile[fingerprint]['profileID'],
                        'profileName': name if fingerprint == '' else fingerPrintToProfile[fingerprint]['profileName'],
                        'clientIndex': clientIndex,
                        'filename': filename,
                        'abbreviations': getAbbreviationsFromFilename(filename),
                        'faction': faction,
                        'factionPick': factionPick,
                        'outcome': outcome,
                        'finalGameTick': finalGameTick,
                        'startTime': startTime,
                        'endTime': endTime,
                        'mapTitle': mapTitle,
                        'version': version})
    if FACTION_PICK_FILTER != None and factionPicks != FACTION_PICK_FILTER:
        # Remove both players and skip processing the file.
        players = players[:-2]
        continue
    
    # Load any chat messages.
    pos = 0
    chat = []
    while pos < len(x):
        pos = getPos(x, b'Chat', pos)
        if pos < len(x):
            try:
                chat.append(getChat(x, pos))
            except UnicodeDecodeError:
                # Silently ignore chat message if it can't be decoded.
                pass
    chats.append(chat)
    
    events = defaultdict(lambda : defaultdict(list))
    actionMap = {b'StartProduction': (getPos, getStartProductionEvents),
                 b'PlaceBuilding': (getPlaceBuildingPos, getPlaceBuildingEvents),
                 b'LineBuild': (getPos, getPlaceBuildingEvents),
                 b'CancelProduction': (getPos, getCancelProductionEvent),
                 b'PauseProduction': (getPos, getPauseProductionEvent),
                 b'SovietSpyPlane': (getPos, getSupportPowerEvent),
                 b'SovietParatroopers': (getPos, getSupportPowerEvent),
                 b'UkraineParabombs': (getPos, getSupportPowerEvent),
                 b'Chronoshift': (getPos, getSupportPowerEvent),
                 # Iron Curtain comes from two different events (depending on OpenRA release).
                 b'GrantExternalConditionPowerInfoOrder': (getPos, getSupportPowerEvent),
                 b'GrantUpgradePowerInfoOrder': (getPos, getSupportPowerEvent),
                 b'NukePowerInfoOrder': (getPos, getSupportPowerEvent),
                 # Sonar Pulse
                 b'SpawnActorPowerInfoOrder': (getPos, getSupportPowerEvent)}
    pos = startGame
    build = defaultdict(list)
    actionList = defaultdict(list)
    posMap = {}
    try:
        while True:
            # Find the next action of each type in the file.
            for term, functions in actionMap.items():
                if term not in posMap:
                    getPosFn = functions[0]
                    posMap[term] = getPosFn(x, term, pos)
            minPos = min(posMap.values())
            # Break if we're at the end of the file.
            if minPos == len(x):
                break
            # Execute the functions corresponding to the type of event.
            for term, functions in actionMap.items():
                if posMap[term] == minPos:
                    # Reset this entry in posMap so that we look for the next matching term next iteration.
                    del posMap[term]
                    getEventFn = functions[1]
                    player, q, eventList = getEventFn(x, minPos)
                    if term in [b'StartProduction', b'PlaceBuilding', b'LineBuild']:
                        events[player][q] += eventList
                        if term == b'PlaceBuilding' and q == 0:
                            for item in eventList:
                                build[player].append(item)
                    elif term == b'PauseProduction':
                        # Remove item from queue, it will be re-added by another StartProduction event.
                        removeLastStartProductionEvent(events, player, q, item)
                    elif term == b'CancelProduction':
                        for item in eventList:
                            # For buildings then we can only cancel production if it was not placed.
                            unplaced = 0
                            for event in events[player][q]:
                                if event == item:
                                    unplaced += 1
                                elif event == '[{}]'.format(item):
                                    unplaced -= 1
                            if unplaced > 0:
                                removeLastStartProductionEvent(events, player, q, item)
                    actionList[player].append((term.decode('utf-8'), q, eventList))
            pos = minPos

        if len(events) != 2:
            # Probably one of the players gave no orders.
            print('Found game with {} player(s): {}'.format(len(events), filename))
            players = players[:-2]
            raise Exception
        
        for player in sorted(events.keys()):
            eventList = events[player]
            for q, queue in eventList.items():
                # Can be used to find which game contains an unusual item.
                if ITEM_TO_FIND in queue:
                    print('{} found in {} ({}) Count: {}'.format(ITEM_TO_FIND, filename, mapTitle, queue.count(ITEM_TO_FIND)))
                #print(player, q, ','.join(queue))
                unitList[q] += queue
            #if ''.join(build[player]).startswith('[PP][PP][PP]'):
            #    print(filename, mapTitle)
            builds.append(build[player])
            buildsByMap[mapTitle].append(build[player])
            # Convert defaultdict to list.
            queues.append(list(map(lambda q: eventList[q], range(len(itemMap)))))
            actions.append(actionList[player])
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
factionWin['Allies'] = factionWin['England'] + factionWin['France'] + factionWin['Germany']
factionLoss['Allies'] = factionLoss['England'] + factionLoss['France'] + factionLoss['Germany']
factionWin['Soviet'] = factionWin['Russia'] + factionWin['Ukraine']
factionLoss['Soviet'] = factionLoss['Russia'] + factionLoss['Ukraine']
print('Faction         Win Rate        From Random A/S      Picked Win Rate')
for factionTuple in [('England', ('England', 'RandomAllies'), 'england'),
                    ('France', ('France', 'RandomAllies'), 'france'),
                    ('Germany', ('Germany', 'RandomAllies'), 'germany'),
                    ('Allies', 'RandomAllies', ''),
                    ('Russia', ('Russia', 'RandomSoviet'), 'russia'),
                    ('Ukraine', ('Ukraine', 'RandomSoviet'), 'ukraine'),
                    ('Soviet', 'RandomSoviet', ''),
                    ('Random', '', '')]:
    factionReports = []
    for faction in factionTuple:
        if factionWin[faction] > 0 or factionLoss[faction] > 0:
            factionReports.append('{: >3}/{: >3} {:3.0f}%'.format(factionWin[faction], (factionWin[faction] + factionLoss[faction]), factionWin[faction] * 100.0 / (factionWin[faction] + factionLoss[faction])))
        else:
            factionReports.append('     ---    ')
    print('{: <12} {}'.format(factionTuple[0], '        '.join(factionReports)))

# A report of the buildings and units that were queued, and how effective they were.
for q in sorted(unitList.keys()):
    print('~~~ Queue {} ~~~'.format(q))
    outStrs = []
    for item, count in Counter(unitList[q]).most_common():
        if '[' not in item or ']' not in item:
            wins = 0
            losses = 0
            unknown = 0
            for i, queue in enumerate(queues):
                if item in queue[q]:
                    if players[i]['outcome'] == 'Won':
                        wins += 1
                        continue
                    elif players[i]['outcome'] == 'Lost':
                        losses += 1
                        continue
                    else:
                        unknown += 1
                        continue
            total = wins + losses + unknown
            buildRate = '{:0.0f}%'.format(total * 100.0 / len(builds))
            winRate = '---' if wins + losses == 0 else '{:0.0f}%'.format(wins * 100.0 / (wins + losses))
            outStrs.append('{}: {} ({} builds ({}), {} wins)'.format(itemNames[item], count, total, buildRate, winRate))
    print('\n'.join(outStrs))

def findPopularBuilds(builds, popularLimit=POPULAR):
    """Print a report of all popular build orders.
    
    builds: The complete set of build orders (every item built).
    popularLimit: How many occurrences are needed to class it as "popular"."""
    buildTree = defaultdict(lambda : defaultdict(list))
    buildTree[0][''] = builds
    out = []
    for depth in range(100):
        for priorBuilt in sorted(buildTree[depth].keys()):
            oldBuilds = buildTree[depth][priorBuilt]
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
for profileName in sorted(set(map(lambda player: player['profileName'], players))):
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
    print(u'=== {} (Played {} game(s), Win Rate {}, Factions {}) ==='.format(profileName, len(playerBuilds), winRate, factionStr))
    findPopularBuilds(playerBuilds, POPULAR_FOR_PLAYER)

# A report for each map of the most popular build orders.
mapPickCounter = Counter()
for mapTitle in buildsByMap.keys():
    mapPickCounter[mapTitle] += len(buildsByMap[mapTitle])
for mapTitle, count in mapPickCounter.most_common():
    print('### {} (Picked {} time(s)) ###'.format(mapTitle, int(count / 2)))
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

def factionResult(player, opponent):
    if player['faction'] in ('England', 'France', 'Germany'):
        faction = 'A'
    else:
        faction = 'S'
    if opponent['faction'] in ('England', 'France', 'Germany'):
        opponentFaction = 'A'
    else:
        opponentFaction = 'S'
    pair = faction + opponentFaction
    if player['outcome'] == 'Won':
        return (pair, 1, 0)
    elif player['outcome'] == 'Lost':
        return (pair, 0, 1)
    return (pair, 0, 0)

# A report of best faction by player.
print('=== Faction-Player Win Rates ===')
print('Name             | Allies vs A  | Allies vs S  | Soviet vs A  | Soviet vs S  ')
print('-----------------+--------------+--------------+--------------+--------------')
for profileName in sorted(set(map(lambda player: player['profileName'], players))):
    factionWins = defaultdict(int)
    factionLosses = defaultdict(int)
    for i in range(len(players) // 2):
        playerA = players[2*i]
        playerB = players[2*i+1]
        if playerA['profileName'] == profileName:
            pair, wins, losses = factionResult(playerA, playerB)
            factionWins[pair] += wins
            factionLosses[pair] += losses
        if playerB['profileName'] == profileName:
            pair, wins, losses = factionResult(playerB, playerA)
            factionWins[pair] += wins
            factionLosses[pair] += losses
    factionWinRates = []
    for pair in ['AA', 'AS', 'SA', 'SS']:
        total = factionWins[pair] + factionLosses[pair]
        if total == 0:
            factionWinRates.append('            ')
        else:
            factionWinRates.append('{:2d}/{:2d} ({:3.0f}%)'.format(factionWins[pair], total, factionWins[pair] * 100.0 / total))
    print(u'{:16s} | {}'.format(profileName, ' | '.join(factionWinRates)))

if DUMP_DATA:
    with open('builds.{}.json'.format(SEASON), 'w') as f:
        json.dump(builds, f)
    with open('players.{}.json'.format(SEASON), 'w') as f:
        json.dump(players, f)
    with open('chats.{}.json'.format(SEASON), 'w') as f:
        json.dump(chats, f)
    with open('queues.{}.json'.format(SEASON), 'w') as f:
        json.dump(queues, f)
    with open('actions.{}.json'.format(SEASON), 'w') as f:
        json.dump(actions, f)
