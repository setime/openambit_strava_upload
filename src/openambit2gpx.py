#!/usr/bin/python3

""" converts the *.log files produced by openambit in ~/.openambit/ to standard gpx format.
usage: ./openambit2gpx.py inputfile outputFile
"""

# from lxml import etree # does not allow namespace prefixes which are required for gpx extensions; everything else in this script would work otherwise with lxml
import xml.etree.ElementTree as etree

# Look at http://www.topografix.com/GPX/1/1/gpx.xsd and https://www8.garmin.com/xmlschemas/TrackPointExtensionv2.xsd for XML Schemata for GPX files


ACTIVITY_MAP = {
    "Mountaineering": "Hike",
    "Running": "Run",
    "Cycling": "Ride",
    "Openwater swimming": "Swim",
    "Multisport": "Run",
}


def utcSplitConvSeconds(utcTime):
    """Splits the UTC time code YYYY-MM-DDTHH:MM:SS.SSSZ, keeps only the time part and converts it into seconds."""

    import math

    tmpTime = utcTime.split("T")[1].split("Z")[0].split(":")
    tmpDay = int(utcTime.split("T")[0].split("-")[2])
    secs = (
        float(tmpDay) * 24 * 3600
        + float(tmpTime[0]) * 3600
        + float(tmpTime[1]) * 60
        + float(tmpTime[2])
    )

    return secs


def timeDiff(utcTime1, utcTime2):
    """Computes the difference, in seconds, between an earlier (utcTime1) and a later date (utcTime2). Only safe for dates within the same month or less than 2 days apart if on the boundary of a month."""

    secs1 = utcSplitConvSeconds(utcTime1)
    secs2 = utcSplitConvSeconds(utcTime2)

    if int(utcTime2.split("T")[0].split("-")[2]) == 1:
        secs1 -= (
            float(utcTime2.split("T")[0].split("-")[2]) * 24 * 3600
        )  # if second date is on a first of a month, then the previous day gets reset to day 0 of the same month

    return secs2 - secs1


class ibiToHr(object):
    def __init__(self, average_hr=False):
        self.ibitimeLast = None
        self.hrLast = 0
        self.hrlist = []
        self.average_hr = average_hr

    def ibiToHr(self, element):
        """Parse a list of IBI times to heart rates, always return some hr rate"""
        sampType = element.findtext("Type")

        if sampType == "ibi":
            ibitime = element.findtext("Time")
            if self.ibitimeLast != ibitime:
                self.hrlist = [int(element.text) for element in element.findall("IBI")]

                if self.average_hr:
                    # filter 1: average hr data, flatten data
                    ibi_avg = sum(self.hrlist) / len(self.hrlist)
                    self.hrlist = [ibi_avg]

            self.ibitimeLast = ibitime

        if len(self.hrlist) > 0:
            # take first element of list to convert to HR
            hr = 60.0 / (self.hrlist[0] / 1000.0)  # convert IBI to beats/min
            del self.hrlist[0]
        else:
            # no data is available anymore
            hr = self.hrLast

        # filter 2: sensor errors
        hrmin = 40  # Mimimum heart rate for humans
        hrmax = 220  # Maximum heart rate for hiumans
        if hr > hrmax or hr < hrmin:
            hr = self.hrLast

        self.hrLast = hr
        ret = None if self.hrLast == 0 else str(int(self.hrLast))
        return ret


