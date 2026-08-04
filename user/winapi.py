import win32ts;
import win32process;
import win32profile;
import win32con;
import win32gui;


def run_proc_from_current_session(proc_path):
    sid = win32ts.WTSGetActiveConsoleSessionId();
    token = win32ts.WTSQueryUserToken(sid);
    env = win32profile.CreateEnvironmentBlock(token, False);

    startup = win32process.STARTUPINFO();
    startup.lpDesktop = "winsta0\\default";

    win32process.CreateProcessAsUser(
        token,
        None,
        proc_path,
        None,
        None,
        False,
        win32con.CREATE_NEW_CONSOLE |
        win32con.CREATE_UNICODE_ENVIRONMENT,
        env,
        None,
        startup
    )

def disable_close_button():
    hwnd  = win32gui.GetForegroundWindow();
    hmenu = win32gui.GetSystemMenu(hwnd, False);

    win32gui.EnableMenuItem(
        hmenu,
        win32con.SC_CLOSE,
        win32con.MF_BYCOMMAND |
        win32con.MF_DISABLED |
        win32con.MF_GRAYED
    );

    win32gui.DrawMenuBar(hwnd);

