
import os
import argparse
import sqlite3
import pandas as pd
from sqlite3 import Error
from graphviz import Digraph as Di

# the structure of each process in the pipeline
class Node:
    def __init__(self,initdata,pid,parent_id, process_name, level):
        self.id = pid
        self.name = process_name
        self.pid = parent_id
        self.data = initdata
        self.leve = level
        self.next = None
    def getId(self):
        return self.id
    def getPid(self):
        return self.pid
    def getData(self):
        return self.data
    def getNext(self):
        return self.next
    def getName(self):
        return self.name
    def getLevel(self):
        return self.leve
    def setId(self,newid):
        self.data = newid
    def setPid(self,newpid):
        self.data = newpid
    def setData(self,newdata):
        self.data = newdata
    def setNext(self,newnext):
        self.next = newnext
    def setName(self, newname):
        self.name = newname
    def setLevel(self, level):
        self.leve = level

# the functions of the proposed linked list
class LinkedList:

    def __init__(self):
        self.head = None
    def isEmpty(self):
        return self.head == None
    def size(self):
        current = self.head
        count = 0
        while current != None:
            count = count + 1
            current = current.getNext()
        return count
    def printing(self):
        current = self.head
        result = []
        while current != None:
            result.append(current)
            current = current.getNext()
        return result

    def add(self,item,pid,parent_id, process_name,level):
        new_node = Node(item,pid,parent_id, process_name,level)
        new_node.setNext(self.head)
        self.head = new_node

    # Returns a linked list contains all pipeline process/sub-process which has read/write
    # the output pipeline files.
    def reverse(self):
        prev=None
        current = self.head
        while (current is not None):
            next = current.getNext()
            current.setNext(prev)
            prev = current
            current = next
        self.head = prev
        return prev

    # keep the involved processes in the pipeline
    def filter(self):
        prev = None
        current = self.head
        level_id = []
        level = 6
        while (current is not None):
            next = current.getNext()
            if len(current.data) != 0:
                # keep just the files of its process
                data = current.data
                current.data = ()
                for d in data:
                    if d[0]==current.id:
                        current.data += (d,)
                # identifying the root process (as the main pipeline elements)
                if current.pid[0][0] == None:
                    level_id.append([current.id, 0])
                    current.setLevel(0)
                    current.setNext(prev)
                    prev = current
                # here we can expand the final result to more sub-process details instead of first-level
                for line2 in level_id:
                    tmp = current.pid[0]
                    if line2[0] == tmp[0]:
                        if line2[1] < level:
                            level_id.append([current.id, line2[1] + 1])
                            current.setLevel(line2[1] + 1)
                            # current.setName(line2[:-1])
                            current.setNext(prev)
                            prev = current
            current = next
        self.head = prev
        return prev
    
    def append(self,pid,newfiles):
        current = self.head
        found = False
        while current != None and not found:
            if current.id == pid:
                current.data += newfiles
                found = True
            else:
                current = current.getNext()

    def get_data(self,item):
        current = self.head
        found = False
        while current != None and not found:
            if current.id == item:
                return current.data
            else:
                current = current.getNext()

    def remove(self,item):
        current = self.head
        previous = None
        found = False
        while not found:
            if current.getData() == item:
                found = True
            else:
                previous = current
                current = current.getNext()
        if previous == None:
            self.head = current.getNext()
        else:
            previous.setNext(current.getNext())

