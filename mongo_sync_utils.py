#!/usr/bin/env python

# filename: mongo_sync_utils.py
# summary: mongo synchronization utilities
# author: caosiyang
# date: 2013/09/16

import os
from utils import error

def db_dump(host, port, outdir='mydump', **kwargs):
    """Dump database.
    """
    if not outdir:
        error('invalid dump directory')
        return False
    # oplog mode is only supported on full dumps --oplog
    username = kwargs.get('username')
    password = kwargs.get('password')
    if username and password:
        cmd = 'mongodump --host %s --port %d --out %s --username %s --passport %s' % (host, port, outdir, username, password)
    else:
        cmd = 'mongodump --host %s --port %d --out %s' % (host, port, outdir)
    res, out = run_command(cmd, log=True)
    if not res:
        error('dump database failed: %s' % cmd)
        return False
    return True

def db_restore(host, port, dumpdir='mydump', **kwargs):
    """Restore database.
    """
    if not dumpdir:
        error('invalid dump directory')
        return False
    username = kwargs.get('username')
    password = kwargs.get('password')
    if username and password:
        cmd = 'mongorestore --host %s --port %d --username %s --passport %s %s' % (host, port, username, password, dumpdir)
    else:
        cmd = 'mongorestore --host %s --port %d %s' % (host, port, dumpdir)
    res, out = run_command(, log=True)
    if not res:
        error('restore database failed: %s' % cmd)
        return False
    return True

def coll_import(host, port, db, coll, srcfile):
    """Import collection of database.
    """
    cmd = 'mongoimport --host %s --port %d --db %s --collection %s < %s' % (host, port, db, coll, srcfile)
    print cmd
    res, out = run_command(cmd, log=True)
    if not res:
        error('import %s.%s failed' % (db, coll))
        return False
    return True

def db_import(host, port, db):
    """Import database.
    """
    dbs = []
    if isinstance(db, str):
        dbs.append(db)
    elif isinstance(db, list):
        dbs = db[:]
    else:
        error('unknown db argument')
        return False

    # convert BSON to JSON
    # and import to destination mongo instance
    db_json_files = []
    for dbname in dbs:
        collbsonfiles = os.listdir('mydump/%s' % dbname)
        for filename in collbsonfiles:
            if filename.endswith('.bson') and not filename.startswith('system.'):
                collname = filename.rsplit('.', 1)[0]
                collbsonfile = 'mydump/%s/%s' % (dbname, filename)
                colljsonfile = create_new_file('%s.%s.json' % (dbname, collname))
                if not bson_dump(collbsonfile, colljsonfile):
                    error('bsondump %s %s failed' % (collbsonfile, colljsonfile))
                    return False
                print 'bsondump %s %s done' % (collbsonfile, colljsonfile)

                if not coll_import(host, port, dbname, collname, colljsonfile):
                    error('coll_import %s failed' % colljsonfile)
                    return False

        db_json_files.append(colljsonfile)


    # convert BSON to JSON for oplog
    oplog_srcfile = 'mydump/oplog.bson'
    if os.path.exists(oplog_srcfile) and os.path.isfile(oplog_srcfile) and os.path.getsize(oplog_srcfile) > 0:
        oplog_dstfile = create_new_file('oplog.json')
        if not bson_dump(oplog_srcfile, oplog_dstfile):
            error('bsondump %s %s failed' % (oplog_srcfile, oplog_dstfile))
            return False
        print 'bsondump %s %s done' % (oplog_srcfile, oplog_dstfile)

    return True


def bson_dump(srcfile, dstfile):
    """convert BSON file into JSON file with human-readable formats.
    """
    cmd = 'bsondump --type json %s | grep "^{" > %s' % (srcfile, dstfile)
    res, out = run_command(cmd, log=True)
    if not res:
        error('%s failed' % cmd)
        return False
    return True


def create_new_file(filename):
    """Create a empty file with specified filename.
    """
    if os.path.exists(filename):
        if os.path.isfile(filename):
            os.remove(filename)
        elif os.path.isdir(filename):
            shutil.rmtree(filename)
    return filename