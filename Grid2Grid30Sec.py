from farmware_tools import app
from farmware_tools import device
from farmware_tools import env
from farmware_tools import get_config_value
import json
import os

# TODO work out why it takes the Farmware librarys so long to load: 
# https://forum.farmbot.org/t/farmware-moveabsolute-and-executesequence-not-working/5784/28

# Rewrite of Grid2Grid to run in 30 seconds due to limitations put on Farmware 
# i.e. Farmware can only run for 30 seconds and there is a 2 second delay between device calls
# the only way to loop is to use sequence recursion
# There will be three calls to the device to stay within the 30 second window
# 1 - Get the current coordinates from a config file the first move is done to prime the loop before Grid2Grid is called
# 2 - Once the next co-ordinates are identified based on the current co-ordinates weite them to a config file and move there
# 3 - Log the move

# Decide if you pass a start flag for the first grid move on subsequent calls set this to false
# May need to pass the current x, y, z co-ordinates rather than make the first call for the current co-ordinates

# To work out Z axis height
# 1. To work out the X axis angle use simple trig: angle = sin(angle) = opposite \ hypotenuse i.e. angle = sin-1 (opposite \ hypotenuse)
# 2. To work out Z axis height i.e the opposite: hypotenuse = current X pos - beginining of X then opposite = sin(angle) * hypotenuse
# 3. Then add that height (the opposite) to the startZGrid value

# Remember if using alternate inbetween last row is missed so:
# Normal grid: 3 rows x 2 columns = 6 cells
# Alternate in between grid: 2 rows x 4 columns = 6 cells as last rows 2 of alternate inbetween columns missed
# Not tested turning alternate inbetween on both grids at the same time
# A better way would be to initialise 2 arrays with x,y coordinates and loop through them but this algo works