# idenfitying and classifying the whole processes of the pipeline based on the reprozip trace
def CreateTree(pid, process_node,db_path):

    try:
        db = sqlite3.connect(db_path)
    except Error as e:
        print (e)

    process_cursor = db.cursor()
    openfile_cursor = db.cursor()
    executed_cursor = db.cursor()
    parent_cursor = db.cursor()
    writefile_cursor = db.cursor()

    # select the list of child process of pid
    process_id_query = '''
            SELECT id
            FROM processes
            WHERE parent = %s
            '''
    process_cursor.execute(process_id_query % pid)
    child_list = process_cursor.fetchall()

    # select the process name from executed_file db
    process_name_query = '''
                SELECT name
                FROM executed_files
                WHERE process = %s
                '''
    executed_cursor.execute(process_name_query % pid)
    process_name = executed_cursor.fetchall()

    #select the list of opened files (w/r) of pid
    opened_files_query = '''
            SELECT process, name, mode
            FROM opened_files
            WHERE process = %s AND mode <= 2 
            '''
    openfile_cursor.execute(opened_files_query % pid)
    opened_files_list = openfile_cursor.fetchall()

    #select the list of opened files (just wrote file) of pid
    written_files_query = '''
            SELECT process, name, mode
            FROM opened_files
            WHERE mode == 2 
            '''
    writefile_cursor.execute(written_files_query)
    total_files = writefile_cursor.fetchall()

    topenedf = [] #total opened files from the matrix file
    for file in opened_files_list:
        for line in total_files:
            #dd = str(file[1])
            if line[1] in file[1]:
                topenedf.append(file) if file not in topenedf else None

    #select the parent id of pid from process list
    process_parent_query = '''
                SELECT parent
                FROM processes
                WHERE id = %s
                '''
    parent_cursor.execute(process_parent_query % pid)
    parent_id = parent_cursor.fetchall()

    # create and add data process of pid to linked list
    process_node.add(topenedf, pid, parent_id, process_name, -1)

    # calling again this class recursively for the child of process
    for child in child_list:
        if child[0] != None :
            process_node.append(pid, CreateTree(child[0], process_node,db_path))
    data = process_node.get_data(pid)
    return data

