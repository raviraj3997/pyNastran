import sys
import copy
from numpy import array
from struct import unpack

# pyNastran
from ogf_Objects import gridPointForcesObject,complexGridPointForcesObject

class OGF(object):
    """Table of Grid Point Forces"""

    def readTable_OGF(self):
        table3 = self.readTable_OGF_3
        table4Data = self.readOGF_Data
        self.readResultsTable(table3,table4Data)
        self.deleteAttributes_OGF()

    def deleteAttributes_OGF(self):
        params = ['formatCode','appCode','numWide','value1','value2',]
        self.deleteAttributes(params)
    
    #def addDataParameter(self,data,Name,Type,FieldNum,applyNonlinearFactor=True):
    #    #self.mode = self.getValues(data,'i',5) ## mode number
    #    value = self.getValues(data,Type,FieldNum)
    #    setattr(self,Name,value)
    #    self.dataCode[Name] = value
    #    
    #    if applyNonlinearFactor:
    #        self.nonlinearFactor = value
    #        self.dataCode['nonlinearFactor'] = value
    #        self.dataCode['name'] = Name
    
    def applyDataCodeValue(self,Name,value):
        self.dataCode[Name] = value
        
    def readTable_OGF_3(self,iTable): # iTable=-3
        bufferWords = self.getMarker()
        if self.makeOp2Debug:
            self.op2Debug.write('bufferWords=%s\n' %(str(bufferWords)))
        #print "2-bufferWords = ",bufferWords,bufferWords*4,'\n'

        data = self.getData(4)
        bufferSize, = unpack('i',data)
        data = self.getData(4*50)
        #print self.printBlock(data)
        
        (three) = self.parseApproachCode(data)

        self.addDataParameter(data,'formatCode',  'i',9,False)   ## format code
        self.addDataParameter(data,'appCode',     'i',9,False)   ## approach code ???
        self.addDataParameter(data,'numWide',     'i',10,False)  ## number of words per entry in record; @note is this needed for this table ???
        self.addDataParameter(data,'value1',      'i',11,False)  ## Data Value 1
        self.addDataParameter(data,'value2',      'f',12,False)  ## Data Value 2
        
        #self.printBlock(data) # on
        ## assuming tCode=1
        if self.analysisCode==1:   # statics / displacement / heat flux
            self.extractDt = self.extractInt
            self.applyDataCodeValue('dataNames',['lsdvmn'])
        elif self.analysisCode==2: # real eigenvalues
            self.extractDt = self.extractInt
            self.applyDataCodeValue('dataNames',['mode','eigr','modeCycle'])
        elif self.analysisCode==3: # differential stiffness
            #self.lsdvmn = self.getValues(data,'i',5) ## load set number
            self.extractDt = self.extractInt
        elif self.analysisCode==4: # differential stiffness
            self.extractDt = self.extractInt
        elif self.analysisCode==5:   # frequency
            self.extractDt = self.extractFloat
            self.applyDataCodeValue('dataNames',['freq'])
        elif self.analysisCode==6: # transient
            self.extractDt = self.extractFloat
        elif self.analysisCode==7: # pre-buckling
            self.extractDt = self.extractInt
            self.applyDataCodeValue('dataNames',['lsdvmn'])
        elif self.analysisCode==8: # post-buckling
            self.extractDt = self.extractInt
            self.applyDataCodeValue('dataNames',['lsdvmn','eigr'])
        elif self.analysisCode==9: # complex eigenvalues
            self.extractDt = self.extractInt
            self.applyDataCodeValue('dataNames',['mode','eigr','eigi'])
        elif self.analysisCode==10: # nonlinear statics
            self.extractDt = self.extractFloat
            self.applyDataCodeValue('dataNames',['lftsfq'])
        elif self.analysisCode==11: # old geometric nonlinear statics
            self.extractDt = self.extractInt
            self.applyDataCodeValue('dataNames',['lsdvmn'])
        elif self.analysisCode==12: # contran ? (may appear as aCode=6)  --> straight from DMAP...grrr...
            self.extractDt = self.extractInt
            self.applyDataCodeValue('dataNames',['lsdvmn'])
        else:
            raise InvalidAnalysisCodeError('invalid analysisCode...analysisCode=%s' %(self.analysisCode))

        
        #print "*iSubcase=%s"%(self.iSubcase)
        #print "analysisCode=%s tableCode=%s thermal=%s" %(self.analysisCode,self.tableCode,self.thermal)

        #self.printBlock(data)
        self.readTitle()

    def extractDt(self):
        pass
    def extractInt(self):
        return 'i',self.scaleEid
    def extractFloat(self):
        return 'f',self.scaleDt
    def scaleEid(self,eid):
        return (eid-self.deviceCode)//10
    def scaleDt(self,dt):
        return dt

    def readOGF_Data(self):
        #print "self.analysisCode=%s tableCode(1)=%s thermal(23)=%g" %(self.analysisCode,self.tableCode,self.thermal)
        tfsCode = [self.tableCode,self.formatCode,self.sortCode]
        #print self.dataCode
        #if self.thermal==2:
        #    self.skipOES_Element()
        #print "tfsCode=%s" %(tfsCode)
        
        if self.tableCode==19: # grid point forces
            self.readOGF_Data_table19()
        else:
            #self.log.debug('skipping approach/table/format/sortCode=%s on %s-OGF table' %(self.tableName,self.atfsCode))
            print self.codeInformation()
            #self.skipOES_Element()
            raise NotImplementedError('bad approach/table/format/sortCode=%s on %s-OGF table' %(self.atfsCode,self.tableName))
        ###
        #print self.obj


    def readOGF_Data_table19(self): # grid point forces
        isSort1 = self.isSort1()
        if self.numWide==10:  # real/random
            #if self.thermal==0:
            self.createTransientObject(self.gridPointForces,gridPointForcesObject) # real
            #else:
                #raise NotImplementedError(self.codeInformation())
            #self.OUG_RealTable()
            self.readOGF_numWide10()
        elif self.numWide==16:  # real/imaginary or mag/phase
            #if self.thermal==0:
            self.createTransientObject(self.gridPointForces,complexGridPointForcesObject) # complex
            #else:
                #raise NotImplementedError(self.codeInformation())
            self.readOGF_numWide16()
            #self.OUG_ComplexTable()
        else:
            raise NotImplementedError('only numWide=10 or 16 is allowed  numWide=%s' %(self.numWide))
        ###

    def readOGF_numWide10(self):
        (eKey,scaleValue) = self.extractDt()
        Format = eKey+'issssssssffffff'
        while len(self.data)>=40:
            eData     = self.data[0:4*10]
            self.data = self.data[4*10: ]
            out = unpack(Format,eData)
            (eKey,eid,a,b,c,d,e,f,g,h,f1,f2,f3,m1,m2,m3) = out
            eKey = scaleValue(eKey)
            elemName = a+b+c+d+e+f+g+h
            elemName = elemName.strip()
            #data = (eid,elemName,f1,f2,f3,m1,m2,m3)
            self.obj.add(eKey,eid,elemName,f1,f2,f3,m1,m2,m3)
            #print "eid/dt/freq=%s eid=%-6s eName=%-8s f1=%g f2=%g f3=%g m1=%g m2=%g m3=%g" %(ekey,eid,elemName,f1,f2,f3,m1,m2,m3)
            #sys.exit('asfd')
        #print len(self.data)
        self.handleResultsBuffer(self.readOGF_numWide10)

    def readOGF_numWide16(self):
        (eKey,scaleValue) = self.extractDt()
        Format = eKey+'issssssssffffffffffff'
        while len(self.data)>=64:
            eData     = self.data[0:4*16]
            self.data = self.data[4*16: ]
            out = unpack(Format,eData)
            (eKey,eid,a,b,c,d,e,f,g,h,f1r,f2r,f3r,m1r,m2r,m3r,f1i,f2i,f3i,m1i,m2i,m3i) = out
            eKey = scaleValue(eKey)
            f1i = f1i*1j
            f1i = f2i*1j
            f1i = f3i*1j
            m1i = m1i*1j
            m2i = m2i*1j
            m3i = m3i*1j
            elemName = a+b+c+d+e+f+g+h
            elemName = elemName.strip()
            #print "eid/dt/freq=%s eid=%-6s eName=%-8s f1=%s f2=%s f3=%s m1=%s m2=%s m3=%s" %(ekey,eid,elemName,f1r+f1i,f2r+f2i,f3r+f3i,m1r+m1i,m2r+m2i,m3r+m3i)
            self.obj.add(eKey,eid,elemName,f1r,f2r,f3r,m1r,m2r,m3r,f1i,f2i,f3i,m1i,m2i,m3i)
        self.handleResultsBuffer(self.readOGF_numWide16)

    def readThermal4(self):
        #print self.codeInformation()
        #print self.printBlock(self.data)
        n=0
        nEntries = len(self.data)//32
        for i in range(nEntries):
            eData = self.data[n:n+32]
            out = unpack('iiffffff',eData)
            nid = (out[0]-self.deviceCode)//10

            #print out
            n+=32
            #print "nid = ",nid
        #sys.exit('thermal4...')
