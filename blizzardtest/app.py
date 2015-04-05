#!flask/bin/python
'''
INFO

This API was written in Python with Flask and sqlite. I chose Python mostly for
familiarity. I've been using it a lot for personal and group projects. I haven't 
had any experience working on RESTful HTTP APIs, but I had a (geniunely) fun week 
looking up guides and examples to get this working. I think I've definitely
learned a lot trying something new. Flask was used as a result of following a 
certain guide, and sqlite was used due to my familiarity with SQL and the ease
of setup.

A little bit about this API, for each resource, I have (extra) links exposing HTTP
methods for that resource. Calling GET for a resource will give some information
about where to go next.

Deletion works by sending DELETE to an active account or character. The resource's
status is then marked as 'Deleted'. It can then be accessed via 
/blizzardtest/api/account/deleted/<account_name> or 
/blizzardtest/api/account/<account_name>/characters/deleted/<character_name>. 
From this deleted directory, issuing PUT will restore the deleted resource back to 
the 'Active' status. Issuing DELETE from the deleted directory will permenantly 
remove it from the database.

For errors, I return a general error code 400. This is a catch all for everything
from bad inputs to non-existent resources.
'''

from flask import Flask, jsonify, request, abort, send_file
import sqlite3

db = sqlite3.connect('Accounts.db')
c = db.cursor()

app = Flask(__name__)

@app.route('/blizzardtest/api', methods=['GET'])
def get_base():
    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/about',
              'rel' : 'about',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account',
              'rel' : 'list',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/app.py',
              'rel' : 'source',
              'method' : 'GET'}]
    
    return jsonify({'links' : links})

@app.route('/blizzardtest/api/app.py', methods=['GET'])
def get_source():
    return send_file('app.py')

@app.route('/blizzardtest/api/about', methods=['GET'])
def get_about():
    # Source is located in http://maxrchung.com/blizzardtest/api/app.py
    info = {'author' : 'Max Robert Chung', 'source' : '/../app.py'}
    return jsonify(info)

@app.route('/blizzardtest/api/account', methods=['GET'])
def get_accounts():
    # Retrieve all active accounts
    c.execute('SELECT * FROM Account WHERE Account.Status = "Active";')
    data = c.fetchall()
    
    accounts = []

    # Loops through all the current accounts and prints out their info
    for index in range(len(data)):
        block = {
            'account_id' : data[index][1],
            'account_name' : data[index][0],
            'links' : [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+data[index][0],
                        'rel' : 'self',
                        'method' : 'GET'},
                       {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+data[index][0],
                        'rel' : 'delete',
                        'method' : 'DELETE'}]
        }
        accounts.append(block)

    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account',
              'rel' : 'create',
              'method' : 'POST'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/deleted',
              'rel' : 'list',
              'method' : 'GET'}]

    info = {'accounts' : accounts, 'links' : links}

    return jsonify(info)

@app.route('/blizzardtest/api/account/<name>', methods=['GET'])
def get_account(name):
    # Verify that the account is active and exists
    c.execute('SELECT * FROM Account WHERE Account.Status = "Active" and Account.Name = ?', (name,))
    # If not, then abort
    if not c.fetchone():
        abort(400)

    # Displays some basic instructions for what to do with the account:
    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name,
              'rel' : 'delete',
              'method' : 'DELETE'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters',
              'rel' : 'list',
              'method' : 'GET'}]
    
    return jsonify({'links' : links})

@app.route('/blizzardtest/api/account', methods=['POST'])
def create_account():
    # Abort if bad input from POST
    if not request.json or not 'name' in request.json:
        abort(400)
    
    name = request.json['name']

    # We check for both active and deleted accounts so we can guarantee
    # uniqueness
    c.execute('SELECT * FROM Account WHERE Account.Name = ?;', (name,))
    # Abort if name already exists
    if c.fetchone():
        abort(400)

    # To find the account ID to add, we find the current max ID
    # from the Account table and add 1. This ensures a unique,
    # nondecreasing ID
    c.execute('SELECT MAX(ID) FROM Account;')

    # If Account is currently empty, start the id as 1, otherwise
    # add 1
    account_id = 1
    data = c.fetchone()[0]
    if data:
        # We need to cast the result, or else the execute statement
        # below will not register account_id as an actual int
        account_id = int(data) + 1

    c.execute('INSERT INTO Account VALUES (?,?,?);',(name, account_id, 'Active',))
    db.commit()

    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account',
              'rel' : 'self',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name,
              'rel' : 'self',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name,
              'rel' : 'delete',
              'method' : 'DELETE'}]
    info = {'account_id' : account_id, 'links' : links}

    return jsonify(info)