def main():
    parser = argparse.ArgumentParser(description='Classification of the pipeline processes and making its graph')
    parser.add_argument("-db", "--sqliteDB",
                        help="The path to the sqlite file which is created by reprozip trace and includes all pipeline process")
    parser.add_argument("-ofile", "--openedFiles",
                        help="refers to the matrix file of output of the 'repro-tools' script")
    args = parser.parse_args()
    #if not os.path.isfile(args.sqliteDB):
        #log_error("The input file path of sqlite file is not correct")


    graph = Di('Graph', filename='GraphModel', format='dot', strict=False)
    node_label = 0
    proc_list = []
    db_path=args.sqliteDB
    read_matrix_file=args.openedFiles
    # write two output files for processes and files separately
    write_files = open("complete_file.txt", 'w')
    write_proc = open("all_processes", 'w')
    write_total_tmp = ['000']
    write_total_tmp2 = ['000']

    # read the pipeline files :
    with open(read_matrix_file, 'r') as pfiles:
        pipeline_files = pfiles.readlines()

    # read the whole files
    db = sqlite3.connect(db_path)
    writefile_cursor = db.cursor()
    #select the list of opened files (just written files)
    written_files_query = '''
            SELECT process, name, mode
            FROM opened_files
            WHERE mode == 2 
            '''
    writefile_cursor.execute(written_files_query)
    written_files_list = writefile_cursor.fetchall()
    db.close()

    #start the program:
    pipeline_graph = LinkedList()
    # root process_id is one
    CreateTree(1, pipeline_graph,db_path)
    pipeline_graph.reverse()
    pipeline_graph.filter()
    pipeline_graph.reverse()
    total_pipe_proc = pipeline_graph.printing()

    for proc in total_pipe_proc:
        count_diff_w = 0
        count_nodiff_w = 0
        count_tmp_w = 0
        count_diff_r = 0
        count_tmp_r = 0
        count_nodiff_r = 0
        write_diff_list = []
        write_nodiff_list = []
        write_tmp_list = []
        read_diff_list = []
        read_nodiff_list = []
        read_tmp_list = []

        for data in proc.data:
            if data[2] == 2:
                # write_list.append(data[1])
                ttt = False
                for t in write_total_tmp2:
                    if data[1] == t[1]: ttt = True
                if ttt == False: write_total_tmp2.append(data[0:2])
                tmp = False
                for diff in pipeline_files:
                    n = diff.split(" ")
                    if (int(n[1][:-1]) != 0 and n[0] in data[1]):
                        write_diff_list.append(data[0:2])
                        count_diff_w += 1
                        tmp = True
                        break
                    elif (int(n[1][:-1]) == 0 and n[0] in data[1]):
                        write_nodiff_list.append(data[0:2])
                        count_nodiff_w += 1
                        tmp = True
                        break
                if tmp == False:
                    write_tmp_list.append(data[0:2])
                    count_tmp_w += 1
                    tt = False
                    for t in write_total_tmp:
                        if data[1] == t[1]: tt = True
                    if tt == False: write_total_tmp.append(data[0:2])

            elif data[2] == 1:
                #finding the origin process of the read files to show dependencies
                origin_p = []
                for o in written_files_list:
                    if data[1] == o[1]:
                        origin_p = o[0]
                        break

                # read_list.append(data[1])
                tmp = False
                for diff2 in pipeline_files:
                    n = diff2.split(" ")
                    if (int(n[1][:-1]) != 0 and n[0] in data[1]):
                        data = data[:2] + (origin_p,)
                        read_diff_list.append(data)
                        count_diff_r += 1
                        tmp = True
                        break
                    elif (int(n[1][:-1]) == 0 and n[0] in data[1]):
                        data = data[:2] + (origin_p,)
                        read_nodiff_list.append(data)
                        count_nodiff_r += 1
                        tmp = True
                        break
                if tmp == False:
                    data =data[:2] + (origin_p,)
                    read_tmp_list.append(data)
                    count_tmp_r += 1

        # making dot file and representing the graph
        name = "Null"
        if proc.name != []: name = str(proc.name[0][0].split('/')[-1])

        #showing the various process by colored node: create(red), propagate(yellow),
        # remove(blue) and green nodes are process with no differences
        if count_diff_r > 0 and count_diff_w > 0:
            graph.attr('node', style='filled', fillcolor='yellow')
            graph.node(str(proc.id), ''.join(
                [str(node_label), '#', name]),
                       shape='circle')
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1
            graph.attr('edge', style='solid', color='black')
            graph.edge(str(proc.pid[0][0]), str(proc.id))

            #showing the dependencies by dashed edges: diff read(red), tmp read(yellow)
            # and read files without differences(green)
            for e in read_diff_list:
                graph.attr('edge', style='dashed', color='red')
                graph.edge(str(e[2]), str(proc.id))
            for e2 in read_tmp_list:
                graph.attr('edge', style='dashed', color='yellow')
                graph.edge(str(e2[2]), str(proc.id))
            for e2 in read_nodiff_list:
                graph.attr('edge', style='dashed', color='green')
                graph.edge(str(e2[2]), str(proc.id))

        elif count_diff_r == 0 and count_diff_w > 0 and count_tmp_r == 0:
            graph.attr('node', style='filled', fillcolor='red')
            graph.node(str(proc.id), ''.join(
                [str(node_label), '#', name]), shape='circle')
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1
            graph.attr('edge', style='solid', color='black')
            graph.edge(str(proc.pid[0][0]), str(proc.id))

            for e2 in read_nodiff_list:
                graph.attr('edge', style='dashed', color='green')
                graph.edge(str(e2[2]), str(proc.id))


        elif count_diff_r == 0 and count_diff_w > 0 and count_tmp_r > 0:
            graph.attr('node', style='filled', fillcolor='red')
            graph.node(str(proc.id), ''.join(
                [str(node_label), '#', name]), shape='square')
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1
            graph.attr('edge', style='solid', color='black')
            graph.edge(str(proc.pid[0][0]), str(proc.id))

            for e2 in read_tmp_list:
               graph.attr('edge', style='dashed', color='yellow')
               graph.edge(str(e2[2]), str(proc.id))
            for e2 in read_nodiff_list:
                graph.attr('edge', style='dashed', color='green')
                graph.edge(str(e2[2]), str(proc.id))


        elif count_diff_r > 0 and count_diff_w == 0 and count_tmp_w == 0:
          if name !="md5sum":
            graph.attr('node', style='filled', fillcolor='blue')
            graph.node(str(proc.id), ''.join(
                [str(node_label), '#', name]), shape='circle')
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1
            graph.attr('edge', style='solid', color='black')
            graph.edge(str(proc.pid[0][0]), str(proc.id))

            for e in read_diff_list:
               graph.attr('edge', style='dashed', color='red')
               graph.edge(str(e[2]), str(proc.id))
            for e2 in read_tmp_list:
               graph.attr('edge', style='dashed', color='yellow')
               graph.edge(str(e2[2]), str(proc.id))
            for e2 in read_nodiff_list:
                graph.attr('edge', style='dashed', color='green')
                graph.edge(str(e2[2]), str(proc.id))

        elif count_diff_r > 0 and count_diff_w == 0 and count_tmp_w > 0:
            graph.attr('node', style='filled', fillcolor='blue')
            graph.node(str(proc.id), ''.join(
                [str(node_label), '#', name]), shape='square')
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1
            graph.attr('edge', style='solid', color='black')
            graph.edge(str(proc.pid[0][0]), str(proc.id))

            for e in read_diff_list:
                graph.attr('edge', style='dashed', color='red')
                graph.edge(str(e[2]), str(proc.id))
            for e2 in read_tmp_list:
                graph.attr('edge', style='dashed', color='yellow')
                graph.edge(str(e2[2]), str(proc.id))
            for e2 in read_nodiff_list:
                graph.attr('edge', style='dashed', color='green')
                graph.edge(str(e2[2]), str(proc.id))

        elif count_diff_r == 0 and count_tmp_r == 0 and count_diff_w == 0 and count_tmp_w == 0:
            graph.attr('node', style='filled', fillcolor='yellowgreen')
            graph.node(str(proc.id), ''.join(
                [str(node_label), '#',name]), shape='circle')
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1
            graph.attr('edge', style='solid', color='black')
            graph.edge(str(proc.pid[0][0]), str(proc.id))

            for e2 in read_nodiff_list:
                graph.attr('edge', style='dashed', color='green')
                graph.edge(str(e2[2]), str(proc.id))

        # elif count_diff_r==0 and count_tmp_r>0 and count_diff_w==0 and count_tmp_w>0:
        else:
            graph.attr('node', style='filled', fillcolor='yellowgreen')
            graph.node(str(proc.id), ''.join(
                [str(node_label), '#', name]), shape='square')
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1
            graph.attr('edge', style='solid', color='black')
            graph.edge(str(proc.pid[0][0]), str(proc.id))

            for e in read_diff_list:
                graph.attr('edge', style='dashed', color='red')
                graph.edge(str(e[2]), str(proc.id))
            for e2 in read_tmp_list:
                graph.attr('edge', style='dashed', color='yellow')
                graph.edge(str(e2[2]), str(proc.id))
            for e2 in read_nodiff_list:
                graph.attr('edge', style='dashed', color='green')
                graph.edge(str(e2[2]), str(proc.id))

        wf = pd.DataFrame(write_diff_list, columns=['process_ID', 'name'])
        rf = pd.DataFrame(read_diff_list, columns=['process_ID', 'name','created_process'])
        tr = pd.DataFrame(read_tmp_list, columns=['process_ID', 'name','created_process'])
        tw = pd.DataFrame(write_tmp_list, columns=['process_ID', 'name'])

        write_files.write(str(proc.id)+"\t"+str(proc.name) + "\ntotal write/read files:\t" + str(len(proc.data)) + "\nlevel\t" + str(
            proc.getLevel()) + "\ntotal write files with diff: " + str(count_diff_w) + "\n\n")
        wf.to_csv(write_files, sep='\t', index=False)
        write_files.write("\ntotal read files with diff: " + str(count_diff_r) + "\n\n")
        rf.to_csv(write_files, sep='\t', index=False)
        write_files.write("\ntotal read temp files: " + str(count_tmp_r) + "\n\n")
        tr.to_csv(write_files, sep='\t', index=False)
        write_files.write("\ntotal write temp files: " + str(count_tmp_w) + "\n\n")
        tw.to_csv(write_files, sep='\t', index=False)
        write_files.write("\n************************************\n\n")

    wproc = pd.DataFrame(proc_list, columns=['node', 'process_ID', 'total_R/W', 'read_diff', 'read_no_diff',
                                             'read_temp', 'write_diff', 'write_no_diff',
                                             'wite_temp', 'process_name'])
    wproc.to_csv(write_proc, sep='\t', index=False)
    graph.render()
    #graph.view()

if __name__=='__main__':
    main();