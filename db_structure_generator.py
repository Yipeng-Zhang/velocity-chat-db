import re


test = False # set True for displaying more detials 


class DbStructureGenerator:

    table_data_list = {}
    graph_list = {}
    top_k = 10

    def __init__(self):
        self.tables_and_columns = {}
        self.table_num = 0

    def get_foreign_key(self, line):
        try:
            # line = line.replace(")","").replace("(","").lower()
            pattern1 = r'FOREIGN KEY\s*(.*?)\s*REFERENCES'
            pattern2 = r'REFERENCES\s*(.*?)$'
            source_column = re.findall(pattern1, line, re.IGNORECASE)[0]
            source_column = source_column.replace(")","").replace("(","").replace("'","").replace('"',"")
            source = re.findall(pattern2, line, re.IGNORECASE)[0]
            target_table = source.split("(")[0].strip()
            target_column = source.split("(")[1].split(")")[0].strip()
            if test:
                print("source column",source_column)
                print("target column",target_table,target_column)
            return(source_column,target_table,target_column)
        except Exception as e:
            print("Error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(e)
            print("line:", line)
            return(None, None, None)
    
    def set_db_connector(self, db_connector):
        self.db_connector = db_connector

    
    def is_column_primary_key(self, table_name, column_name):
        # Execute PRAGMA query to get column info
        columns_info = self.db_connector.exe_sql(f"PRAGMA table_info({table_name});")
        # print(columns_info)

        # Check if the specified column is part of the primary key
        for column_info in columns_info:
            _, name, _, _, _, pk = column_info
            # print(name, column_name, pk)
            if name == column_name and pk == 1:
                return True
        return False

    def table_structure_extractor(self, table_schema_sql):
        table_name = ""
        primary_keys = set()
        for sql_line in table_schema_sql:
            columns = []
            foreign_keys = []
            primary_keys_new = []
            if type(sql_line) != str:
                lines = sql_line[0].splitlines()
            else:
                lines = sql_line.splitlines()
            if test:
                print("len(Sql)", len(lines), " ; Sql", lines)

            for line in lines:
                translation_table = str.maketrans("\t'`", "   ")
                line = line.replace('"',"")
                line = line.translate(translation_table).strip()
                if test:
                    print("read line:", line)
                contents = line.split()
                if "create table" in line.lower():
                    self.table_num += 1
                    table_name = contents[2].replace("(","").strip()
                    if test:
                        print("create table:", table_name)
                elif "foreign key" in line.lower():
                    source_column,target_table,target_column = self.get_foreign_key(line)
                    if test:
                        print("add foreign key:", source_column,"|",target_table,"|",target_column )
                    if source_column != None:
                        foreign_keys.append({
                            "source_table": table_name,
                            "source_column": source_column,
                            "target_table": target_table,
                            "target_column": target_column
                        })
                elif "primary" in line.lower():
                    if "primary" in contents[0].lower():
                        #setting primary key
                        pattern = r'\bprimary\s+key\s*\(([^)]+)\)'
                        matches = re.findall(pattern, line, re.IGNORECASE)
                        
                        for match in matches:
                            primary_keys_new.extend([pk.strip() for pk in match.split(',')])
                        if test:
                            print("add primary key1:", primary_keys_new)
                        primary_keys.update(primary_keys_new)
                    else:
                        #create new column
                        for column in contents:
                            if len(column)>=2:
                                columns.append(column)
                                primary_keys.add(column)
                                if test:
                                    print("add primary key2:", column)
                                break
                elif len(contents) >= 2:
                    column_name = contents[0].strip()
                    if column_name in primary_keys:
                        continue
                    columns.append(column_name)
                    if test:
                        print("add column:", column_name)

            if table_name == None:
                continue

            self.tables_and_columns[table_name] = columns 

            # print("Fiding primary key")
            for column in columns:
                # print ("table:", table_name, "column:", column)
                if self.is_column_primary_key(table_name,column):
                    primary_keys.add(table_name + "." + column)
                    # print("Find primary:", column)
                    break

    def get_table_structure(self, table_name):
        if table_name in self.tables_and_columns.keys():
            return self.tables_and_columns[table_name]
        else:
            return None


    
    def extract_table_columns(self, sql):
        # Regular expression pattern to match CREATE TABLE statements
        create_table_pattern = r"CREATE\s+TABLE\s+['\"]?(\w+)['\"]?\s*\((.*?)\);"

        print("sql", sql)

        table_columns = {}

        # Find all CREATE TABLE statements in the SQL
        create_table_matches = re.findall(create_table_pattern, sql, re.IGNORECASE)

        print("len(create_table_matches)", len(create_table_matches))
        print(create_table_matches)

        # Process each CREATE TABLE statement
        for table, columns in create_table_matches:
            # Split the columns by comma
            column_list = columns.split(',')
            column_names = []

            # Process each column to extract the column name
            for column in column_list:
                column_name_match = re.search(r'"?(\w+)"?\s', column)
                if column_name_match:
                    column_names.append(column_name_match.group(1))

            # Add the table and its corresponding column names to the result dictionary
            table_columns[table] = column_names

        return table_columns


    def getNeighbor(self, table, column = None):
        if column == None:
            targetName = table
        else:
            targetName = table + "." + column
        # Get the node labels (entities)
        nodes = list(self.graph.nodes)
        nodeIndex = nodes.index(targetName)
        # Get the neighbors of the target node
        neighbors = [nodes[i] for i, val in enumerate(self.adjArray[nodeIndex]) if val != 0]

        # Print the neighbors
        # print("Neighbors of", targetName, ":", neighbors)
        return neighbors

    
    def get_db_schema(self):
        return self.get_db_schema