@app.route('/blizzardtest/api/account/<name>', methods=['DELETE'])
def delete_account(name):
    # Delete only active accounts
    c.execute('SELECT * FROM Account WHERE Account.Name = ? and Account.Status = "Active";', (name,))
    data = c.fetchone()

    # Abort if there is no active account with the given name
    if not data:
        abort(400)

    # Set the account's status to 'Deleted'
    c.execute('UPDATE Account SET Status = "Deleted" WHERE Account.Name = ?;', (name,))
    db.commit()

    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/deleted/'+name,
              'rel' : 'self',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/deleted/'+name,
              'rel' : 'restore',
              'method' : 'POST'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/deleted/'+name,
              'rel' : 'delete',
              'method' : 'DELETE'}]

    info = {'links' : links}

    # Return info about the account at the new location
    return jsonify(info)

@app.route('/blizzardtest/api/account/deleted', methods=['GET'])
def get_deleted_accounts():
    # Retrive all deleted accounts
    c.execute('SELECT * FROM Account WHERE Account.Status = "Deleted";')
    data = c.fetchall()
    
    accounts = []

    for index in range(len(data)):
        block = {
            'account_id' : data[index][1],
            'account_name' : data[index][0],
            'links' : [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/deleted/'+data[index][0],
                        'rel' : 'self',
                        'method' : 'GET'},
                       {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/deleted/'+data[index][0],
                        'rel' : 'restore',
                        'method' : 'PUT'},
                       {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/deleted/'+data[index][0],
                        'rel' : 'delete',
                        'method' : 'DELETE'}]
        }
        accounts.append(block)

    info = {'deleted_accounts' : accounts}

    return jsonify(info)

@app.route('/blizzardtest/api/account/deleted/<name>', methods=['GET'])
def get_deleted_account(name):
    # Verify that the account actually exists
    c.execute('SELECT * FROM Account WHERE Account.Status = "Deleted" and Account.Name = ?;', (name,))
    data = c.fetchone()
    # And if not, then abort
    if not data:
        abort(400)
    
    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/deleted/'+name,
              'rel' : 'restore',
              'method' : 'PUT'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/deleted/'+name,
              'rel' : 'delete',
              'method' : 'DELETE'}]

    return jsonify({'links' : links})

@app.route('/blizzardtest/api/account/deleted/<name>', methods=['DELETE'])
def kill_deleted_account(name):
    # Verify that the account actually exists in the table
    c.execute('SELECT ID FROM Account WHERE Account.Status = "Deleted" and Account.Name = ?;',(name,))
    data = c.fetchone()
    # If not, abort
    if not data:
        abort(400)

    account_id = data[0]

    # We have to make sure to delete all the characters from the account
    # otherwise there's no way to access these characters after
    c.execute('DELETE FROM Character WHERE Character.Account = ?', (account_id,))
    # Deletes the account
    c.execute('DELETE FROM Account WHERE Account.Name = ?;',(name,))
    db.commit()

    # Don't return anything because account is deleted
    return ''

@app.route('/blizzardtest/api/account/deleted/<name>', methods=['PUT'])
def restore_deleted_account(name):
    # Verify that the account exists
    c.execute('SELECT * FROM Account WHERE Account.Status = "Deleted" and Account.Name = ?;',(name,))
    # If not, abort
    if not c.fetchone():
        abort(400)

    # Set account status to active
    c.execute('UPDATE Account SET Status="Active" WHERE Name=?;',(name,))
    db.commit()

    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name,
              'rel' : 'self',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name,
              'rel' : 'delete',
              'method' : 'DELETE'}]

    info = {'links' : links}

    # Return link information about the restored account
    return jsonify(info)

@app.route('/blizzardtest/api/account/<name>/characters', methods=['GET'])
def get_characters(name):
    # Verify that the account exists
    c.execute('SELECT ID FROM Account WHERE Account.Name = ? and Account.Status = "Active";', (name,))
    data = c.fetchone()
    if not data:
        abort(400)

    account_id = data[0]

    # Finds active characters of the given active account
    c.execute('SELECT * FROM Character CROSS INNER JOIN Account WHERE Account.ID = Character.Account and Character.Status = "Active" and Account.Status = "Active" and Account.Name = ?;', (name,))

    data = c.fetchall()

    characters = []

    # Loops through all the current accounts and prints out their info
    for index in range(len(data)):
        block = {
            'character_id' : data[index][6],
            'name' : data[index][1],
            'race' : data[index][2],
            'class' : data[index][3],
            'faction' : data[index][4],
            'level' : data[index][5],
            'links' : [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/' + data[index][1],
                        'rel' : 'self',
                        'method' : 'GET'},
                       {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/' + data[index][1],
                        'rel' : 'delete',
                        'method' : 'DELETE'}]
        }
        characters.append(block)

    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters',
              'rel' : 'create',
              'method' : 'POST'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/deleted',
              'rel' : 'list',
              'method' : 'GET'}]

    info = {'account_id' : account_id, 'characters' : characters, 'links' : links}

    return jsonify(info)

