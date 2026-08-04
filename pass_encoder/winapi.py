import win32net;
import win32netcon;
import win32security;



def get_admin_group():
    # getting admin group name

    sid = win32security.ConvertStringSidToSid("S-1-5-32-544");
    admin_group_name, domain, sid_type = win32security.LookupAccountSid(None, sid);

    admins = [];

    # ...

    resume = 0

    # loop

    while True:
        members, total, resume = win32net.NetLocalGroupGetMembers(
            None, # local pc
            admin_group_name,
            1, # info level (possible range: 3) ; 1 allows user_names
            resume
        );
        
        for m in members:
            admins.append(m["name"]);

        # resume is the pointer: winapi should not return the whole list of the users at once
        
        if (resume == 0):
            break;

    return admins;


