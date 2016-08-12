from osgeo import gdal
import gdalconst
import numpy as np
import math
import time
import sqlite3
import matplotlib.pyplot as plt



start = time.time()
 


fn='srtm_20_04_burned_fill_ptner_clipped_clipped.asc' #set input D8 flow pointer
fn2='srtm_20_04_burned_fill_stream_3_clipped_clipped.asc' #ser input stream raster
resolution = 90  #set raster resolution (m)

##database_name ="sqlite_database1.db"  #set database name
##table_name= "gdal_result_test_44" #set table name (must be changed after each run)

ds = gdal.Open(fn)
ds2 = gdal.Open(fn2)
cols = ds.RasterXSize
rows = ds.RasterYSize
##bands = ds.RasterCount
##band = ds.GetRasterBand(1)

output_array_all = np.zeros([rows,cols])
output_array_major = np.zeros([rows,cols])

flow_pointer = ds.ReadAsArray(0,0,cols,rows).astype(np.int)
stream_link = ds2.ReadAsArray(0,0,cols,rows).astype(np.int)


dX = [1, 1, 1, 0, -1, -1, -1, 0]
dY = [-1, 0, 1, 1, 1, 0, -1, -1]
inFlowVals = [16, 32, 64, 128, 1, 2, 4, 8]
D8FlowVals = [1, 2, 4, 8, 16, 32, 64, 128]


numInFlowCells = 0
rivermouths = []
total_junctions = 0
print"reading raster...."
print "total rows is:",rows, "columns:",cols

for row in range(rows):
    for col in range(cols):
        if stream_link[row,col] > 0:  #for each cell with a valid value
            
            #find the river mouth cells
            
            if flow_pointer[row,col] == 0:# in case the cell is but won't flow out, it's because it reached the edge of the raster, therefore is a river mouth
                rivermouths.append([row,col])
                
                
            else:
                move_to = D8FlowVals.index(flow_pointer[row,col])

                x_outflow = col + dX[move_to]
                y_outflow = row + dY[move_to]
                
                
                
                if stream_link[y_outflow,x_outflow] == -9999: #if the cell has no outflow neigbour who is a vaild stream cell
                    
                    rivermouths.append([row,col])
                    

print "rivermouths found:",rivermouths

#find the major river on the input raster

forever = True
all_total_length = []
for one_rivermouth in rivermouths:
    
    print "searching rivermouth",one_rivermouth[0],one_rivermouth[1]
    next_group_yx = [one_rivermouth]
    next_group_numOrders = ["1"]
    total_length = 0
    
    ##next_group_yx = [[2972,1551]]
    ##next_group_numOrders = ["1"]
    while forever is True:
        current_group_yx = next_group_yx
        current_group_numOrders = next_group_numOrders
        next_group_yx = []
        next_group_numOrders = []
    
        for n in range(0,len(current_group_yx)):  #searching a group
      
            row = current_group_yx[n][0]
            col = current_group_yx[n][1]
            numOrder = current_group_numOrders[n]
            
            
            
            while forever is True:         #searching a stream
                nextcell = []
                numInFlowCells = 0
                for c in range(8):
                    x = col + dX[c]
                    y = row + dY[c]
                    try:
                        if stream_link[y,x] > 0 and flow_pointer[y,x] == inFlowVals[c]:
                            nextcell.append([y,x])
                            numInFlowCells += 1
                            if c in [0,2,4,6]:
                                total_length += math.sqrt(2)*resolution
                            else:
                                total_length += resolution
                    except:
                        pass
                    
                
                if numInFlowCells == 0:
                    ##print "row",y,"col",x, "is a headwater"
                    break
                    
                    
                elif numInFlowCells == 1:
                    y0=nextcell[0][0]; x0=nextcell[0][1]
                    output_array_all[y0,x0] = long(numOrder)
                    row = nextcell[0][0]
                    col = nextcell[0][1]
                    ##print row,col,numOrder
                    
                    ##print "order is" , numOrder
                    ##print "move to next cell"
                
                elif numInFlowCells == 2:
                    y0=nextcell[0][0]; x0=nextcell[0][1]
                    y1=nextcell[1][0]; x1=nextcell[1][1]           
                    output_array_all[y0,x0] = long(numOrder+"0")
                    output_array_all[y1,x1] = long(numOrder+"1")
                    next_group_yx.append([y0,x0])
                    next_group_yx.append([y1,x1])
                    
                    ##print next_group_yx
                    next_group_numOrders.append(numOrder+"0")
                    next_group_numOrders.append(numOrder+"1")
                    ##print "junction found, move to next stream"
                    
                    break
                else:
                    print "numInFlow Cells is :",numInFlowCells, "row:",row ,"col:", col
                    print "ERROR something else occured"                  
                    break
                
        if len(next_group_yx) != 0:
            current_group_yx = next_group_yx
            current_group_numOrders = next_group_numOrders 
            ##print"next_group has values",current_group_yx, "go to next group"
            
        else:
            ##print "no more stream found, searching completed"
            all_total_length.append(total_length)
            print "total length for this river is :", total_length
            break
        

