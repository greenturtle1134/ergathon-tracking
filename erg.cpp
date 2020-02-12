// erg.cpp : Defines the exported functions for the DLL application.
//

#include "windows.h"
#include <stdio.h>

#include <string>

#include "PM3DDICP.h"
#include "PM3CsafeCP.h"
//#include "pc_error.h"
#include "MMSystem.h"
//#include "tk_time.h"
//#include "csafe.h"

#pragma pack(push, before_firmware, 1)
//#include "logmap.h"
#pragma pack(pop, before_firmware)

extern "C" __declspec(dllexport) UINT16_T __cdecl GetNumDevices()
{
    UINT16_T numOldPM3Devices = 0;
    UINT16_T numNewPM3Devices = 0;
    UINT16_T numPM4Devices = 0;
    UINT16_T numPM5Devices = 0;
    ERRCODE_T ecode = 0;

    UINT16_T numCommunicating = 0;

    // Look for PM3 devices
    ecode = tkcmdsetDDI_discover_pm3s(TKCMDSET_PM3_PRODUCT_NAME2, 0, &numCommunicating);

    if (!ecode && numCommunicating)
    {
        // We discovered one or more PM3's
        numNewPM3Devices = numCommunicating;
    }

    // Look for old style PM3 devices, starting numbering after the previous
    ecode = tkcmdsetDDI_discover_pm3s(TKCMDSET_PM3_PRODUCT_NAME, numCommunicating, &numCommunicating);

    if (!ecode && numCommunicating)
    {
        // We discovered one or more old PM3's
        numOldPM3Devices = numCommunicating - numNewPM3Devices;
    }

    // Look for PM4 devices
    ecode = tkcmdsetDDI_discover_pm3s(TKCMDSET_PM4_PRODUCT_NAME, numCommunicating, &numCommunicating);

    if (!ecode && numCommunicating)
    {
        // We discovered one or more PM4's
        numPM4Devices = numCommunicating - numNewPM3Devices - numOldPM3Devices;
    }

    // Look for PM5 devices
    ecode = tkcmdsetDDI_discover_pm3s(TKCMDSET_PM5_PRODUCT_NAME, numCommunicating, &numCommunicating);

    if (!ecode && numCommunicating)
    {
        // We discovered one or more PM5's
        numPM5Devices = numCommunicating - numNewPM3Devices - numOldPM3Devices - numPM4Devices;
    }

    return numCommunicating;
}

extern "C" __declspec(dllexport) UINT16_T __cdecl GetNumDevices2()
{
    ERRCODE_T ecode = 0;
    UINT16_T numCommunicating = 0;
    ecode = tkcmdsetDDI_discover_pm3s("Concept", numCommunicating, &numCommunicating);
    return numCommunicating;
}

extern "C" __declspec(dllexport) UINT16_T __cdecl GetNumDevicesForPMVersion(int ver)
{
    ERRCODE_T ecode = 0;
    UINT16_T numCommunicating = 0;

    switch (ver)
    {
    case 2:
        // Look for old style PM3 devices, starting numbering after the previous
        ecode = tkcmdsetDDI_discover_pm3s(TKCMDSET_PM3_PRODUCT_NAME, 0, &numCommunicating);
    case 3:
        // Look for PM3 devices
        ecode = tkcmdsetDDI_discover_pm3s(TKCMDSET_PM3_PRODUCT_NAME2, 0, &numCommunicating);
        break;
    case 4:
        // Look for PM4 devices
        ecode = tkcmdsetDDI_discover_pm3s(TKCMDSET_PM4_PRODUCT_NAME, 0, &numCommunicating);
        break;
    case 5:
        // Look for PM5 devices
        ecode = tkcmdsetDDI_discover_pm3s(TKCMDSET_PM5_PRODUCT_NAME, 0, &numCommunicating);
        break;
    }
    return numCommunicating;
}

#define PM_SERIALNUMSTRING_LEN   16
#define MAX_NUMBER_PORT 16
static char SNS[MAX_NUMBER_PORT][PM_SERIALNUMSTRING_LEN+1];

extern "C" __declspec(dllexport) char* __cdecl GetSerialNumber(int port)
{
    std::string sn;
    ERRCODE_T ecode = 0;

    /* Get identifier for communication port */
    ecode = tkcmdsetDDI_serial_number(port, SNS[port], PM_SERIALNUMSTRING_LEN);
    return ecode == 0 ? SNS[port] : nullptr;
}

extern "C" __declspec(dllexport) int __cdecl GetDistance(int port)
{
    UINT16_T cmd_data_size = 1;
    UINT32_T cmd_data = 0xA1;
    UINT16_T rsp_data_size = 100;
    UINT32_T rsp_data[100];
    ERRCODE_T ecode = tkcmdsetCSAFE_command(port, cmd_data_size, &cmd_data, &rsp_data_size, rsp_data);
    return (int64_t)rsp_data[2] + (((int64_t)rsp_data[3]) << 8);
}

extern "C" __declspec(dllexport) int __cdecl Init()
{
    ERRCODE_T ecode = 0;

    // Init DDI DLL
    ecode = tkcmdsetDDI_init();
    if (!ecode)
    {
        // Init CSAFE protocol
        ecode = tkcmdsetCSAFE_init_protocol(1000);

    }
    return ecode;
}

extern "C" __declspec(dllexport) int __cdecl Shutdown()
{
    tkcmdsetDDI_shutdown_all();
    return 0;
}


