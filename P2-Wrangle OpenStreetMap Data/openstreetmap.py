
# coding: utf-8

# In[2]:

import os
import xml.etree.cElementTree as ET
from collections import defaultdict
import collections
import pprint
import re
import codecs
import csv
import cerberus
import copy
import schema
import sys



# In[48]:

import xml.etree.ElementTree as ET

OSM_FILE = "toronto.osm"
SAMPLE_FILE = "sample.osm"




# ## Generate sample data

# In[4]:

k = 50 # Parameter: take every k-th top level element
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag
    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

with open(SAMPLE_FILE, 'wb') as output:
    a = '<?xml version="1.0" encoding="UTF-8"?>\n'
    b = bytearray(a, encoding='utf-8')
    
    b.extend('<osm>\n  '.encode())
    output.write(b)

    # Write every kth top level element
    
    for i, element in enumerate(get_element(OSM_FILE)):

        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))
    a = '</osm>'
    b = bytearray(a,encoding = 'utf-8')
    output.write(b)


# ## Count the number of tags in the dataset

# In[3]:

def count_tags(filename):
    counts_tag = defaultdict(int)
    for event, element in ET.iterparse(filename):
        counts_tag[element.tag] += 1
    return counts_tag


# In[4]:

tags = count_tags(SAMPLE_FILE)
pprint.pprint(tags)


# ## Check the k value for each tag

# In[5]:

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    if element.tag == "tag":
        if lower.match(element.attrib['k']):
            keys['lower'] += 1
        elif lower_colon.match(element.attrib['k']):
            keys['lower_colon'] += 1
        elif problemchars.match(element.attrib['k']):
            keys['problemchars'] += 1
        else:
            keys['other'] += 1
            
        
    return keys



def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys


# In[6]:

keys = process_map(SAMPLE_FILE)
pprint.pprint(keys)


# In[7]:

def process_map(filename):
    users = set()
    for _, element in ET.iterparse(filename):
   
        if 'user' in element.attrib:
            users.add(element.attrib['user'])
            

    return users


# In[8]:

users = process_map('sample.osm')
pprint.pprint(len(users))


# ## Audit the street types

# In[9]:

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons","Circle", "Crescent", "Gate", "Terrace", "Grove", "Way"]
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:    
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile,  encoding="utf-8")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


st_types = audit(SAMPLE_FILE)
pprint.pprint(dict(st_types))



# In[10]:

mapping = {"Ave":  "Avenue",
            "Rd":  "Road",
            "E" : "East",
           "Lane," : "Lane"
          }            
   


# In[11]:

def update_name(name, mapping):

    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if m not in expected:
            if m.group() in mapping.keys():
                name = re.sub(m.group(), mapping[m.group()], name)
    
    return name


# In[16]:

for st_type, ways in st_types.items():
    for name in ways:
        better_name = update_name(name, mapping)
        print (name, "=>", better_name)


# ## Process the openstreetmap XML file and update province

# In[17]:


def process_tag(tag, element):
    new_tag = {}
    new_tag["id"] = int(element.attrib["id"])
    if tag.attrib["k"] == "addr:street":
        new_tag["value"] = update_name(tag.attrib["v"], mapping)
    
    elif tag.attrib["k"] == "addr:province":
        if tag.attrib["v"] == "Ontario":
            new_tag["value"] = "ON"
        else:
            new_tag["value"] = tag.attrib["v"]
    else:
        #if tag.attrib["v"] is not None:
        new_tag["value"] = tag.attrib["v"]
                
            
        
    if LOWER_COLON.search(tag.attrib["k"]):
        colon = tag.attrib["k"].index(":")
        new_tag["type"] = tag.attrib["k"][:colon]
        new_tag["key"] = tag.attrib["k"][colon+1:]
        
        
    else:
        new_tag["type"] = "regular"
        new_tag["key"] = tag.attrib["k"]
        
            
    return new_tag


# In[40]:

OSM_PATH = "sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
#PHONE_NUM = re.compile(r'\d{3}\d{3}\d{4}')
SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


 

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []
    
  

    if element.tag == 'node':
        for node in NODE_FIELDS:
            node_attribs[node] = element.attrib[node]
        node_attribs["id"] = int(element.attrib["id"])
        node_attribs["lat"] = float(element.attrib["lat"])
        node_attribs["lon"] = float(element.attrib["lon"])
        node_attribs["uid"] = int(element.attrib["uid"])
        node_attribs["changeset"] = int(element.attrib["changeset"])
        
        for tag in element.iter("tag"):
            if PROBLEMCHARS.search(tag.attrib["k"]) is not None:
                continue
            else:
                tag_set = process_tag(tag, element)
                if tag_set:
                    tags.append(tag_set)
                
        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':
        for node in WAY_FIELDS:
            way_attribs[node] = element.attrib[node]
        way_attribs["id"] = int(element.attrib["id"])
        way_attribs["uid"] = int(element.attrib["uid"])
        way_attribs["changeset"] = int(element.attrib["changeset"])
        for tag in element.iter("tag"):
            if PROBLEMCHARS.search(tag.attrib["k"]) is not None:
                continue
            else:
                tag_set = process_tag(tag, element)
                if tag_set:
                    tags.append(tag_set)
            
          
        count = 0
        for node in element.iter("nd"):
            nodes = {}
            nodes["id"] = int(element.attrib["id"])
            nodes["node_id"] = int(node.attrib["ref"])
            nodes["position"] = count
            count = count+1
            way_nodes.append(nodes)
    
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}



