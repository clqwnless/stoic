#include <windows.h>
#include <userenv.h>
#include <stdio.h>
#include <time.h>
#include <stdbool.h>


#define SERVICE_NAME "StoicGuardian"

#define MAX_RUNNERS 1024

#define STOIC_EXE_NAME "stoic.exe"
#define LOG_FILE_NAME  "stoic.log"

#pragma comment(lib, "advapi32.lib")
#pragma comment(lib, "userenv.lib")

/* structs */

typedef struct {
    DWORD  sid;
    HANDLE hProcess;
} Runner;

typedef struct {
    HANDLE hProcess;
    HANDLE hThread;
    DWORD  pid;
    DWORD  tid;
} Process;


/* global variables */

SERVICE_STATUS serviceStatus;
SERVICE_STATUS_HANDLE serviceStatusHandle;

HANDLE stopEvent;
HANDLE workerThread;

/* runners */

Runner runners[MAX_RUNNERS];
size_t runners_num = 0;

/* paths */

char service_directory[MAX_PATH];
char stoic_path[MAX_PATH];
char log_path[MAX_PATH];

/* prototypes */

BOOL launch_system_to_session(DWORD session_id, LPCSTR command, LPCSTR working_directory, Process *p);
void log(const char *fmt, ...);

void get_exe_path(char path[MAX_PATH])
{
    GetModuleFileNameA(NULL, path, MAX_PATH);
    
    char *last = strrchr(path, '\\');
    
    if (last)
        *last = '\0';
}

bool init_paths(void)
{
    get_exe_path(service_directory);
    
    if (strlen(service_directory) + strlen(LOG_FILE_NAME) >= MAX_PATH)
        return false;
    
    if (strlen(service_directory) + strlen(STOIC_EXE_NAME) >= MAX_PATH)
        return false;
    
    snprintf(stoic_path, sizeof(stoic_path), "%s\\%s", service_directory, STOIC_EXE_NAME);
    snprintf(log_path,   sizeof(log_path),   "%s\\%s", service_directory, LOG_FILE_NAME);

    return true;
}


bool is_proc_alive(HANDLE hProcess)
{
    DWORD ExitCode;
    
    if (GetExitCodeProcess(hProcess, &ExitCode))
    {
        if (ExitCode == STILL_ACTIVE)
            return true;
    }
    
    return false;
}


Runner *search_for_runner(DWORD searched_sid)
{
    for (size_t i = 0; i < runners_num; i++)
    {
        if (runners[i].sid == searched_sid)
            return &runners[i];
    }
    
    return NULL;
}


Runner *start_runner(DWORD sid)
{    
    Process p;
    
    char cmd_buffer[1024];
    snprintf(cmd_buffer, sizeof(cmd_buffer), "\"%s\" \"%s\"", stoic_path, service_directory);
    
    BOOL ret = launch_system_to_session(sid, cmd_buffer, NULL, &p);
    
    if (!ret)
        return NULL;
    
    CloseHandle(p.hThread);
    
    if (runners_num > MAX_RUNNERS)
        return NULL;
    
    Runner *r;
    
    if ((r = search_for_runner(sid)) == NULL)
    {
        r = &runners[runners_num];
        runners_num++;
    }

    r->sid      = sid;
    r->hProcess = p.hProcess;
    
    return r;
}


void on_logon(DWORD sid)
{
    log("on_logon, sid: %lu", sid);
    
    if (search_for_runner(sid) != NULL)
        return;
    
    start_runner(sid);
}


void on_logoff(DWORD sid)
{
    log("on_logoff, sid: %lu", sid);
    
    Runner *r;
    
    if ((r = search_for_runner(sid)) == NULL)
        return;
    
    if (TerminateProcess(r->hProcess, 0) == FALSE)
    {
        log("on_logoff, TerminateProcess err: %lu", GetLastError());
        return;
    }
}


void get_time(char *str, size_t str_size)
{
    time_t now   = time(NULL);
    struct tm *t = localtime(&now);

    snprintf(
        str,
        str_size,
        "%04d-%02d-%02d %02d:%02d:%02d",
        t->tm_year + 1900,
        t->tm_mon + 1,
        t->tm_mday,
        t->tm_hour,
        t->tm_min,
        t->tm_sec
    );
}

void write_log(const char *s)
{
    FILE *f = fopen(log_path, "a");
    
    if (!f)
        return;
    
    char time_str[128];
    
    get_time(time_str, sizeof(time_str));
    
    fprintf(f, "[%s] %s\n", time_str, s);
    
    fclose(f);
}

void log(const char *fmt, ...)
{
    char buffer[1024];
    
    va_list args;
    va_start(args, fmt);
    
    vsnprintf(buffer, sizeof(buffer), fmt, args);
    
    va_end(args);
    
    write_log(buffer);
}



void set_token_session_id(HANDLE token_handle, DWORD session_id)
{
    if (!SetTokenInformation(token_handle, TokenSessionId, &session_id, sizeof(session_id)))
        printf("SetTokenInformation failed: %lu\n", GetLastError());
}


