import struct
import datetime
import os
import csv
import argparse
import sys
from xlsxwriter import Workbook

argParser = argparse.ArgumentParser(description='Parse Firefox cache2 index file.')
argParser.add_argument('file', help='index file to parse')
argParser.add_argument('-o', '--output', help='CSV output file')
argParser.add_argument('-v', '--verbose', action='store_true', default=False, help='Print cache while parsing')
args = argParser.parse_args()

verbose = args.verbose
doCsv, doXlsx, saved = False, False, False

indexFile = open(args.file, 'r')
indexFileSize = os.path.getsize(args.file)

version = struct.unpack('>i', indexFile.read(4))[0]
print version
dirty = struct.unpack('>i', indexFile.read(4))[0]
print dirty
try:
    lastWrittenInt = struct.unpack('>i', indexFile.read(4))[0]
    lastWritten = datetime.datetime.fromtimestamp(lastWrittenInt)
    print lastWritten
except:
    print('Error')

count = 0

if args.output :
    ext = os.path.splitext(args.output)[-1]
    if ext == '.csv':
        doCsv = True
    elif ext == '.xlsx':
        doXlsx = True
    else:
        verbose = True
    if doXlsx:
        workbook = Workbook(args.output)
        bold = workbook.add_format({'bold': True})
        worksheet1 = workbook.add_worksheet('Firefox Cache2 Index Time')
        worksheet1.freeze_panes(1, 0)
        worksheet2 = workbook.add_worksheet('Firefox Cache2 Index Timestamps')
        worksheet2.freeze_panes(1, 0)
        columnNames = ['Hash', 'Frecency', 'Expires', 'AppID', 'Flags', 'Size']
        columnWidth = [40, 15, 20, 15, 10, 10]
        columns = ['A', 'B', 'C', 'D', 'E', 'F']
        for i in range(len(columnNames)):
            worksheet1.write(0, i, columnNames[i], bold)
            worksheet1.set_column(columns[i] + ':' + columns[i], columnWidth[i])
            worksheet2.write(0, i, columnNames[i], bold)
            worksheet2.set_column(columns[i] + ':' + columns[i], columnWidth[i])
    elif doCsv:
        csvFile = open(args.output, 'w')
        csvWriter = csv.writer(csvFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        csvWriter.writerow(('hash', 'frecency', 'expires', 'appId', 'flags', 'size'))
else:
    verbose = True

while indexFileSize - indexFile.tell() > 36 :
    if verbose:
        print "loc: {0}".format(indexFile.tell()),
    hash = indexFile.read(20)
    frecency = struct.unpack('>i', indexFile.read(4))[0]
    expireTimeInt = struct.unpack('>i', indexFile.read(4))[0]
    appId = struct.unpack('>i', indexFile.read(4))[0]
    flags = struct.unpack('>B', indexFile.read(1))[0]
    fileSize = struct.unpack('>I', '\x00'+indexFile.read(3))[0]
    if hash == 0 :
        break
    try:
        expireTime = datetime.datetime.fromtimestamp(expireTimeInt)
    except:
        expireTime = expireTimeInt
    if verbose:
        print "hash: {0}h".format(hash.encode('hex')),
        print "frec: {0}".format(hex(frecency)),
        print "expr: {0}".format(expireTime),
        print "apid: {0}".format(hex(appId)),
        print "flgs: {0}".format(hex(flags)),
        print "size: {0}".format(fileSize)

    if doXlsx:
        vals1 = [format(hash.encode('hex')), hex(frecency), format(expireTime), format(hex(appId)), format(hex(flags)), fileSize]
        vals2 = [format(hash.encode('hex')), hex(frecency), expireTimeInt, format(hex(appId)), format(hex(flags)), fileSize]
        for col in range(len(vals1)):
            worksheet1.write(count+1, col, vals1[col])
            worksheet2.write(count+1, col, vals2[col])

    if doCsv :
        csvWriter.writerow((hash.encode('hex'),
                            hex(frecency),
                            expireTime,
                            hex(appId),
                            hex(flags),
                            fileSize))

    count += 1
print "\nrecord count: {0}".format(count)
if doXlsx:
    try:
        workbook.close()
        print('Data written to XLSX file ' + args.output)
        saved = True
    except:
        print('Could not save XLSX file ' + args.output)
elif doCsv :
    try:
        csvFile.close()
        print 'Data written to CSV file: {0}'.format(csvFile.name)
        saved = True
    except:
        print('Could not save CSV file ' + args.output)

if saved:
    os.startfile(args.output)
