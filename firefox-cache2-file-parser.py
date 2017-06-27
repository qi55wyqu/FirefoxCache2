import argparse
import os
import struct
import datetime
import hashlib
import csv
from xlsxwriter import Workbook

argParser = argparse.ArgumentParser(description='Parse Firefox cache2 files in a directory or individually.')
argParser.add_argument('-f', '--file', help='single cache2 file to parse')
argParser.add_argument('-d', '--directory', help='directory with cache2 files to parse')
argParser.add_argument('-o', '--output', help='CSV or XLSX output file')
argParser.add_argument('-v', '--verbose', help='Print cache while parsing')
args = argParser.parse_args()

chunkSize = 256 * 1024

script_dir = os.path.dirname(__file__)

def ParseCacheFile (parseFile):
    if verbose:
        print "parsing file: {0}".format(parseFile.name)
    fileSize = os.path.getsize(parseFile.name)
    parseFile.seek(-4, os.SEEK_END)
    metaStart = struct.unpack('>I', parseFile.read(4))[0]
    numHashChunks = metaStart / chunkSize
    if metaStart % chunkSize :
        numHashChunks += 1
    parseFile.seek(metaStart + 4 + numHashChunks * 2, os.SEEK_SET)
    version = struct.unpack('>I', parseFile.read(4))[0]
    #if version > 1 :
        # TODO quit with error
    fetchCount = struct.unpack('>I', parseFile.read(4))[0]
    lastFetchInt = struct.unpack('>I', parseFile.read(4))[0]
    lastModInt = struct.unpack('>I', parseFile.read(4))[0]
    frecency = struct.unpack('>I', parseFile.read(4))[0]
    expireInt = struct.unpack('>I', parseFile.read(4))[0]
    keySize = struct.unpack('>I', parseFile.read(4))[0]
    flags = struct.unpack('>I', parseFile.read(4))[0] if version >= 2 else 0
    key = parseFile.read(keySize)
    key_hash = hashlib.sha1(key).hexdigest().upper()

    if doCsv :
        csvWriter.writerow((fetchCount,
                            datetime.datetime.fromtimestamp(lastFetchInt),
                            datetime.datetime.fromtimestamp(lastModInt),
                            hex(frecency),
                            datetime.datetime.fromtimestamp(expireInt),
                            flags,
                            key,
                            key_hash))

    if doXlsx:
        vals1 = [fetchCount, format(datetime.datetime.fromtimestamp(lastFetchInt)), format(datetime.datetime.fromtimestamp(lastModInt)), format(hex(frecency)), format(datetime.datetime.fromtimestamp(expireInt)), keySize, flags, key, key_hash]
        vals2 = [fetchCount, lastFetchInt, lastModInt, hex(frecency), expireInt, keySize, flags, key, key_hash]
        for col in range(len(vals1)):
            worksheet1.write(row, col, vals1[col])
            worksheet2.write(row, col, vals2[col])

    if verbose:
        print "version: {0}".format(version)
        print "fetchCount: {0}".format(fetchCount)
        print "lastFetch: {0}".format(datetime.datetime.fromtimestamp(lastFetchInt))
        print "lastMod: {0}".format(datetime.datetime.fromtimestamp(lastModInt))
        print "frecency: {0}".format(hex(frecency))
        print "expire: {0}".format(datetime.datetime.fromtimestamp(expireInt))
        print "keySize: {0}".format(keySize)
        print "flags: {0}".format(flags)
        print "key: {0}".format(key)
        print "key sha1: {0}\n".format(key_hash)

if args.verbose:
    verbose = True
else:
    verbose = False
if args.directory or args.file :
    if args.output :
        ext = os.path.splitext(args.output)[-1]
        if ext == '.csv':
            doCsv = True
            doXlsx = False
        elif ext == '.xlsx':
            doCsv = False
            doXlsx = True
        else:
            verbose = True
            doCsv = False
            doXlsx = False
        if doXlsx:
            workbook = Workbook(args.output)
            bold = workbook.add_format({'bold': True})
            worksheet1 = workbook.add_worksheet('Firefox Cache2 Time')
            worksheet1.freeze_panes(1, 0)
            worksheet2 = workbook.add_worksheet('Firefox Cache2 Timestamps')
            worksheet2.freeze_panes(1, 0)
            columnNames = ['Fetch Count', 'Last Fetch', 'Last Modified', 'Frecency', 'Expiration', 'Key size', 'Flags', 'URL', 'Key Hash']
            columnWidth = [10, 20, 20, 15, 20, 10, 5, 40, 30]
            columns = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
            for i in range(len(columnNames)):
                worksheet1.write(0, i, columnNames[i], bold)
                worksheet1.set_column(columns[i] + ':' + columns[i], columnWidth[i])
                worksheet2.write(0, i, columnNames[i], bold)
                worksheet2.set_column(columns[i] + ':' + columns[i], columnWidth[i])

        if doCsv:
            csvFile = open(args.output, 'w')
            csvWriter = csv.writer(csvFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
            csvWriter.writerow(('Fetch Count', 'Last Fetch', 'Last Modified', 'Frecency', 'Expiration', 'Flags', 'URL', 'Key Hash'))
    procPath = args.directory
    fileList = os.listdir(procPath)
    row = 1
    for filePath in fileList :
        file = open(os.path.join(procPath, filePath), 'r')
        try:
            ParseCacheFile(file)
            row += 1
        except:
            print('Could not parse file ' + filePath)

    if doCsv :
        print 'Data written to CSV file: {0}'.format(csvFile.name)
        csvFile.close()
    if doXlsx:
        workbook.close()
    os.startfile(args.output)
else :
    argParser.print_help()
