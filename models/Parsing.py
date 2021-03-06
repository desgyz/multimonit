import xml.etree.cElementTree as ET
from models import Config
import urllib, ssl, urlparse, datetime

def loop(data):
    for key, value in data.iteritems():
        if key == "uptime":
            # do something with value
            data[key] = duration(value)

def duration(seconds):
    config = Config.readconfig()
    time = config["time"]

    if time == "Week Day Hour Minute Second":
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 7)
        if weeks == 0:
            date = '{}D {}H {}M {}S'.format(days, hours, minutes, seconds)
        elif days == 0:
            date = '{}H {}M {}S'.format(hours, minutes, seconds)
        elif hours == 0:
            date = '{}M {}S'.format(minutes, seconds)
        else:
            date = '{}W {}D {}H {}M {}S'.format(weeks, days, hours, minutes, seconds)

    elif time == "Day Hour Minute Second":
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        if days == 0:
            date = '{}H {}M {}S'.format(hours, minutes, seconds)
        if hours == 0:
            date = '{}M {}S'.format(minutes, seconds)
        else:
            date = '{}D {}H {}M {}S'.format(days, hours, minutes, seconds)

    elif time == "Week Day Hour Minute":
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 7)

        if weeks == 0:
            date = '{}D {}H {}M'.format(days, hours, minutes)
        elif days == 0:
            date = '{}H {}M'.format(hours, minutes)
        elif hours == 0:
            date = '{}M'.format(minutes)
        else:
            date = '{}W {}D {}H {}M'.format(weeks, days, hours, minutes)

    elif time == "Year Day Hour Minute":
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 7)
        years, weeks = divmod(days, 52)

        if years == 0:
            date = '{}D {}H {}M'.format(days, hours, minutes)
        elif days == 0:
            date = '{}H {}M'.format(hours, minutes)
        elif hours == 0:
            date = '{}M'.format(minutes)
        else:
            date = '{}Y {}D {}H {}M'.format(years, days, hours, minutes)

    return str(date)

def system():

    # read config
    config = Config.readconfig()
    url = config["URLS"]

    parsed = []

    # for loop of URls in config
    for m in url:
        data = {}
        de = []
        hostlst = []
        fs = []

        # parse the xml whether its a local xml file or remote
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        monit = ET.parse(urllib.urlopen(m, context=ctx)) or ET.parse(m)
        root = monit.getroot()

        # find and save daemon xml data
        for i in root.findall("*[@type='3']"):
            daemon = {h.tag: h.text for h in i if h.text != '\n            ' and h.text != '\n      ' and h.text != None and h.text != '\n          '}
            daemon.update({"mem": {h.tag: h.text for l in i.iter("memory") for h in l}})
            daemon.update({"cpu":{h.tag: h.text for l in i.iter("cpu") for h in l}})
            daemon.update({"port":{h.tag: h.text for l in i.iter("port") for h in l}})
            loop(daemon)
            de.append(daemon)

        data.update({"process": de})

        # find and save host xml data
        for i in root.findall("*[@type='4']"):
            host = {h.tag: h.text for h in i if h.text != '\n            ' and h.text != '\n      ' and h.text != None and h.text != '\n          '}
            host.update({"port": {h.tag: h.text for l in i.iter("port") for h in l}})
            loop(host)
            hostlst.append(host)

        data.update({"host": hostlst})

        # find and save filesystem xml data
        for i in root.findall("*[@type='0']"):
            file = {h.tag: h.text for h in i if h.text != '\n            ' and h.text != '\n      ' and h.text != None and h.text != '\n          '}
            file.update({"block": {h.tag: h.text for l in i.iter("block") for h in l}})
            file.update({"inode": {h.tag: h.text for l in i.iter("inode") for h in l}})
            loop(file)
            fs.append(file)

        data.update({"fs": fs})

        # find and save system details xml data
        sys = {h.tag: h.text for i in root.findall("*[@type='5']") for h in i if h.text != '\n            ' and h.text != '\n      ' and h.text != None and h.text != '\n          '}
        loop(sys)
        sys.update({"load": {h.tag: h.text for i in root.findall("*[@type='5']/system/load") for h in i}, "cpu": {h.tag: h.text for i in root.findall("*[@type='5']/system/cpu") for h in i}, "memory":{h.tag: h.text for i in root.findall("*[@type='5']/system/memory") for h in i}, "swap":{h.tag: h.text for i in root.findall("*[@type='5']/system/swap") for h in i}, "server": {h.tag: h.text for i in root.findall("server") for h in i}, 'platform': {h.tag: h.text for i in root.findall('platform') for h in i}})
        loop(sys["server"])
        data.update({"sys": sys})
        netloc = urlparse.urlparse(m).netloc
        scheme = urlparse.urlparse(m).scheme
        data.update({"url": scheme + ":\\\\www." + netloc })
        loop(data)

        parsed.append(data)

    return parsed