a = all_total_length.index(max(all_total_length))

print "major river found at",
print rivermouths[a][0],rivermouths[a][1]


#------------------------------


#find the binary numbers in the major river#

next_group_yx = [rivermouths[a]]
next_group_numOrders = ["1"]
bin_length_list = []
while forever is True:
    current_group_yx = next_group_yx
    current_group_numOrders = next_group_numOrders
    next_group_yx = []
    next_group_numOrders = []

    for n in range(0,len(current_group_yx)):  #searching a group
  
        row = current_group_yx[n][0]
        col = current_group_yx[n][1]
        numOrder = current_group_numOrders[n]
        
        
        one_length = 0
        while forever is True:         #searching a stream
            nextcell = []
            numInFlowCells = 0
            for c in range(8):
                x = col + dX[c]
                y = row + dY[c]
                if stream_link[y,x] > 0 and flow_pointer[y,x] == inFlowVals[c]:
                    nextcell.append([y,x])
                    numInFlowCells += 1
                    if c in [0,2,4,6]:
                        one_length += math.sqrt(2)*resolution
                    else:
                        one_length += resolution                    
                    
            
            
            if numInFlowCells == 0:
                ##print "row",y,"col",x, "is a headwater"
                bin_length_list.append([numOrder,one_length])
                break
                
                
            elif numInFlowCells == 1:
                y0=nextcell[0][0]; x0=nextcell[0][1]
                output_array_major[y0,x0] = long(numOrder)
                row = nextcell[0][0]
                col = nextcell[0][1]
                ##print row,col,numOrder
                
                ##print "order is" , numOrder
                ##print "move to next cell"
            
            elif numInFlowCells == 2:
                y0=nextcell[0][0]; x0=nextcell[0][1]
                y1=nextcell[1][0]; x1=nextcell[1][1]           
                output_array_major[y0,x0] = long(numOrder+"0")
                output_array_major[y1,x1] = long(numOrder+"1") 
                next_group_yx.append([y0,x0])
                next_group_yx.append([y1,x1])
                next_group_numOrders.append(numOrder+"0")
                next_group_numOrders.append(numOrder+"1")
                
                bin_length_list.append([numOrder,one_length])
                one_length = 0
                ##print "junction found, move to the next stream"
                
                break
            else:
                print "ERROR something else occured"
            
    if len(next_group_yx) != 0:
        current_group_yx = next_group_yx
        current_group_numOrders = next_group_numOrders 
        ##print"next_group has values",current_group_yx, "go to next group"
        
    else:
        print "Major River Searching completed"
        
        
        
        break
    





# ---calculate accumulative length--- #