try :
    rowsGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='rowsGrid1', value_type=int)
    colsGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='colsGrid1', value_type=int)
    spaceBetweenRowsGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='spaceBetweenRowsGrid1', value_type=float)
    spaceBetweenColsGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='spaceBetweenColsGrid1', value_type=float)
    startXGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='startXGrid1', value_type=float)
    startYGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='startYGrid1', value_type=float)
    startZGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='startZGrid1', value_type=float)
    begininingOfXGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='begininingOfXGrid1', value_type=float)
    sineOfAngleXGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='sineOfAngleXGrid1', value_type=float)
    alternateInBetweenGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='alternateInBetweenGrid1', value_type=int)
    startLastRowOfGrid1 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='startLastRowOfGrid1', value_type=int)

    rowsGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='rowsGrid2', value_type=int)
    colsGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='colsGrid2', value_type=int)
    spaceBetweenRowsGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='spaceBetweenRowsGrid2', value_type=float)
    spaceBetweenColsGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='spaceBetweenColsGrid2', value_type=float)
    startXGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='startXGrid2', value_type=float)
    startYGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='startYGrid2', value_type=float)
    startZGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='startZGrid2', value_type=float)
    begininingOfXGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='begininingOfXGrid2', value_type=float)
    sineOfAngleXGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='sineOfAngleXGrid2', value_type=float)
    alternateInBetweenGrid2 = get_config_value(farmware_name='Grid2Grid30Sec', config_name='alternateInBetweenGrid2', value_type=int)

    # Set config file and environment variable names
    configFileName = '/tmp/farmware/config.json'
    evName = 'xyCoordinates'
    configContents = ''

    # Initialise row (X) and column (Y) indexes for all grids
    rowGrid1Index = 0
    colGrid1Index = 0
    rowGrid2Index = 0
    colGrid2Index = 0
    addToZHeightGrid1 = 0
    addToZHeightGrid2 = 0

    # Initialise the current Position Found flags to not found
    currentPositionGrid1Found = False
    currentPositionGrid2Found = False

    # Set constant Z positions
    zPosGrid1 = startZGrid1
    zPosGrid2 = startZGrid2

    # Get the current position for x and y from the device
    # currentPosition = device.get_current_position()
    # currentPositionXstr = str(currentPosition['x'])
    # currentPositionX = int(currentPositionXstr.split('.')[0])
    # currentPositionYstr = str(currentPosition['y'])
    # currentPositionY = int(currentPositionYstr.split('.')[0])

    # Get the current position for x and y from the config
    with open(configFileName, 'r') as f:
        configContents = json.load(f)
        f.close()

    # Edit the data
    currentPositionXstr = str(configContents[evName]).split(",",-1)[0]
    currentPositionX = int(currentPositionXstr.split('.')[0])
    currentPositionYstr = str(configContents[evName]).split(",",-1)[1]
    currentPositionY = int(currentPositionYstr.split('.')[0])

    # Start the first grid movement
    for rowGrid1Index in range(rowsGrid1):
        # Set first grids y position back to the first column
        yPosGrid1 = startYGrid1

        for colGrid1Index in range(colsGrid1):
            # Set the x and y positions on the first grid if alternateInBetween assume the first 
            # column is not an alternateInBetween then odd numbered colums are
            # if startLastRowOfGrid1 then the x position starts on the last row and moves backwards
            if alternateInBetweenGrid1 == 1 :
                if colGrid1Index > 0 and (colGrid1Index % 2) > 0 :
                    #device.log(message='Grid 1 alternateInBetween', message_type='success')
                    if startLastRowOfGrid1 == 1 :
                        xPosGrid1 = startXGrid1 - (spaceBetweenRowsGrid1 * 0.5) - (spaceBetweenRowsGrid1 * rowGrid1Index)
                    else :
                        xPosGrid1 = startXGrid1 + (spaceBetweenRowsGrid1 * 0.5) + (spaceBetweenRowsGrid1 * rowGrid1Index)
                else :
                    if startLastRowOfGrid1 == 1 :
                        xPosGrid1 = startXGrid1 - (spaceBetweenRowsGrid1 * rowGrid1Index)
                    else :
                        xPosGrid1 = startXGrid1 + (spaceBetweenRowsGrid1 * rowGrid1Index)
            else :
                if startLastRowOfGrid1 == 1 :
                    xPosGrid1 = startXGrid1 - (spaceBetweenRowsGrid1 * rowGrid1Index)                    
                else :
                    xPosGrid1 = startXGrid1 + (spaceBetweenRowsGrid1 * rowGrid1Index)

            # 1st grid move set the first grid row index back to zero if alternate inbetween column on last row let the loop handle the rest
            if ((alternateInBetweenGrid1 == 1)                  # Is alternateInBetween
            and (colGrid1Index > 0 and (colGrid1Index % 2) > 0) # is on an alternateInBetween odd numbered (offset) column  
            and (rowGrid1Index >= rowsGrid1 - 1)) :             # is on the second to last row index as an alternateInBetween has 1 less row
                # Increment y column position for grid 1
                yPosGrid1 = yPosGrid1 + spaceBetweenColsGrid1
                #device.log(message='Grid 1 alternateInBetween column last row so miss a row', message_type='success')
            else :
                # If the second grid was found then move otherwise check if we've reached the current position
                if currentPositionGrid2Found == True :
                    # Delete and then rewrite the config file with the new co-ordinate
                    os.remove(configFileName)
                    configContents = {evName: str(xPosGrid1) + "," + str(yPosGrid1)}
                    with open(configFileName, 'w') as f:
                        json.dump(configContents, f)
                        f.close()

                    # Get the height additions for the Z axis if there is an x axis length and angle 
                    if (begininingOfXGrid1 != 0) and (sineOfAngleXGrid1 != 0) :
                        hypotenuseGrid1 = xPosGrid1 - begininingOfXGrid1
                        addToZHeightGrid1 = sineOfAngleXGrid1 * hypotenuseGrid1
                        
                    # Do the move
                    device.move_absolute(
                        {
                            'kind': 'coordinate',
                            'args': {'x': xPosGrid1, 'y': yPosGrid1, 'z': addToZHeightGrid1}
                        },
                        100,
                        {
                            'kind': 'coordinate',
                            'args': {'x': 0, 'y': 0, 'z': 0}
                        }
                    )
                        
                    currentPositionGrid2Found = False
                    #device.log('Grid 1 moving to ' + str(xPosGrid1) + ', ' + str(yPosGrid1) + ', ' + str(zPosGrid1), 'success', ['toast'])
                elif ((xPosGrid1 - 5) <= currentPositionX <= (xPosGrid1 + 5)) and ((yPosGrid1 - 5) <= currentPositionY <= (yPosGrid1 + 5)) :
                    currentPositionGrid1Found = True

                # Set the x and y positions on the second grid if alternateInBetween assume the first 
                # column is not an alternateInBetween then odd numbered colums are
                if alternateInBetweenGrid2 == 1 :
                    if colGrid2Index > 0 and (colGrid2Index % 2) > 0 :
                        device.log(message='Grid 2 alternateInBetween column', message_type='success')
                        xPosGrid2 = startXGrid2 + (spaceBetweenRowsGrid2 * 0.5) + (spaceBetweenRowsGrid2 * rowGrid2Index)
                    else :
                        xPosGrid2 = startXGrid2 + (spaceBetweenRowsGrid2 * rowGrid2Index)
                else :
                    xPosGrid2 = startXGrid2 + (spaceBetweenRowsGrid2 * rowGrid2Index)
                
                yPosGrid2 = startYGrid2 + (spaceBetweenColsGrid2 * colGrid2Index)

                # If the first grid was found then move otherwise check if we've reached the current position
                if currentPositionGrid1Found == True :
                    # Delete and then rewrite the config file with the new co-ordinate
                    os.remove(configFileName)
                    configContents = {evName: str(xPosGrid2) + "," + str(yPosGrid2)}
                    with open(configFileName, 'w') as f:
                        json.dump(configContents, f)
                        f.close()

                    # Get the height additions for the Z axis if there is an x axis length and angle 
                    if (begininingOfXGrid2 != 0) and (sineOfAngleXGrid2 != 0) :
                        hypotenuseGrid2 = xPosGrid2 - begininingOfXGrid2
                        addToZHeightGrid2 = sineOfAngleXGrid2 * hypotenuseGrid2

                    # Do the move
                    device.move_absolute(
                        {
                            'kind': 'coordinate',
                            'args': {'x': xPosGrid2, 'y': yPosGrid2, 'z': addToZHeightGrid2}
                        },
                        100,
                        {
                            'kind': 'coordinate',
                            'args': {'x': 0, 'y': 0, 'z': 0}
                        }
                    )

                    currentPositionGrid1Found = False
                    #device.log('Grid 2 moving to ' + str(xPosGrid2) + ', ' + str(yPosGrid2) + ', ' + str(zPosGrid2), 'success', ['toast'])
                elif ((xPosGrid2 - 5) <= currentPositionX <= (xPosGrid2 + 5)) and ((yPosGrid2 - 5) <= currentPositionY <= (yPosGrid2 + 5)) :
                    currentPositionGrid2Found = True

                # Increment y column position for grid 1
                yPosGrid1 = yPosGrid1 + spaceBetweenColsGrid1

                # Set the second grid row and column indexes
                if ((alternateInBetweenGrid2 == 1)                  # Is alternateInBetween
                and (colGrid2Index > 0 and (colGrid2Index % 2) > 0) # is on an alternateInBetween odd numbered (offset) column  
                and (rowGrid2Index >= rowsGrid2 - 2)) :              # is on the second to last row index as an alternateInBetween has 1 less row
                    rowGrid2Index = 0                                   # Reset row index
                    colGrid2Index += 1                                  # Increment column index to move to the next column
                elif rowGrid2Index >= (rowsGrid2 - 1) :             # else if on the last row
                    rowGrid2Index = 0                                   # Reset row index
                    colGrid2Index += 1                                  # Increment column index to move to the next column
                else :                                              # else
                    rowGrid2Index += 1                                  # Increment row index to move to the next row
except :
    pass # To ignore the error "Failed to execute command: Firmware error @ “get_position”: :farmware_exit at x=2218.2, y=41, z=0"