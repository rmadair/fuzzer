''' List of all mutations. If you want to add/remove mutations, do it here! '''

# globals
MAX8  = 0xff
MAX16 = 0xffff
MAX32 = 0xffffffff

# Format :
# - 'value' and 'size' are self explanatory
# - 'type' is either 'replace' or 'insert'
#   - replace: overwrite the bytes at a specific offset with the new bytes
#     - aka: AAAAAAAAAA -> AAAABBBBAA
#   - insert: insert the bytes at a specific offset with the new bytes, shifting the rest of the bytes down
#     - aka: AAAAAAAAAA -> AAAABBBBAAAAAA
values_8bit  = [{'value':0x00,       'type':'replace', 'size':1}, {'value':0x01,    'type':'replace', 'size':1}, {'value':MAX8/2-16,  'type':'replace', 'size':1}, 
                {'value':MAX8/2-1,   'type':'replace', 'size':1}, {'value':MAX8/2,  'type':'replace', 'size':1}, {'value':MAX8/2+1,   'type':'replace', 'size':1}, 
                {'value':MAX8/2+16,  'type':'replace', 'size':1}, {'value':MAX8-1,  'type':'replace', 'size':1}, {'value':MAX8,       'type':'replace', 'size':1} ]

values_16bit  = [{'value':0x00,      'type':'replace', 'size':2}, {'value':0x01,    'type':'replace', 'size':2}, {'value':MAX16/2-16, 'type':'replace', 'size':2}, 
                {'value':MAX16/2-1,  'type':'replace', 'size':2}, {'value':MAX16/2, 'type':'replace', 'size':2}, {'value':MAX16/2+1,  'type':'replace', 'size':2}, 
                {'value':MAX16/2+16, 'type':'replace', 'size':2}, {'value':MAX16-1, 'type':'replace', 'size':2}, {'value':MAX16,      'type':'replace', 'size':2} ]

values_32bit  = [{'value':0x00,       'type':'replace', 'size':4}, {'value':0x01,    'type':'replace', 'size':4}, {'value':MAX32/2-16, 'type':'replace', 'size':4}, 
                {'value':MAX32/2-1,  'type':'replace', 'size':4}, {'value':MAX32/2, 'type':'replace', 'size':4}, {'value':MAX32/2+1,  'type':'replace', 'size':4}, 
                {'value':MAX32/2+16, 'type':'replace', 'size':4}, {'value':MAX32-1, 'type':'replace', 'size':4}, {'value':MAX32,      'type':'replace', 'size':4} ]

values_strings = [{'value':list("B"*100),  'type':'insert', 'size':100}, \
                  {'value':list("B"*1000), 'type':'insert', 'size':1000}, \
                  {'value':list("B"*10000),'type':'insert', 'size':10000}, \
                  {'value':list("%s"*10),  'type':'insert', 'size':10}, \
                  {'value':list("%s"*100), 'type':'insert', 'size':100}]