@app.route('/blizzardtest/api/account/<name>/characters/<char_name>', methods=['GET'])
def get_character(name, char_name):
    # Verify that the character exists
    c.execute('SELECT * FROM Character CROSS INNER JOIN Account WHERE Character.Status = "Active" and Account.Status = "Active" and Character.Name = ? and Account.ID = Character.Account and Account.Name = ?;', (char_name, name))
    if not c.fetchone():
        abort(400)

    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/'+char_name,
              'rel' : 'delete',
              'method' : 'DELETE'}]

    return jsonify({'links' : links})

@app.route('/blizzardtest/api/account/<name>/characters', methods=['POST'])
def create_character(name):
    # Abort if missing input from POST
    if not request.json or not 'name' in request.json or not 'race' in request.json or not 'class' in request.json or not 'faction' in request.json or not 'level' in request.json:
        abort(400)

    # Level check
    try:
        level = int(request.json['level'])
        if level < 1 or level > 85:
            abort(400)
    except ValueError:
        abort(400)

    # Race check
    race = request.json['race']
    if race != 'Orc' and race != 'Tauren' and race != 'Blood Elf' and race != 'Human' and race != 'Gnome' and race != 'Worgen':
        abort(400)

    # Class check
    class_ = request.json['class']
    if class_ != 'Warrior' and class_ != 'Druid' and class_ != 'Death Knight' and class_ != 'Mage':
        abort(400)

    # Faction check
    faction = request.json['faction']
    if faction != 'Horde' and faction != 'Alliance':
        abort(400)

    # Rules:
    # Orc, Tauren, Blood Elf races are exclusively Horde
    if race == 'Orc' or race == 'Tauren' or race == 'Blood Elf':
        if faction != 'Horde':
            abort(400)

    # Human, Gnome, and Worgen races are exclusively Alliance
    if race == 'Human' or race == 'Gnome' or race == 'Worgen':
        if faction != 'Alliance':
            abort(400)

    # Only Taurens and Worgen can be Druids
    if class_ == 'Druid':
        if race != 'Tauren' and race != 'Worgen':
            abort(400)

    # Blood Elves cannot be Warriors
    if race == 'Blood Elf' and class_ == 'Warrior':
        abort(400)

    # Check to make sure account exists and is active
    # Also set the account_id for future use
    c.execute('SELECT ID FROM Account WHERE Account.Name = ? and Account.Status = "Active";', (name,))
    data = c.fetchone()
    if not data:
        abort(400)
    account_id = data[0]

    # A player can only have all Horde or all Alliance active characters
    # Find the faction of the account
    c.execute('SELECT Faction FROM Character CROSS INNER JOIN Account WHERE Account.ID = Character.Account and Account.Name = ?;', (name,))
    data = c.fetchone()
    if data:
        # Compare with the new character's faction
        if data[0] != faction:
            abort(400)

    # Set the ID number by finding the current max ID and adding 1
    c.execute('SELECT MAX(ID) FROM Character;')
    data = c.fetchone()[0]
    char_id = 1
    if data:
        char_id = int(data) + 1

    print('6')

    # Checks that the character name is unique
    charname = request.json['name']
    c.execute('SELECT Name FROM Character WHERE Character.Name = ?;', (charname,))
    data = c.fetchone()
    # Abort if the name already exists
    if data:
        abort(400)


    # Applies changes to database
    values = (account_id, charname, race, class_, faction, level, char_id, 'Active',)
    c.execute('INSERT INTO Character VALUES (?,?,?,?,?,?,?,?);',values)
    db.commit()

    print('7')

    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters',
              'rel' : 'list',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/'+charname,
              'rel' : 'self',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/'+charname,
              'rel' : 'delete',
              'method' : 'DELETE'}]

    info = {'character_id' : char_id, 'links' : links}

    return jsonify(info)