def convert(fileIn, fileOut, average_hr=True):
    ###########################################
    ## setting variables up, starting output ##
    ###########################################
    activityType = None
    rootIn = etree.parse(fileIn)

    fOut = open(fileOut, "w")

    fOut.write('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n\n')
    fOut.write(
        '<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="openambit2gpx" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:gpxdata="http://www.cluetrust.com/XML/GPXDATA/1/0" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.cluetrust.com/XML/GPXDATA/1/0 http://www.cluetrust.com/Schemas/gpxdata10.xsd">'
    )
    fOut.write(" <trk>\n")

    # Fill meta data information
    for element in rootIn.iterfind("Log/Header"):
        activityType = element.findtext("ActivityTypeName")

    if activityType is not None:
        fOut.write(f"  <type>{ACTIVITY_MAP[activityType]}</type>\n")

    fOut.write("  <trkseg>\n")

    latLast = None
    lonLast = None
    timeLast = None
    altitudeLast = None
    hrLast = None
    cadenceLast = None
    powerLast = None
    speedLast = None
    tempLast = None
    airpressureLast = None
    latLatest = None
    lonLatest = None
    timeGPSLatest = None

    lapCount = 0
    lapArray = [0]
    maxLap = 0

    ###########################
    ## getting activity data ##
    ###########################
    ibiconvertor = ibiToHr(average_hr=average_hr)

    # Fill waypoints
    for element in rootIn.iterfind("Log/Samples/Sample"):

        # Position samples just repeat positional/time information in the previous gps-base sample
        # Thus simply skip these to avoid creating duplicate gpx trkpts
        sampType = element.findtext("Type")
        if sampType == "position":
            continue

        trk = etree.Element("trkpt")

        lat = element.findtext("Latitude")
        lon = element.findtext("Longitude")
        time = element.findtext("UTC")

        altitude = (
            element.findtext("Altitude")
            if element.findtext("Altitude") != None
            else altitudeLast
        )
        hr = element.findtext("HR") if element.findtext("HR") != None else hrLast
        if hr == None:
            hr = ibiconvertor.ibiToHr(element)

        cadence = (
            element.findtext("Cadence")
            if element.findtext("Cadence") != None
            else cadenceLast
        )
        power = (
            element.findtext("BikePower")
            if element.findtext("BikePower") != None
            else powerLast
        )
        speed = (
            str(float(element.findtext("Speed")) / 100)
            if element.findtext("Speed") != None
            else speedLast
        )
        temp = (
            str(float(element.findtext("Temperature")) / 10)
            if element.findtext("Temperature") != None
            else tempLast
        )
        airpressure = (
            element.findtext("SeaLevelPressure")
            if element.findtext("SeaLevelPressure") != None
            else airpressureLast
        )

        if sampType == "lap-info":
            lapType = element.findtext("Lap/Type")
            lapDate = element.findtext("Lap/DateTime")
            lapDuration = element.findtext("Lap/Duration")
            lapDistance = element.findtext("Lap/Distance")
            lapUtc = element.findtext("UTC")
            lapPreviousLat = latLatest
            lapPreviousLon = lonLatest
            lapPreviousTime = timeGPSLatest
            lapCheck = 1

            if lapCount == 0:
                lapArray[0] = [
                    lapType,
                    lapDate,
                    lapDuration,
                    lapDistance,
                    lapUtc,
                    lapPreviousLat,
                    lapPreviousLon,
                    lapPreviousTime,
                    0,
                    0,
                    0,
                ]
            else:
                lapArray.append(
                    [
                        lapType,
                        lapDate,
                        lapDuration,
                        lapDistance,
                        lapUtc,
                        lapPreviousLat,
                        lapPreviousLon,
                        lapPreviousTime,
                        0,
                        0,
                        0,
                    ]
                )
            lapCount += 1

        maxLap = lapCount - 1

        if lat != None and lon != None:
            lat = float(lat) / 10000000
            lon = float(lon) / 10000000

            trk.set("lat", str(lat))
            trk.set("lon", str(lon))

            latLatest = str(lat)
            lonLatest = str(lon)
            timeGPSLatest = time

            if lapCheck == 1:
                lapArray[lapCount - 1][8] = latLatest
                lapArray[lapCount - 1][9] = lonLatest
                lapArray[lapCount - 1][10] = timeGPSLatest
                lapCheck = 0

            if altitude != None:
                etree.SubElement(trk, "ele").text = altitude
            elif altitudeLast != None:
                etree.SubElement(trk, "ele").text = altitudeLast

            if time != None and len(time) > 0:
                etree.SubElement(trk, "time").text = time
            elif timeLast != None and len(timeLast) > 0:
                etree.SubElement(trk, "time").text = timeLast

            if (
                hr != None
                or cadence != None
                or power != None
                or speed != None
                or temp != None
                or airpressure != None
            ):
                extGpx = etree.SubElement(trk, "extensions")
                if hr != None:
                    etree.SubElement(extGpx, "gpxdata:hr").text = hr
                if cadence != None:
                    etree.SubElement(extGpx, "gpxdata:cadence").text = cadence
                if power != None:
                    etree.SubElement(extGpx, "gpxdata:power").text = power
                if temp != None:
                    etree.SubElement(extGpx, "gpxdata:temp").text = temp
                if speed != None:
                    etree.SubElement(extGpx, "gpxdata:speed").text = speed
                if airpressure != None:
                    etree.SubElement(extGpx, "gpxdata:SeaLevelPressure").text = (
                        airpressure
                    )

            fOut.write("   " + etree.tostring(trk).decode() + "\n")

        latLast = lat
        lonLast = lon
        timeLast = time
        altitudeLast = altitude
        hrLast = hr
        cadenceLast = cadence
        powerLast = power
        speedLast = speed
        tempLast = temp
        airpressureLast = airpressure

        lat = None
        lon = None
        time = None
        altitude = None
        hr = None
        cadence = None
        power = None
        speed = None
        temp = None
        airpressure = None

    fOut.write("  </trkseg>\n")
    fOut.write(" </trk>\n")

    #############################
    ## getting lap information ##
    #############################

    lapCount = 0
    previousEndTime = 0

    fOut.write(" <extensions>\n")

    previousLatEP = 0
    previousLonEP = 0
    for i in range(0, len(lapArray)):
        if lapArray[i][0] == "Manual":
            lap = etree.Element("gpxdata:lap")
            lap.set("xmlns", "http://www.cluetrust.com/XML/GPXDATA/1/0")

            startTime = lapArray[0][4] if lapCount == 0 else previousEndTime
            previousEndTime = lapArray[i][4]

            etree.SubElement(lap, "index").text = str(lapCount)
            etree.SubElement(lap, "startTime").text = startTime
            etree.SubElement(lap, "elapsedTime").text = str(
                float(lapArray[i][2]) / 1000
            )
            etree.SubElement(lap, "distance").text = lapArray[i][3]

            latInterPolSP = lapArray[0][8] if lapCount == 0 else previousLatEP
            lonInterPolSP = lapArray[0][9] if lapCount == 0 else previousLonEP

            if i == maxLap:
                latInterPolEP = lapArray[i][5]
            else:
                t = lapArray[i][4]
                t1 = lapArray[i][7]
                t2 = lapArray[i][10]
                lat1 = float(lapArray[i][5]) if lapArray[i][5] != None else 0.0
                lat2 = float(lapArray[i][8]) if lapArray[i][8] != None else 0.0
                # only try to parse time difference if both times look like valid timestamps
                if (
                    t1 != None
                    and t2 != None
                    and t1 != 0
                    and t2 != 0
                    and "T" in t1
                    and "Z" in t2
                    and "T" in t1
                    and "Z" in t2
                ):
                    latInterPolEP = str(
                        ((lat2 - lat1) / timeDiff(t1, t2)) * timeDiff(t1, t) + lat1
                    )
                else:
                    print("Failed to interpolate with t1: ", t1, ", t2: ", t2)
                    latInterPolEP = 0

            if i == maxLap:
                lonInterPolEP = lapArray[i][6]
            else:
                t = lapArray[i][4]
                t1 = lapArray[i][7]
                t2 = lapArray[i][10]
                lon1 = float(lapArray[i][6]) if lapArray[i][6] != None else 0.0
                lon2 = float(lapArray[i][9]) if lapArray[i][9] != None else 0.0
                # only try to parse time difference if both times look like valid timestamps
                if (
                    t1 != None
                    and t2 != None
                    and t1 != 0
                    and t2 != 0
                    and "T" in t1
                    and "Z" in t2
                    and "T" in t1
                    and "Z" in t2
                ):
                    lonInterPolEP = str(
                        ((lon2 - lon1) / timeDiff(t1, t2)) * timeDiff(t1, t) + lon1
                    )
                else:
                    print("Failed to interpolate with t1: ", t1, ", t2: ", t2)
                    lonInterPolEP = 0

            previousLatEP = latInterPolEP
            previousLonEP = lonInterPolEP
            SP = etree.SubElement(lap, "startPoint")
            SP.text = " "
            SP.set("lat", str(latInterPolSP))
            SP.set("lon", str(lonInterPolSP))
            EP = etree.SubElement(lap, "endPoint")
            EP.text = " "
            EP.set("lat", str(latInterPolEP))
            EP.set("lon", str(lonInterPolEP))

            etree.SubElement(lap, "intensity").text = "active"
            trigger = etree.SubElement(lap, "trigger")
            trigger.text = " "
            trigger.set("kind", "manual")

            # the elements below need to be added for the gpx file to be understood; data all set to 0
            etree.SubElement(lap, "calories").text = "0"
            sumHrAvg = etree.SubElement(lap, "summary")
            sumHrAvg.text = "0"
            sumHrAvg.set("kind", "avg")
            sumHrAvg.set("name", "hr")
            sumHrMax = etree.SubElement(lap, "summary")
            sumHrMax.text = "0"
            sumHrMax.set("kind", "max")
            sumHrMax.set("name", "hr")
            sumCadAvg = etree.SubElement(lap, "summary")
            sumCadAvg.text = "0"
            sumCadAvg.set("kind", "avg")
            sumCadAvg.set("name", "cadence")
            sumSpeedMax = etree.SubElement(lap, "summary")
            sumSpeedMax.text = "0"
            sumSpeedMax.set("kind", "max")
            sumSpeedMax.set("name", "speed")

            lapCount += 1

            fOut.write("  " + etree.tostring(lap).decode() + "\n")

    fOut.write(" </extensions>\n")

    #########################
    ## closing output file ##
    #########################

    fOut.write("</gpx>\n")
    fOut.close()

    return rootIn