BOOL launch_system_to_session(DWORD session_id, LPCSTR command, LPCSTR working_directory, Process *p)
{
    HANDLE current_token;
    HANDLE token;
    LPVOID environment = NULL;

    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ALL_ACCESS, &current_token))
        return FALSE;

    if (!DuplicateTokenEx(current_token, TOKEN_ALL_ACCESS, NULL, SecurityImpersonation, TokenPrimary, &token))
    {
        CloseHandle(current_token);
        return FALSE;
    }

    CloseHandle(current_token);

    set_token_session_id(token, session_id);

    if (!CreateEnvironmentBlock(&environment, token, FALSE))
    {
        CloseHandle(token);
        return FALSE;
    }

    STARTUPINFOA startup = {0};
    startup.cb = sizeof(startup);
    startup.lpDesktop = "winsta0\\default";

    PROCESS_INFORMATION process_info = {0};

    BOOL result = CreateProcessAsUserA(
        token,
        NULL,
        (LPSTR)command,
        NULL,
        NULL,
        FALSE,
        CREATE_NEW_CONSOLE | CREATE_UNICODE_ENVIRONMENT,
        environment,
        working_directory,
        &startup,
        &process_info
    );

    if (environment)
        DestroyEnvironmentBlock(environment);

    CloseHandle(token);

    if (!result)
        return FALSE;

    p->hProcess = process_info.hProcess;
    p->hThread  = process_info.hThread;
    p->pid      = process_info.dwProcessId;
    p->tid      = process_info.dwThreadId;

    return TRUE;
}






DWORD WINAPI WorkerThread(LPVOID param)
{
    log("WorkerThread");
    
    while (WaitForSingleObject(stopEvent, 1000) == WAIT_TIMEOUT)
    {
        for (size_t i = 0; i < runners_num; i++)
        {
            Runner *r = &runners[i];
            
            if (is_proc_alive(r->hProcess) == false)
            {
                start_runner(r->sid);
            }
        }
    }

    return 0;
}

DWORD WINAPI ServiceCtrlHandlerEx(DWORD control, DWORD event_type, LPVOID data, LPVOID context)
{
    if (control == SERVICE_CONTROL_SESSIONCHANGE)
    {
        WTSSESSION_NOTIFICATION *notification = (WTSSESSION_NOTIFICATION *)data;

        if (event_type == WTS_SESSION_LOGON)
            on_logon(notification->dwSessionId);
        /*else if (event_type == WTS_SESSION_LOGOFF)
            on_logoff(notification->dwSessionId);*/
    } else if (control == SERVICE_CONTROL_STOP) {
        serviceStatus.dwCurrentState = SERVICE_STOP_PENDING;
        SetServiceStatus(serviceStatusHandle, &serviceStatus);
        
        SetEvent(stopEvent);
    }

    return NO_ERROR;
}


void WINAPI ServiceMain(DWORD argc, LPTSTR* argv)
{
    log("ServiceMain");
    
    serviceStatusHandle = RegisterServiceCtrlHandlerExA(SERVICE_NAME, ServiceCtrlHandlerEx, NULL);

    if (!serviceStatusHandle)
        return;
    
    ZeroMemory(&serviceStatus, sizeof(serviceStatus));

    serviceStatus.dwServiceType      = SERVICE_WIN32_OWN_PROCESS;
    serviceStatus.dwCurrentState     = SERVICE_START_PENDING;
    serviceStatus.dwControlsAccepted = SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN | SERVICE_ACCEPT_PAUSE_CONTINUE | SERVICE_ACCEPT_SESSIONCHANGE;

    SetServiceStatus(serviceStatusHandle, &serviceStatus);


    stopEvent = CreateEvent(NULL, TRUE, FALSE, NULL);

    if (!stopEvent)
    {
        serviceStatus.dwCurrentState = SERVICE_STOPPED;
        SetServiceStatus(serviceStatusHandle, &serviceStatus);
        return;
    }


    workerThread = CreateThread(
        NULL,
        0,
        WorkerThread,
        NULL,
        0,
        NULL
    );

    if (!workerThread)
    {
        CloseHandle(stopEvent);

        serviceStatus.dwCurrentState = SERVICE_STOPPED;
        SetServiceStatus(serviceStatusHandle, &serviceStatus);
        return;
    }


    serviceStatus.dwCurrentState = SERVICE_RUNNING;
    SetServiceStatus(serviceStatusHandle, &serviceStatus);


    // Warten, bis Worker beendet wurde
    WaitForSingleObject(workerThread, INFINITE);


    CloseHandle(workerThread);
    CloseHandle(stopEvent);


    serviceStatus.dwCurrentState = SERVICE_STOPPED;
    SetServiceStatus(serviceStatusHandle, &serviceStatus);
}




int main(void)
{
    log("start");
    
    if (!init_paths())
        return -1;
    
    DeleteFile(log_path);
    
    log("paths initalized");
    
    SERVICE_TABLE_ENTRYA serviceTable[] =
    {
        {
            SERVICE_NAME,
            (LPSERVICE_MAIN_FUNCTIONA)ServiceMain
        },
        {
            NULL,
            NULL
        }
    };

    StartServiceCtrlDispatcherA(serviceTable);

    return 0;
}

