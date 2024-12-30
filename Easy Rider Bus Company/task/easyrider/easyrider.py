import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

test_input = ('[{"bus_id": 128, "stop_id": 1, "stop_name": "Prospekt Avenue", "next_stop": 3, "stop_type": "S", "a_time": "08:12"}, '
              '{"bus_id": 128, "stop_id": 3, "stop_name": "Elm Street", "next_stop": 5, "stop_type": "O", "a_time": "08:19"}, '
              '{"bus_id": 128, "stop_id": 5, "stop_name": "Fifth Avenue", "next_stop": 7, "stop_type": "O", "a_time": "08:25"}, '
              '{"bus_id": 128, "stop_id": 7, "stop_name": "Sesame Street", "next_stop": 0, "stop_type": "F", "a_time": "08:37"}, '
              '{"bus_id": 256, "stop_id": 2, "stop_name": "Pilotow Street", "next_stop": 3, "stop_type": "S", "a_time": "09:20"}, '
              '{"bus_id": 256, "stop_id": 3, "stop_name": "Elm Street", "next_stop": 6, "stop_type": "", "a_time": "09:45"}, '
              '{"bus_id": 256, "stop_id": 6, "stop_name": "Abbey Road", "next_stop": 7, "stop_type": "O", "a_time": "09:59"}, '
              '{"bus_id": 256, "stop_id": 7, "stop_name": "Sesame Street", "next_stop": 0, "stop_type": "F", "a_time": "10:12"}, '
              '{"bus_id": 512, "stop_id": 4, "stop_name": "Bourbon Street", "next_stop": 6, "stop_type": "S", "a_time": "08:13"}, '
              '{"bus_id": 512, "stop_id": 6, "stop_name": "Abbey Road", "next_stop": 0, "stop_type": "F", "a_time": "08:16"}]')
suffixes = (" Road", " Avenue", " Boulevard", " Street")
valid_stop_types = ('S', 'O', 'F', '')
err_freq = {}
line_to_stops = {}


@dataclass
class BusStop:
    bus_id: int = -1
    stop_id: int = -1
    stop_name: str = 'N/A'
    next_stop: int = -1
    stop_type: str = 'N/A'
    a_time: str = 'N/A'


stops: list[BusStop] = []


def parse_check_types(j: List[Dict]):
    for i in j:
        for field, value in i.items():
            err_freq.setdefault(field, 0)
            match (field, value):
                case ('bus_id', int()):
                    line_to_stops.setdefault(value, 0)
                    line_to_stops[value] += 1
                    bus_id = int(value)
                case ('stop_id', int()):
                    stop_id = value
                case ('stop_id', str()):  # still have to turn ascii representation of value back to int
                    err_freq[field] += 1
                    try:
                        stop_id = int(value)
                    except ValueError:
                        stop_id = -1
                case ('next_stop', int()):
                    next_stop = int(value)
                case ('next_stop', str() | float()):
                    err_freq[field] += 1
                    try:
                        next_stop = int(value)
                    except ValueError:
                        next_stop = -1
                case ('stop_type', str()):
                    if value not in valid_stop_types:
                        err_freq[field] += 1

                    stop_type = value
                case ('stop_name', str()):
                    if not value.istitle() or not value.endswith(suffixes):
                        err_freq[field] += 1
                    stop_name = value
                case ('a_time', str()):
                    if len(value) != 5:
                        err_freq[field] += 1
                    else:
                        try:
                            datetime.strptime(value, "%H:%M")
                            a_time = value
                        except ValueError:
                            err_freq[field] += 1
                case _:
                    err_freq[field] += 1
        s = BusStop(bus_id, stop_id, stop_name, next_stop, stop_type, a_time)
        stops.append(s)


def main():
    j = json.loads(input())
    # j = json.loads(test_input)
    # print(json.dumps(j, indent=4), file=sys.stderr)

    parse_check_types(j)

    # extra check for increasing arrival time for each line
    check_arrival_time = defaultdict(list)
    for stop in stops:
        check_arrival_time[stop.bus_id].append(stop)
    for bus_id, _ in check_arrival_time.items():
        if check_arrival_time[bus_id][-1].stop_type != 'F':
            check_arrival_time[bus_id].sort(key=lambda s: s.next_stop)
            check_arrival_time[bus_id].append(check_arrival_time[bus_id].pop(0))
    for bus_id, line_stops in check_arrival_time.items():
        prev = datetime.strptime(line_stops[0].a_time, "%H:%M")
        for n in line_stops[1:]:
            n = datetime.strptime(n.a_time, "%H:%M")
            if n < prev:
                err_freq['a_time'] += 1
                break
            prev = n
    print(f'Type and field validation: {sum(err_freq.values())} errors')
    for k, v in err_freq.items():
        print(f'{k}: {v}')

    print(f'Line names and number of stops:')
    for k, v in line_to_stops.items():
        print(f'bus_id: {k} stops: {v}')

    start_final = ((s.bus_id, s.stop_type) for s in stops if s.stop_type in ['S', 'F'])
    bus_groups_types = defaultdict(list)
    for bus_id, stop_type in start_final:
        bus_groups_types[bus_id].append(stop_type)

    for bus_id, stop_types in bus_groups_types.items():
        c = Counter(stop_types)
        if c['S'] != 1 or c['F'] != 1:
            print(f'There is no start or end stop for the line: {bus_id}')
            return

    start_stops = {s.stop_name for s in stops if s.stop_type == 'S'}
    start_stops = list(start_stops)
    start_stops.sort()

    finish_stops = {s.stop_name for s in stops if s.stop_type == 'F'}
    finish_stops = list(finish_stops)
    finish_stops.sort()

    stop_id_counts = Counter(s.stop_id for s in stops)
    transfer_stops_ids = {id for id, c in stop_id_counts.items() if c > 1}
    transfer_stops = {stop.stop_name for stop in stops if stop.stop_id in transfer_stops_ids and stop.stop_id != -1}
    transfer_stops = list(transfer_stops)
    transfer_stops.sort()

    ondemand_stops = {stop.stop_name for stop in stops if stop.stop_type == 'O'}
    ondemand_stops = ondemand_stops - set(transfer_stops)
    ondemand_stops = list(ondemand_stops)
    ondemand_stops.sort()

    print(f'Start stops: {len(start_stops)} {start_stops}')
    print(f'Transfer stops: {len(transfer_stops)} {transfer_stops}')
    print(f'Finish stops: {len(finish_stops)} {finish_stops}')
    print(f'Finish stops: {len(ondemand_stops)} {ondemand_stops}')

if __name__ == "__main__":
    main()