one_result = [] ; result_list = [] ; bin_result = [];
accu_result = []; bin_accu_list = []
for fetch_one in bin_length_list:
    this_bin= fetch_one[0]
    AccuLen = 0
    for nb in bin_length_list:
             
        each_bin = nb[0]
        
        tf = each_bin.startswith(this_bin)
        if tf == True:
            AccuLen += nb[1]
    
    one_result= [this_bin, AccuLen]
    bin_result.append(this_bin)
    accu_result.append(AccuLen) 
    bin_accu_list.append(one_result)






# calculate paired junction order #

x="1"
xi="1"
a = ""
counter = 0
AccuLen_a= 0
AccuLen_b= 0
forever = True
result_list = []
paired_result = []
new_bin_result= []
critical_point = []



while counter < len(bin_result):
    while forever == True:
        
    
        counter +=1
        this_bin = xi
        this_AccuLen = accu_result[bin_result.index(this_bin)]
        result_list.append([this_bin,this_AccuLen,counter])
        
        paired_result.append(counter)
        new_bin_result.append(this_bin)
        
        xa = xi+"0"
        xb = xi+"1"
        
        
        
        
        if xa in bin_result:
            
            AccuLen_a = accu_result[bin_result.index(xa)]
         
        else:
            break
         

        
        if xb is not bin_result:
            AccuLen_b = accu_result[bin_result.index(xb)]
                
        else:
            break
        
        
        
        if AccuLen_a > AccuLen_b:
          
            critical_point.append(xa)
            
            x = xb
            xi = xb
            #this_AccuLen = Acculen_b
         
        elif AccuLen_a < AccuLen_b:
          
            critical_point.append(xb)      
            x = xa
            xi = xa
            #this_AccuLen = Acculen_a
     
      
 

  
    if counter < len(bin_result):
        xi = critical_point[-1]
        critical_point.pop()
    

print result_list
print new_bin_result
  
  






# plot river network, matplotlib#


x=[] ; y=[]
for each_result in result_list:
    
  
    paired = each_result[2]
    AccuLen = each_result[1]

    x.append(AccuLen)
    y.append(paired)
  

sqrt_x =np.sqrt(x)

fig, ax = plt.subplots()
ax.set_xlabel('Sqaure Root of Accumulative Length (m-1)')
ax.set_ylabel('Network Order')
ax.set_title("Test Paired Juntion Plot", va='bottom')
ax.scatter(sqrt_x, y)



#mycursor.execute(select_query.format("dev,tier,BIN,paired_junction,shreve,AccuLen",table_name))
#fetch_all = mycursor.fetchall()

#mycursor.execute(select_query.format("dev,tier,BIN,paired_junction,shreve,AccuLen",table_name))
#fetch_one = mycursor.fetchone()

for fetch_one in new_bin_result:
    
    if fetch_one + "1" in new_bin_result:
        
        x = math.sqrt(result_list[new_bin_result.index(fetch_one)][1])
        y = result_list[new_bin_result.index(fetch_one)][2]
        x0 = math.sqrt(result_list[new_bin_result.index(fetch_one+"0")][1])
        y0 = result_list[new_bin_result.index(fetch_one+"0")][2]
        x1 = math.sqrt(result_list[new_bin_result.index(fetch_one+"1")][1])
        y1 = result_list[new_bin_result.index(fetch_one+"1")][2]
        

      
            
        if y0 > y1:
            a  = y0
            y0 = y1
            y1 = a
            b = x0
            x0 = x1
            x1 = b
          
        
        xaxis=[x0,x,x1]
       
        yaxis=[y0,y,y1]
              
        connect_point = float(x1)+float(y1-y0)/float(y1-y)*float(x-x1)
              
    
              
        connect_line_x = [x0,connect_point]
        connect_line_y = [y0,y0]
              
              
    
        plt.plot(xaxis,yaxis,c="#0095E5")
        #plt.plot(connect_line_x,connect_line_y,c="#0095E5")
                    
            
          
          
            

plt.show()


print"Completed!"


end = time.time()
print "time elapsed:", (end - start)