@app.route('/blizzardtest/api/account/<name>/characters/<char_name>', methods=['DELETE'])
def delete_character(name, char_name):
    # Verify active character belongs to an active account
    c.execute('SELECT * FROM Character CROSS INNER JOIN Account WHERE Character.Status = "Active" and Account.Status = "Active" and Character.Account = Account.ID and Account.Name = ? and Character.Name = ?;', (name,char_name))
    # Abort if there is no active account with the given character
    if not c.fetchone():
        abort(400)

    # Set the character's status to 'Deleted'
    c.execute('UPDATE Character SET Status = "Deleted" WHERE Character.Name = ?;', (char_name,))
    db.commit()

    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/deleted/'+char_name,
              'rel' : 'self',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/deleted/'+char_name,
              'rel' : 'restore',
              'method' : 'POST'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/deleted/'+char_name,
              'rel' : 'delete',
              'method' : 'DELETE'}]

    info = {'links' : links}
    # Return info about the character at the deleted location
    return jsonify(info)

@app.route('/blizzardtest/api/account/<name>/characters/deleted', methods=['GET'])
def get_deleted_characters(name):
    # Verify that the account exists
    # The account can be either deleted or active
    c.execute('SELECT ID FROM Account WHERE Account.Name = ?;', (name,))
    data = c.fetchone()
    if not data:
        abort(400)

    account_id = data[0]

    # Retrieve all deleted characters
    c.execute('SELECT * FROM Character CROSS INNER JOIN Account WHERE Character.Status = "Deleted" and Character.Account = Account.ID and Account.Name = ?;',(name,))
    data = c.fetchall()

    characters = []

    for index in range(len(data)):
        block = {
            'character_id' : data[index][6],
            'name' : data[index][1],
            'race' : data[index][2],
            'class' : data[index][3],
            'faction' : data[index][4],
            'level' : data[index][5],
            'links' : [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/deleted/' + data[index][1],
                        'rel' : 'self',
                        'method' : 'GET'},
                       {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/deleted/' + data[index][1],
                        'rel' : 'restore',
                        'method' : 'PUT'},
                       {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/deleted/' + data[index][1],
                        'rel' : 'delete',
                        'method' : 'DELETE'}]
        }
        characters.append(block)

    info = {'account_id' : account_id, 'deleted_characters' : characters}

    return jsonify(info)

@app.route('/blizzardtest/api/account/<name>/characters/deleted/<char_name>', methods=['GET'])
def get_deleted_character(name,char_name):
    # Find the specific deleted character from an active or deleted account
    c.execute('SELECT * FROM Character CROSS INNER JOIN Account WHERE Character.Status = "Deleted" and Character.Account = Account.ID and Account.Name = ? and Character.Name = ?;', (name, char_name,))
    # If character does not exist, then abort
    if not c.fetchone():
        abort(400)
    
    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/deleted/' + char_name,
              'rel' : 'restore',
              'method' : 'PUT'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/deleted/' + char_name,
              'rel' : 'delete',
              'method' : 'DELETE'}]

    return jsonify({'links' : links})

@app.route('/blizzardtest/api/account/<name>/characters/deleted/<char_name>', methods=['DELETE'])
def kill_deleted_character(name, char_name):
    # Verify that the character exists on the given account
    c.execute('SELECT * FROM Character CROSS INNER JOIN Account WHERE Character.Status = "Deleted" and Character.Name = ? and Account.ID = Character.Account and Account.Name = ?;', (char_name,name))
    if not c.fetchone():
        abort(400)

    c.execute('DELETE FROM Character WHERE Name = ?', (char_name,))
    db.commit()

    # Don't return anything because the character is now deleted
    return ''

@app.route('/blizzardtest/api/account/<name>/characters/deleted/<char_name>', methods=['PUT'])
def restore_deleted_character(name, char_name):
    # Verify that the character exists
    c.execute('SELECT * FROM Character CROSS INNER JOIN Account WHERE Character.Status = "Deleted" and Character.Name = ? and Account.ID = Character.Account and Account.Name = ?;', (char_name,name))
    if not c.fetchone():
        abort(400)

    c.execute('UPDATE Character SET Status = "Active" WHERE Name = ?;',(char_name,))
    db.commit()

    links = [{'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/'+char_name,
              'rel' : 'self',
              'method' : 'GET'},
             {'href' : 'http://maxrchung.com:5000/blizzardtest/api/account/'+name+'/characters/'+char_name,
              'rel' : 'delete',
              'method' : 'DELETE'}]
    
    info = {'links' : links}

    # Return link information about the restored character
    return jsonify(info)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
