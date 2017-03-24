#/usr/bin/python
"""
hrv2domo.py
Reads data from HRV system
Sends data to Domoticz

for automation set up a crontab:

    $ crontab -e
add rule (a measurement every 5 minutes):

    5 * * * * python /home/pi/domoticz/hrv2domo.py

"""

import urllib
import urllib2
import lxml.html
import base64
import time

hrvuser = ""
hrvpass = ""
hrvIP = "192.168.1.4"
hrvPort = "80"

domouser = ""
domopass = ""
domoIP = "127.0.0.1"
domoPort = "8082"

outsideIDx = [9, "temperature"]
outside_humidityIDx = [10, "humidity"]
outside_dewpointIDx = [11, "temperature"]
supplyIDx = [12, "temperature"]
extractIDx = [13, "temperature"]
extract_humidityIDx = [14, "humidity"]
extract_dewpointIDx = [15, "temperature"]
exhaustIDx = [16, "temperature"]
efficiencyIDx = [17, "efficiency"]
supply_setpointIDx = [18, "percentage"]
exhaust_setpoint = [19, "percentage"]
uptimeIDx = [20, "uptime"]

domoURL = ("http://%s:%s/json.htm?type=command&param=udevice" % (domoIP, domoPort))
domoLogURL = ("http://%s:%s/json.htm?type=command&param=addlogmessage&message=" % (domoIP, domoPort))
hrvURL = ("http://%s:%s" % (hrvIP, hrvPort))

base64string = base64.encodestring('%s:%s' % (domouser, domopass))[:-1]

def makeRequest(url,payload=None):
    global urllib2
    if payload:
        # Use urllib to encode the payload
        data = urllib.urlencode(payload)
        req = urllib2.Request(url, data)
    else:
        req = urllib2.Request(url)

    # Make the request and read the response
    try:
        resp = urllib2.urlopen(req)
    except urllib2.URLError, e:
        print e.code
    else:
        body = resp.read()
        return body;

def domoticzrequest (url):
    try:
        request = urllib2.Request(url)
        #request.add_header("Authorization", "Basic %s" % base64string)
        response = urllib2.urlopen(request)
    except urllib2.URLError, e:
        print ("URLError '%s' for url '%s'" % (e,url))
    except urllib2.HTTPError, e:
        print ("HTTPError '%s' for url '%s'" % (e,url))
    return None;

def parseTable(html):
    root = lxml.html.fromstring(html)
    data = root.xpath('//tr//text()')
    return data

def collect_data(data):
    items = []
    output = parseTable(data)
    for i in output:
	time.sleep(0.005)
        if ":" in i: # this is uptime in DAYS:HOURS:MINUTES:SECONDS, convert to days
            t = i.split(":")
            days = float(t[0])
            hours = float(t[1])
            minutes = float(t[2])
            seconds = float(t[3])
            uptime = days + hours/24 + minutes/60/24 + seconds/60/60/24
            uptime = round(uptime, 2)
            items.append("{0:0.2f}".format(uptime))
        try:
            item = float(i)
            items.append(i)
        except:
            pass
    return items

def create_dict():
    data = makeRequest(hrvURL)
    values = collect_data(data)

    keys = [outsideIDx[0], outside_humidityIDx[0], outside_dewpointIDx[0], supplyIDx[0], extractIDx[0], extract_humidityIDx[0],
           extract_dewpointIDx[0], exhaustIDx[0], efficiencyIDx[0], supply_setpointIDx[0], exhaust_setpoint[0], uptimeIDx[0]]

    types = [outsideIDx[1], outside_humidityIDx[1], outside_dewpointIDx[1], supplyIDx[1], extractIDx[1], extract_humidityIDx[1],
           extract_dewpointIDx[1], exhaustIDx[1], efficiencyIDx[1], supply_setpointIDx[1], exhaust_setpoint[1], uptimeIDx[1]]

    dictionary = dict(zip(keys, zip(values, types)))
    return dictionary

def sendToDomo():# Send data to Domoticz
    dict = create_dict()
    for key, value in dict.iteritems():
        try:
            if "temperature" in value[1]:
                url = domoURL + "&idx=%s&nvalue=0&svalue=%s" % (key, value[0])
                print "url sent: ", url
                domoticzrequest(url)
            if "humidity" in value[1]:
                humidity = round(float(value[0]))
                url = domoURL + "&idx=%s&nvalue=%s&svalue=0" % (key, int(humidity))
                print "url sent: ", url
                domoticzrequest(url)
            if "percentage" in value[1]:
                percentage = (float(value[0])/255)*100
                url = domoURL + "&idx=%s&nvalue=0&svalue=%s" % (key, "%.2f" % percentage)
                print "url sent: ", url
                domoticzrequest(url)
            if "efficiency" in value[1]:
                url = domoURL + "&idx=%s&nvalue=0&svalue=%s" % (key, value[0])
                print "url sent: ", url
                domoticzrequest(url)
            if "uptime" in value[1]:
                url = domoURL + "&idx=%s&svalue=%s" % (key, value[0])
                print "url sent: ", url
                domoticzrequest(url)
	except:
            print ("Error sending key %s and value %s" % (key, value))
            url = domoLogURL + urllib.quote_plus(("Error in HRV measurement cycle for key '%s' and value '%s'" % (key, value[0])))
            domoticzrequest(url)

    url = domoLogURL + urllib.quote_plus("HRV measurement cycle finished successfully")
    print "url sent: ", url
    domoticzrequest(url)

if __name__ == '__main__':
    sendToDomo()
