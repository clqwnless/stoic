#define WIN32_LEAN_AND_MEAN
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

typedef struct {
    HANDLE hJob;
    HANDLE hProcess;
    DWORD  pid;
} JobObject;

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

BOOL launch_system_to_session(DWORD session_id, LPWSTR command, LPCWSTR working_directory, Process *p);
void log(const char *fmt, ...);
void setx(const char *var, const char *value);





void set_token_session_id(HANDLE token_handle, DWORD session_id)
{
    if (!SetTokenInformation(token_handle, TokenSessionId, &session_id, sizeof(session_id)))
        printf("SetTokenInformation failed: %lu\n", GetLastError());
}

BOOL set_token_to_system(DWORD sid, HANDLE token)
{
    HANDLE current_token;

    // returns a handle to the exisiting token of the process
    
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ALL_ACCESS, &current_token))
        return FALSE;

    if (!DuplicateTokenEx(current_token, TOKEN_ALL_ACCESS, NULL, SecurityImpersonation, TokenPrimary, &token))
    {
        CloseHandle(current_token);
        return FALSE;
    }

    CloseHandle(current_token);

    set_token_session_id(token, sid);
}


BOOL start_in_job(LPCWSTR applicationPath, LPWSTR commandLine, JobObject *result) {
    if (!applicationPath || !commandLine || !result) {
        SetLastError(ERROR_INVALID_PARAMETER);
        return FALSE;
    }

    result->hJob     = NULL;
    result->hProcess = NULL;
    result->pid      = 0;

    HANDLE hJob = CreateJobObjectW(NULL, NULL);
    if (!hJob)
        return FALSE;

    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits = { 0 };

    // kill all processes in a job object if the last handle is closed
    
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

    if (!SetInformationJobObject(hJob, JobObjectExtendedLimitInformation, &limits, sizeof(limits))) {
        DWORD err = GetLastError();
        
        CloseHandle(hJob);
        SetLastError(err);
        
        return FALSE;
    }

    STARTUPINFOW si  = { 0 };
    PROCESS_INFORMATION pi = { 0 };
    si.cb = sizeof(si);

    // create process but don't allow code execution (suspend it after the creation)
    if (!CreateProcessW(
        applicationPath,
        commandLine,
        NULL,
        NULL,
        FALSE,
        CREATE_SUSPENDED,
        NULL,
        NULL,
        &si,
        &pi
    )) {
        DWORD err = GetLastError();
        CloseHandle(hJob);
        SetLastError(err);
        return FALSE;
    }

    // Add process to the job object
    if (!AssignProcessToJobObject(hJob, pi.hProcess)) {
        DWORD err = GetLastError();

        TerminateProcess(pi.hProcess, err);
        WaitForSingleObject(pi.hProcess, INFINITE);

        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        CloseHandle(hJob);

        SetLastError(err);
        return FALSE;
    }

    // the process can be now resumed (and create another processes which will automatically be assigned to the job object)
    
    if (ResumeThread(pi.hThread) == (DWORD)-1) {
        DWORD err = GetLastError();

        TerminateProcess(pi.hProcess, err);
        WaitForSingleObject(pi.hProcess, INFINITE);

        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        CloseHandle(hJob);

        SetLastError(err);
        return FALSE;
    }

    CloseHandle(pi.hThread);

    result->hJob     = hJob;
    result->hProcess = pi.hProcess;
    result->pid      = pi.dwProcessId;

    return TRUE;
}


BOOL start_as_system_in_job(
    DWORD sid,
    LPWSTR command,
    LPCWSTR working_directory,
    JobObject *job
) {
    HANDLE hJob  = NULL;
    HANDLE token = NULL;

    STARTUPINFOW si        = {0};
    PROCESS_INFORMATION pi = {0};

    LPVOID env = NULL; // the environment with %PATH% vars, etc ...

    BOOL ret    = FALSE;
    
    /* creating a new token in order to run as system */
    
    set_token_to_system(sid, token);
    
    if (!CreateEnvironmentBlock(&env, token, FALSE))
        goto cleanup;
    
    if (!command || !working_directory || !job) {
        SetLastError(ERROR_INVALID_PARAMETER);
        goto cleanup;
    }

    job->hJob     = NULL;
    job->hProcess = NULL;
    job->pid      = 0;

    /* creating job object */
    
    hJob = CreateJobObjectW(NULL, NULL);
    if (!hJob)
        goto cleanup;

    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits = { 0 };

    // kill all processes in a job object if the last handle is closed
    
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

    if (!SetInformationJobObject(hJob, JobObjectExtendedLimitInformation, &limits, sizeof(limits)))
        goto cleanup;

    /* create the process itself */
    
    si.cb = sizeof(si);
    si.lpDesktop = L"winsta0\\default";
    
    if (!CreateProcessAsUserW(
        token,
        NULL,
        command,
        NULL,
        NULL,
        FALSE,
        CREATE_NEW_CONSOLE | CREATE_UNICODE_ENVIRONMENT | CREATE_SUSPENDED,
        env,
        working_directory,
        &si,
        &pi
    )) {
        goto cleanup;
    }
    
    // Add the process to the job object
    
    if (!AssignProcessToJobObject(hJob, pi.hProcess))
        goto cleanup;
    
    // resume the thread
    // (the thread was suspended so that it doesn't create new processes which aren't assigned to the job object)
    
    if (ResumeThread(pi.hThread) == (DWORD)-1)
        goto cleanup;

    CloseHandle(pi.hThread);

    job->hJob     = hJob;
    job->hProcess = pi.hProcess;
    job->pid      = pi.dwProcessId;

    return TRUE;
        
cleanup:
    DWORD err = GetLastError();

    if (token != NULL)
        CloseHandle(token);
    
    if (hJob != NULL)
        CloseHandle(hJob);
    
    if (pi.hProcess != NULL)
    {
        TerminateProcess(pi.hProcess, err);
        WaitForSingleObject(pi.hProcess, INFINITE); // waiting process to be terminated
        CloseHandle(pi.hProcess);
    }
    
    if (pi.hThread != NULL)
        CloseHandle(pi.hThread);
    
    if (env != NULL)
        DestroyEnvironmentBlock(env);

    SetLastError(err);

    return ret;
}


BOOL launch_system_to_session(DWORD session_id, LPWSTR command, LPCWSTR working_directory, Process *p)
{
    HANDLE token;
    LPVOID environment = NULL;

    set_token_to_system(session_id, token);

    if (!CreateEnvironmentBlock(&environment, token, FALSE))
    {
        CloseHandle(token);
        return FALSE;
    }

    STARTUPINFOW startup = {0};
    startup.cb = sizeof(startup);
    startup.lpDesktop = L"winsta0\\default";

    PROCESS_INFORMATION process_info = {0};

    BOOL result = CreateProcessAsUserW(
        token,
        NULL,
        command,
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

void init_env(void)
{
    setx("STOIC_ROOT_PATH", service_directory);
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


void setx(const char *var, const char *value)
{
    char buffer[1024];
    
    snprintf(buffer, sizeof(buffer), "setx \"%s\" \"%s\"", var, value);
    
    system(buffer);
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


#define ARRAY_SIZE(arr) sizeof((arr)) / sizeof((arr)[0])


Runner *start_runner(DWORD sid)
{    
    Process p;
    
    wchar_t cmd_buffer[1024];
    
    swprintf(cmd_buffer, ARRAY_SIZE(cmd_buffer), L"\"%s\"", stoic_path);
    
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

    init_env();
    
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

