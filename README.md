# awr-triage-system

from awr.chroma import ChromaDB
db = ChromaDB()
db.init_populate()
file = "./data/docx/CHAMP-2024-0247.docx"
json_data = extract_awr_sections(file)
text_data = json.dumps(json_data)
v_awr = query_awr(text_data)
for awr in v_awr:
    print(awr)

### Demo script
Load dummy data to Jira Board
```
$ python demo_rest.py --mode load-dummy --xml-path data/xml/AWRData_List.xml
```

