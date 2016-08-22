#!/usr/bin/env python
import re
from decimal import Decimal
import nagiosplugin
good_header = ['VEID', 'user', 'nice', 'system', 'uptime', 'idle', 'strv', 'uptime', 'used', 'maxlat', 'totlat', 'numsched']

class Vestat(nagiosplugin.Resource):
    def __init__(self, fname="vestat", statefile="/tmp/vestat.cookie"):
        self.fname = fname
        self.statefile = statefile

    def from_file(self):
        with open(self.fname) as f:
            return f.read()

    def probe(self):
        raw_text = self.from_file()
        lines = raw_text.split('\n')
        def to_list(s):
            return re.split(' +', s.strip())
        header = to_list(lines[1])
        if header != good_header:
            raise("Possible error parsing vestat data")
        with nagiosplugin.Cookie(self.statefile) as cookie:

            for line in lines[2:]:
                if line == "":
                    continue
                row = to_list(line)
                veid = row[0]
                data = dict(zip(header[1:5], to_list(line)[1:5]))
                diff = {}
                for k, v in data.items():
                    mname = '{metric} {veid}'.format(metric=k, veid=veid)
                    old = cookie.get(mname, None)
                    cookie[mname] = int(v)
#                    yield nagiosplugin.Metric(mname, v, uom='jif', min=0, context='jiffies')
                    if old is None:
                        continue
                    dv = int(v) - old
                    diff[k] = dv
                print diff
                if all(x in diff for x in header[1:5]) and diff['uptime']>0:
                    cpu = (diff['user'] + diff['nice'] + diff['system']) / Decimal(diff['uptime'])
                    cpu = cpu.quantize(Decimal('.01'))
                    yield nagiosplugin.Metric('CPU {0}'.format(veid), cpu,
                                              uom='%', min=0, max=100, context='default')

def main():
    check = nagiosplugin.Check(
        Vestat(),
        nagiosplugin.ScalarContext('jiffies', "@0:", "@0:")
    )
    check.main()

main()