# In[42]:

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(iter(validator.errors.items()))
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, str) else v) for k, v in iter(row.items())
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file,         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,         codecs.open(WAYS_PATH, 'w') as ways_file,         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)


# ## SQL and database

# Basic information on file size

# In[5]:

path1 = "C:\\Users\\Sally\\Anaconda3\\Data-Analyst-P3\\toronto.osm"
path2 = "C:\\Users\\Sally\\Anaconda3\\Data-Analyst-P3\\sample.osm"
path3 = "C:\\Users\\Sally\\Anaconda3\\Data-Analyst-P3\\nodes.csv"
path4 = "C:\\Users\\Sally\\Anaconda3\\Data-Analyst-P3\\nodes_tags.csv"
path5 = "C:\\Users\\Sally\\Anaconda3\\Data-Analyst-P3\\ways.csv"
path6 = "C:\\Users\\Sally\\Anaconda3\\Data-Analyst-P3\\ways_nodes.csv"
path7 = "C:\\Users\\Sally\\Anaconda3\\Data-Analyst-P3\\ways_tags.csv"
path8 = "C:\\sqlite\\toronto.db"

toronto = os.path.getsize(path1)/1e6
sample = os.path.getsize(path2)/1e6
nodes = os.path.getsize(path3)/1e6
nodes_tags = os.path.getsize(path4)/1e6
ways = os.path.getsize(path5)/1e6
ways_nodes = os.path.getsize(path6)/1e6
ways_tags = os.path.getsize(path7)/1e6
database = os.path.getsize(path8)/1e6

print("The toronto.osm file size is {} MB".format(toronto))
print("The sample.osm file size is {} MB".format(sample))
print("The nodes.csv file size is {} MB".format(nodes))

print("The nodes_tags.csv file size is {} MB".format(nodes_tags))
print("The ways.csv file size is {} MB".format(ways))
print("The ways_nodes.csv file size is {} MB".format(ways_nodes))
print("The ways_tags.csv file size is {} MB".format(ways_tags))
print("The toronto.db file size is {} MB".format(database))


# Number of Nodes
sqlite> SELECT COUNT(*)
   ...> FROM Nodes;
38630
# Number of Ways
sqlite> SELECT COUNT(*)
   ...> FROM way;
6639
# Number of unique users
sqlite> SELECT COUNT(user.uid)
   ...> FROM (SELECT uid FROM Nodes UNION SELECT uid FROM way) user;
630
# Top 10 contributing users
sqlite> SELECT user.user as User, COUNT(*) as User_Count
   ...> FROM (SELECT user FROM Nodes UNION ALL SELECT user FROM way) user
   ...> GROUP BY User
   ...> ORDER BY User_Count DESC
   ...> LIMIT 10;
"b'andrewpmk'",27253
"b'Kevo'",3285
"b'Matthew Darwin'",2767
"b'Victor Bielawski'",2001
"b'Bootprint'",1167
"b'Mojgan Jadidi'",790
"b'andrewpmk_imports'",526
"b'MikeyCarter'",475
"b'TristanA'",463
"b'Nate_Wessel'",427
# Number of users appearing only once
sqlite> SELECT COUNT(*)
   ...> FROM (SELECT user.user AS User, COUNT(*) AS User_Count FROM
   ...> (SELECT user FROM Nodes UNION ALL SELECT user FROM way) user GROUP BY User
   ...> HAVING COUNT(*) = 1);
274
# Top ten popular amenities
sqlite> SELECT COUNT(*), value
   ...> FROM Node_tags
   ...> WHERE key = "b'amenity'"
   ...> GROUP BY value
   ...> ORDER BY COUNT(*) DESC
   ...> LIMIT 10;
135|b'fast_food'
111|b'bench'
111|b'restaurant'
72|b'post_box'
69|b'parking'
51|b'bank'
48|b'cafe'
39|b'pharmacy'
39|b'waste_basket'
39|b'waste_basket;recycling'
# Top 10 popular cuisines
sqlite> SELECT Node_tags.value, COUNT(*)
   ...> FROM Node_tags
   ...> JOIN (SELECT DISTINCT(id) FROM Node_tags WHERE value = "b'restaurant'") i
   ...> ON Node_tags.id = i.id
   ...> WHERE Node_tags.key = "b'cuisine'"
   ...> GROUP BY Node_tags.value
   ...> ORDER BY COUNT(*) DESC
   ...> LIMIT 10;
b'chinese'|9
b'indian'|6
b'pizza'|6
b'brazilian'|3
b'greek'|3
b'italian'|3
b'mexican'|3
b'sushi'|3
# Number of Tim Hortons
sqlite> SELECT COUNT(*)
   ...> FROM Node_tags
   ...> WHERE value LIKE "%Tim Hortons%";
24
# Number of Starbucks
sqlite> SELECT COUNT(*)
   ...> FROM Node_tags
   ...> WHERE value LIKE "%Starbucks%";
18
# Top 10 popular bank
sqlite> SELECT Node_tags.value, COUNT(*)
   ...> FROM Node_tags
   ...> JOIN (SELECT DISTINCT (id) FROM Node_tags WHERE value = "b'bank'") i
   ...> ON Node_tags.id = i.id
   ...> WHERE Node_tags.key = "b'name'"
   ...> GROUP BY Node_tags.value
   ...> ORDER BY COUNT(*) DESC
   ...> LIMIT 10;
b'TD Canada Trust'|15
b'RBC Royal Bank'|6
b'RBC'|6
b'Scotiabank'|6
b'CIBC'|3
b'Callian Capital'|3
b'CityCan Mortgage Services'|3
b'RBC Financial Group'|3
b'Shinhan Bank'|3
b'Tangerine'|3