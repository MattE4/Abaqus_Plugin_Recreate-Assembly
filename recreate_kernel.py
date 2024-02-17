from __future__ import print_function
from abaqus import *
from abaqusConstants import *
#import regionToolset
#from time import *

def recreateAssembly(kw_instance=None, kw_parts=None):

    ##########################################################################################
    # check if selection is valid
    if kw_instance == None:
        #print '\nError: Select face(s) and confirm selection before pressing Apply or OK'
        getWarningReply(message='No instance selected!', buttons=(CANCEL,))
        return

    ##########################################################################################

    #t1 = clock()

    master = kw_instance    
    
    vpName = session.currentViewportName
    modelName = session.sessionState[vpName]['modelName']
    
    m = mdb.models[modelName]
    a = m.rootAssembly
    
    equals = []
    instancelist = []
    global CSYSname
    CSYSname = 'CSYS_part_pos'
    
    ###########################################################################
    ### get names
    
    masterinstance_name = master.name
    masterpart_name = master.partName
    
    
    ############################################################################
    ### function get volume
    
    def getVolume(fname):
    
        fmassprops = m.parts[fname].getMassProperties(relativeAccuracy=MEDIUM)
        fvolume = fmassprops['volume']
    
        return fvolume
    
    ############################################################################
    ### function get area
    
    def getArea(fname):
    
        fmassprops = m.parts[fname].getMassProperties(relativeAccuracy=MEDIUM)
        farea = fmassprops['area']
        if farea != None:
            if farea > 100:
                farea = round(farea,2)
            else:
                farea = round(farea,4)
        return farea
    
    ############################################################################
    ### function get edge length
    
    def getEdgesize(fname, index):
    
        flength = m.parts[fname].edges[index].getSize(printResults=False)
        flength = round(flength,3)
    
        return flength
    
    ############################################################################
    ### function get face size
    
    def getFacesize(fname, index):
    
        fsize = m.parts[fname].faces[index].getSize(printResults=False)
        fsize = round(fsize,3)
    
        return fsize
    
    
    ############################################################################
    ### function get attributes
    
    def getAttributes(fname):
    
        fatt = m.parts[fname].queryAttributes(printResults=False)
        fvertices = fatt['numVertices']
        fedges = fatt['numEdges']
        ffaces = fatt['numFaces']
        fcells = fatt['numCells']
        
        fentries = [fvertices, fedges, ffaces, fcells]
    
        return fentries
    
    
    ############################################################################
    ### function create CSYS
    
    def createCSYS(fname):
    
        v1 = m.parts[fname].vertices
        m.parts[fname].DatumCsysByThreePoints(origin=v1[0], point1=v1[1], point2=v1[-1], 
            name=CSYSname, coordSysType=CARTESIAN)
    

    ############################################################################################################################
    ############################################################################################################################
    ### get masterpart attributes
    
    try:
        mp_attributes = getAttributes(masterpart_name)
    except:
        print('\nError: Invalid master instance. Only face and solid geometry is supported.')
        return
    
    mp_num_vertices = mp_attributes[0]
    mp_num_edges = mp_attributes[1]
    mp_num_faces = mp_attributes[2]
    mp_num_cells = mp_attributes[3]
    mp_volume = getVolume(masterpart_name)
    mp_area = getArea(masterpart_name)

    # exit script if master is line geometry
    if mp_num_vertices < 3 or mp_num_faces < 1:
        print('\nError: Invalid master instance. Only face and solid geometry is supported.')
        return
    
    mp_size_edge_1 = getEdgesize(masterpart_name,0)
    mp_size_edge_2 = getEdgesize(masterpart_name,1)
    mp_size_last_edge = getEdgesize(masterpart_name,-1)
    mp_size_face_1 = getFacesize(masterpart_name,0)
    mp_size_last_face = getFacesize(masterpart_name,-1)
    

    
    

    ############################################################################
    ### find equal parts
    
    for x in m.parts.keys():
        if x != masterpart_name:
    
            same=[] #dummy list to monitor equal criteria
            
            try:
                attributes = getAttributes(x)
            except:
                continue
            
            # num vertices
            if mp_num_vertices == attributes[0]:
                same.append(1)
            if len(same) != 1:
                continue
    
            #volume
            p_volume = getVolume(x)
            if mp_volume == None and p_volume == None:
                same.append(2)
            else:
                try:       
                    percent_diff = (100./mp_volume)*p_volume
                    if percent_diff > 99.8 and percent_diff < 100.2:
                        same.append(2)
                except:
                    pass
            if len(same) != 2:
                continue
                
            # area
            p_area = getArea(x)
            if mp_area == None and p_area == None:
                same.append(3)
            else:
                try:       
                    percent_diff = (100./mp_area)*p_area
                    if percent_diff > 99.8 and percent_diff < 100.2:
                        same.append(3)
                except:
                    pass            
            if len(same) != 3:
                continue
    
            # num edges
            if mp_num_edges == attributes[1]:
                same.append(4)
            
            # num faces
            if mp_num_faces == attributes[2]:
                same.append(5)            
            
            # num cells
            if mp_num_cells == attributes[3]:
                same.append(6)
            
            # size edge 1
            if mp_size_edge_1 == getEdgesize(x,0):
                same.append(7)
            
            # size edge 2
            if mp_size_edge_2 == getEdgesize(x,1):
                same.append(8)
            
            # size last edge
            if mp_size_last_edge == getEdgesize(x,-1):
                same.append(9)
            
            # size face 1
            if mp_size_face_1 == getFacesize(x,0):
                same.append(10)
            
            # size last face
            if mp_size_last_face == getFacesize(x,-1):
                same.append(11)
    
            if len(same)==11:
                equals.append(x)
            #print '\n\n', x, same
            #print same

    print('\nFound '+str(len(equals))+' other identical part(s)')


    ############################################################################

    #t2 = clock()
    #t = t2 - t1
    #print '\nRuntime (s): ', t

    if len(equals) > 0:
        
        session.viewports[vpName].disableColorCodeUpdates()     

        ########################################################################################
        ### prepare lists
        
        # equals contains all parts that are equal to the masterinstance
        # instancelist contains all instances from parts of list equals
        # partlist contains all equal parts  plus the masterpart
    
        
        #print '\n\n******'
        #print equals
        
        partlist = equals[:]
        partlist.append(masterpart_name)
        

        #print partlist
        
        for x in a.instances.keys():
            if a.instances[x].partName in equals:
                instancelist.append(x)
    
        
        print('Replacing these instances:')
        print(instancelist)
        print('\n\n')
    
    
        ########################################################################################
        ### create CSYS on parts
        
        for i in partlist:
            createCSYS(i)
        
    
        ########################################################################################
        ### get dependent/ independent setting of instance    
        
        dep = a.instances[masterinstance_name].dependent
        if dep == 0:
            depcrit=OFF
        else:
            depcrit=ON
    
    
    
        ########################################################################################
        ### create instances

        for iname in instancelist:
        
            ### find new name
            i=0
            x=0
            existingnames = a.instances.keys()
            while x==0:
                x = 1
                i = i+1
                newinst_name = masterpart_name+'-'+str(i)
                for name in existingnames:
                    if name.find(newinst_name) != -1:
                        x = 0
            
        
            ### create new instance
            newinst = a.Instance(name=newinst_name, part=m.parts[masterpart_name], dependent=depcrit)
            a.regenerate()

    
            ### position instance and delete old one
    
            m_id = m.parts[masterpart_name].features[CSYSname].id
            d_m = a.instances[newinst_name].datums[m_id]
        
            i_id = m.parts[a.instances[iname].partName].features[CSYSname].id
            d_i = a.instances[iname].datums[i_id]
            a.ParallelCsys(movableCsys=d_m, fixedCsys=d_i)
        
            v1 = a.instances[newinst_name].vertices
            v2 = a.instances[iname].vertices
            a.CoincidentPoint(movablePoint=v1[0], fixedPoint=v2[0])
        
            p1 = a.instances[newinst_name]
            p1.ConvertConstraints()
        
            del a.features[iname]
            #a.regenerate()
        

        ########################################################################################
        ### delete CSYS on parts
        
        for i in partlist:
            del m.parts[i].features[CSYSname]
            
        ########################################################################################
        
        a.regenerate()
        session.viewports[vpName].enableColorCodeUpdates()
        session.viewports[vpName].forceRefresh()    
        #session.viewports[vpName].view.fitView()
    
    
        ###############################################################################################
        # get unused parts from partlist and delete unused parts
        
        if kw_parts and len(equals) > 0:
            unused_parts = equals[:]
            for i in a.instances.keys():
                if a.instances[i].partName in unused_parts:
                    unused_parts.remove(a.instances[i].partName)
            
            print('\nDeleting these '+str(len(unused_parts))+' part(s):')
            print(unused_parts)
            
            for i in unused_parts:
                del mdb.models[modelName].parts[i]
    
    
        
        #t3 = clock()
        #t = t3 - t1
        #print '\nRuntime [s]: ', t
